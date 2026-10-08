"""API cek dulu. Jalankan dari folder backend/:  uvicorn app.main:app --reload --port 8000"""
from __future__ import annotations

import base64
import binascii
import json
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import quota
from .ai import guard
from .ai.jev import get_jev
from .ai.provider import extract_with_fallback
from .ai.tanya import jawab_tanya
from .catalog import kamus
from .config import settings
from .data import sectors
from .engine import run_cek
from .modul import free_float as m_ff
from .modul import komoditas as m_k
from .schemas import (CekRequest, CekResponse, FreeFloatList, KlaimRequest, KlaimResponse, TanyaRequest,
                      TanyaResponse, KomoditasList, KomoditasDetail)

app = FastAPI(title="cek dulu. API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["*"],
                   allow_headers=["*"])

# Hasil cek disimpan di memori supaya /api/tanya bisa merujuk kartu. Hilang kalau server restart.
_CEK: dict[str, CekResponse] = {}
EX = settings.contract_dir / "examples"
BATAS_GAMBAR = 4 * 1024 * 1024


def _contoh(nama: str) -> dict:
    d = json.loads((EX / nama).read_text(encoding="utf-8"))
    d.pop("_catatan", None)
    return d


def _contoh_ticker(prefix: str, ticker: Optional[str]) -> dict:
    t = (ticker or "mdka").lower()
    f = EX / f"{prefix}_{t}.json"
    return _contoh(f.name if f.exists() else f"{prefix}_mdka.json")


def _validasi_gambar(image_base64: Optional[str]) -> None:
    """Tolak payload rusak/besar sebelum menyentuh penyedia AI."""
    if image_base64 is None:
        return
    # Empat byte base64 mewakili paling banyak tiga byte gambar. Pemeriksaan
    # murah ini mencegah decode payload yang sudah pasti melewati batas.
    if len(image_base64) > 4 * ((BATAS_GAMBAR + 2) // 3):
        raise HTTPException(413, "Ukuran screenshot maksimal 4 MB.")
    try:
        data = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(422, "Screenshot bukan base64 yang valid.") from exc
    if len(data) > BATAS_GAMBAR:
        raise HTTPException(413, "Ukuran screenshot maksimal 4 MB.")
    if not data:
        raise HTTPException(422, "Screenshot kosong.")


def _pastikan_tersedia(ticker: Optional[str]) -> None:
    """Mode fixture hanya punya data saham demo. Tanpa ini, saham lain lolos ke cek,
    semua pemeriksa jadi `data_kurang`, dan kuota tetap terpakai."""
    tersedia = sectors.ticker_tersedia()
    if ticker and tersedia is not None and ticker.upper() not in tersedia:
        raise HTTPException(404, f"{ticker.upper()} belum ada di data demo. "
                                 f"Coba salah satu: {', '.join(tersedia)}.")


@app.get("/api/health")
def health():
    return {"ok": True, "mode": settings.data_mode, "llm": settings.llm_provider,
            "kredit_live_terpakai": sectors.credits_used()}


@app.get("/api/rules")
def rules():
    return kamus()


@app.post("/api/klaim", response_model=KlaimResponse)
def klaim(req: KlaimRequest):
    if not (req.text or req.image_base64 or req.ticker):
        raise HTTPException(422, "Isi teks, screenshot, atau kode saham.")
    _validasi_gambar(req.image_base64)
    if settings.data_mode == "mock":
        from .ai.fallback import cari_ticker
        return _contoh_ticker("klaim_res", req.ticker or cari_ticker(req.text or ""))
    res = extract_with_fallback(req.text, req.image_base64, req.ticker)
    _pastikan_tersedia(res.ticker)
    return res


@app.post("/api/cek", response_model=CekResponse)
def cek(req: CekRequest, x_device_id: str = Header(default="anon")):
    if settings.data_mode != "mock":
        _pastikan_tersedia(req.ticker)
    q = quota.pakai(x_device_id)
    if q is None:
        raise HTTPException(429, detail={"code": "kuota_habis", "quota": quota.status(x_device_id).model_dump()})
    if settings.data_mode == "mock":
        res = CekResponse.model_validate(_contoh_ticker("cek_res", req.ticker))
    else:
        res = run_cek(req)
    res.quota = q
    _CEK[res.id] = res
    return res


@app.post("/api/tanya", response_model=TanyaResponse)
def tanya(req: TanyaRequest):
    if guard.minta_saran(req.question):
        return TanyaResponse(answer=guard.PENOLAKAN, refused=True, answer_kind="saran")
    cek_res = _CEK.get(req.cek_id)
    if cek_res is None:
        raise HTTPException(404, "Hasil cek tidak ditemukan (server mungkin restart). Cek ulang dulu.")
    kartu = next((c for c in cek_res.claims if c.claim_id == req.card), None)
    if kartu is None:
        idx = int(req.card[1:]) if req.card.startswith("u") and req.card[1:].isdigit() else -1
        kartu = cek_res.untold[idx] if 0 <= idx < len(cek_res.untold) else None
    if kartu is None:
        raise HTTPException(404, "Kartu tidak ditemukan.")
    # Angka dan kalimat disusun kode; JEV hanya memilih bagian kartu yang relevan.
    return TanyaResponse(**jawab_tanya(kartu, req.question, jev=get_jev()))


@app.get("/api/modul/free-float", response_model=FreeFloatList)
def modul_free_float():
    if settings.data_mode == "mock":
        return _contoh("modul_free_float_list.json")
    try:
        return m_ff.daftar()
    except sectors.DataUnavailable as e:
        raise HTTPException(503, str(e))


@app.get("/api/modul/free-float/{ticker}")
def modul_free_float_detail(ticker: str):
    items = modul_free_float().items if settings.data_mode != "mock" else \
        FreeFloatList.model_validate(_contoh("modul_free_float_list.json")).items
    for i in items:
        if i.ticker == ticker.upper():
            return i
    raise HTTPException(404, f"{ticker.upper()} tidak ada di Radar Free Float")


@app.get("/api/modul/komoditas", response_model=KomoditasList)
def modul_komoditas(jenis: str = "batubara"):
    if jenis not in m_k.NAMA_SERI:
        raise HTTPException(422, "Komoditas belum didukung")
    if settings.data_mode == "mock":
        contoh = KomoditasDetail.model_validate(_contoh("modul_komoditas_detail_mdka.json"))
        return KomoditasList(as_of=contoh.as_of, jenis=jenis, items=[i for i in contoh.items if i.komoditas == jenis])
    try:
        return m_k.daftar(jenis)
    except sectors.DataUnavailable as e:
        raise HTTPException(503, str(e))


@app.get("/api/modul/komoditas/{ticker}", response_model=KomoditasDetail)
def modul_komoditas_detail(ticker: str):
    if settings.data_mode == "mock":
        if ticker.upper() != "MDKA":
            raise HTTPException(404, "Contoh modul hanya tersedia untuk MDKA")
        return _contoh("modul_komoditas_detail_mdka.json")
    try:
        return m_k.detail(ticker)
    except sectors.DataUnavailable as e:
        raise HTTPException(404, str(e))
