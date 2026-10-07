"""Pintu ke LLM. Satu antarmuka, penyedia bisa diganti lewat LLM_PROVIDER.  [Lane C]

⚠️ Keputusan terbuka #1: penyedia LLM + siapa pemegang API key.

Batas peran AI (FINAL_PLAN §5) — dijaga di kode, bukan hanya di prompt:
- extract_claims: boleh memecah teks/screenshot jadi klaim + memilih pemeriksa.
  Pemeriksa yang dipilih divalidasi terhadap rules.json; yang tak dikenal dibuang.
- answer: HANYA boleh memakai angka di kartu yang dikirim. Guard penolakan jalan dulu.
- TIDAK PERNAH: menentukan vonis, menghitung angka, memilih data, memberi saran.
"""
from __future__ import annotations

import re
from typing import Optional, Protocol

from ..catalog import known_ids
from ..config import settings
from ..schemas import Card, KlaimResponse
from . import fallback
from .jev import get_jev, klaim_jev, prediksi_jev, target_jev


def _get_jev_prediksi():
    """Klien JEV untuk memeriksa prediksi, atau None (mode kode / tanpa kunci).

    Dipisah supaya tes bisa menggantinya. Kegagalan apa pun -> None: tanpa JEV,
    heuristik kata kunci yang dipakai, jadi jalur tanpa AI tetap sama seperti dulu.
    """
    try:
        return get_jev()
    except Exception:
        return None


def _layak_diperiksa(kalimat: str, jev_pred) -> bool:
    """False = sapaan/pertanyaan/ngobrol, bukan klaim saham.

    Heuristik `fallback.bukan_klaim` selalu jalan; kalau JEV ada, ia yang memutuskan
    (hasil ukur: non-klaim maks 0,28 vs klaim min 0,55). JEV mati/gagal -> klaim DIPERTAHANKAN.
    """
    if fallback.bukan_klaim(kalimat):
        return False
    if jev_pred is None:
        return True
    return klaim_jev(jev_pred, kalimat)


class LLM(Protocol):
    """Antarmuka AI. Sejak panel Tanya memakai penyusun jawaban deterministik, satu-satunya
    tugas LLM yang tersisa di antarmuka ini adalah memecah klaim (extract_claims).
    """

    def extract_claims(self, text: Optional[str], image_base64: Optional[str],
                       ticker: Optional[str]) -> KlaimResponse: ...


class NoLLM:
    """Tanpa AI: heuristik kata kunci. Screenshot tidak didukung."""

    def extract_claims(self, text, image_base64, ticker):
        if not text and ticker:
            return KlaimResponse(ticker=ticker.upper(), claims=[], used_ai=False)  # cek umum
        return fallback.pecah_klaim(text or "", ticker)


def get_llm() -> LLM:
    p = settings.llm_provider.lower()
    if p in ("", "none"):
        return NoLLM()
    if p == "gemini":
        from .gemini import GeminiLLM
        return GeminiLLM(settings.llm_api_key, settings.llm_model)
    if p in ("openai_compat", "openai", "ollama_cloud"):
        from .openai_compat import OpenAICompatLLM
        return OpenAICompatLLM(settings.llm_base_url, settings.llm_api_key, settings.llm_model)
    raise ValueError(f"LLM_PROVIDER '{p}' belum dibuat")


def sanitize(res: KlaimResponse) -> KlaimResponse:
    """Buang pemeriksa yang tidak ada di katalog (AI tidak boleh mengarang pemeriksa)."""
    ok = known_ids()
    for c in res.claims:
        c.checks = [x for x in c.checks if x in ok]
    return res


def _ticker_valid(teks: str, ticker: Optional[str]) -> Optional[str]:
    kandidat = (ticker or "").upper()
    if not re.fullmatch(r"[A-Z]{4}", kandidat):
        return None
    if teks and not re.search(rf"\b{re.escape(kandidat)}\b", teks):
        return None
    return kandidat


def _normalisasi(res: KlaimResponse, teks: Optional[str], ticker: Optional[str],
                 used_ai: bool, dari_gambar: bool) -> KlaimResponse:
    """Hitung ulang semua bagian yang tidak boleh dipercayakan kepada LLM."""
    # Untuk screenshot, teks hasil baca AI menggantikan teks pengguna: klaim dan ticker
    # harus benar-benar ada di teks yang nanti disorot di layar konfirmasi.
    sumber = (res.source_text or "") if dari_gambar else (teks or "")
    ticker_input = _ticker_valid("", ticker) if ticker else None
    ticker_ai = _ticker_valid(sumber, res.ticker)
    ticker_akhir = ticker_input or ticker_ai or fallback.cari_ticker(sumber)

    # Pengaman kedua: heuristik kata kunci melewatkan prediksi seperti "momen bagus
    # buat masuk, gaskeun". JEV (kalau ada) memutuskan; ia hanya bisa MENGHAPUS pemeriksa,
    # tidak pernah menambah, dan JEV mati/gagal -> hasil heuristik yang dipakai.
    jev_pred = _get_jev_prediksi()

    klaim_bersih = []
    for klaim in res.claims:
        awal = sumber.find(klaim.text)
        if awal < 0:
            continue
        if not _layak_diperiksa(klaim.text, jev_pred):
            continue  # sapaan/pertanyaan/ngobrol, bukan klaim saham
        checks = klaim.checks[:2]
        if fallback.prediksi_tanpa_angka(klaim.text) or (jev_pred and prediksi_jev(jev_pred, klaim.text)):
            checks = []
        # Target/prediksi harga berangka juga tidak boleh diberi vonis (T-1), walau
        # angkanya terlihat seperti klaim "dari A ke B".
        if jev_pred and checks and target_jev(jev_pred, klaim.text):
            checks = []
        klaim_bersih.append(klaim.model_copy(update={
            "id": f"c{len(klaim_bersih) + 1}",
            "span": (awal, awal + len(klaim.text)),
            "checks": checks,
        }))

    return KlaimResponse(
        ticker=ticker_akhir,
        company=res.company,
        claims=klaim_bersih,
        used_ai=used_ai,
        source_text=sumber if dari_gambar and sumber else None,
    )


def extract_with_fallback(text, image_base64, ticker) -> KlaimResponse:
    dari_gambar = bool(image_base64)
    try:
        llm = get_llm()
        hasil = sanitize(llm.extract_claims(text, image_base64, ticker))
        memakai_ai = not isinstance(llm, NoLLM) and bool(text or image_base64)
        return _normalisasi(hasil, text, ticker, memakai_ai, dari_gambar)
    except Exception:
        # Tanpa AI screenshot tidak terbaca: hasilnya tanpa ticker dan klaim, FE meminta teksnya.
        hasil = sanitize(NoLLM().extract_claims(text, image_base64, ticker))
        return _normalisasi(hasil, text, ticker, False, dari_gambar)
