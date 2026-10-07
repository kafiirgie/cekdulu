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


class LLM(Protocol):
    def extract_claims(self, text: Optional[str], image_base64: Optional[str],
                       ticker: Optional[str]) -> KlaimResponse: ...

    def answer(self, card: Card, question: str) -> str: ...


class NoLLM:
    """Tanpa AI: heuristik kata kunci. Screenshot tidak didukung."""

    def extract_claims(self, text, image_base64, ticker):
        if not text and ticker:
            return KlaimResponse(ticker=ticker.upper(), claims=[], used_ai=False)  # cek umum
        return fallback.pecah_klaim(text or "", ticker)

    def answer(self, card: Card, question: str) -> str:
        bukti = "; ".join(f"{e.label}: {e.value}" for e in card.evidence) or "tidak ada angka tambahan"
        sumber = ", ".join(s.name for s in card.sources) or "-"
        return f"{card.headline} Angka di kartu ini: {bukti}. Sumber: {sumber}."


def get_llm() -> LLM:
    p = settings.llm_provider.lower()
    if p in ("", "none"):
        return NoLLM()
    if p == "gemini":
        from .gemini import GeminiLLM
        return GeminiLLM(settings.llm_api_key, settings.llm_model)
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
                 used_ai: bool) -> KlaimResponse:
    """Hitung ulang semua bagian yang tidak boleh dipercayakan kepada LLM."""
    sumber = teks or ""
    ticker_input = _ticker_valid("", ticker) if ticker else None
    ticker_ai = _ticker_valid(sumber, res.ticker)
    ticker_akhir = ticker_input or ticker_ai or fallback.cari_ticker(sumber)

    klaim_bersih = []
    for klaim in res.claims:
        awal = sumber.find(klaim.text)
        if awal < 0:
            continue
        checks = klaim.checks[:2]
        if fallback.prediksi_tanpa_angka(klaim.text):
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
    )


def extract_with_fallback(text, image_base64, ticker) -> KlaimResponse:
    # C2 core sudah dapat membaca gambar, tetapi jangan habiskan request Gemini
    # sebelum kontrak `source_text` disetujui. Tanpa field itu, normalisasi pusat
    # tidak dapat memverifikasi span terhadap teks OCR dan FE tidak bisa menyorotnya.
    if image_base64:
        return sanitize(NoLLM().extract_claims(text, image_base64, ticker))
    try:
        llm = get_llm()
        hasil = sanitize(llm.extract_claims(text, image_base64, ticker))
        memakai_ai = not isinstance(llm, NoLLM) and bool(text or image_base64)
        return _normalisasi(hasil, text, ticker, memakai_ai)
    except Exception:
        hasil = sanitize(NoLLM().extract_claims(text, image_base64, ticker))
        return _normalisasi(hasil, text, ticker, False)
