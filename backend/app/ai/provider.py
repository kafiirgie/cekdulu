"""Pintu ke LLM. Satu antarmuka, penyedia bisa diganti lewat LLM_PROVIDER.  [Lane C]

⚠️ Keputusan terbuka #1: penyedia LLM + siapa pemegang API key.

Batas peran AI (FINAL_PLAN §5) — dijaga di kode, bukan hanya di prompt:
- extract_claims: boleh memecah teks/screenshot jadi klaim + memilih pemeriksa.
  Pemeriksa yang dipilih divalidasi terhadap rules.json; yang tak dikenal dibuang.
- answer: HANYA boleh memakai angka di kartu yang dikirim. Guard penolakan jalan dulu.
- TIDAK PERNAH: menentukan vonis, menghitung angka, memilih data, memberi saran.
"""
from __future__ import annotations

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
    # TODO(C1): tambahkan kelas penyedia, mis. GeminiLLM di ai/gemini.py, lalu:
    # if p == "gemini": from .gemini import GeminiLLM; return GeminiLLM(settings.llm_api_key, settings.llm_model)
    raise ValueError(f"LLM_PROVIDER '{p}' belum dibuat")


def sanitize(res: KlaimResponse) -> KlaimResponse:
    """Buang pemeriksa yang tidak ada di katalog (AI tidak boleh mengarang pemeriksa)."""
    ok = known_ids()
    for c in res.claims:
        c.checks = [x for x in c.checks if x in ok]
    return res


def extract_with_fallback(text, image_base64, ticker) -> KlaimResponse:
    try:
        return sanitize(get_llm().extract_claims(text, image_base64, ticker))
    except Exception:
        return sanitize(NoLLM().extract_claims(text, image_base64, ticker))
