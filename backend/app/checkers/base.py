"""Kerangka pemeriksa. Satu file = satu pemeriksa = satu pemilik.

Pola tiap file di checkers/:
1. Fungsi aturan MURNI (`aturan_xx`) — input angka biasa, output keputusan.
   Tidak boleh memanggil API. Ini yang dites di tests/test_aturan.py dan
   inilah bukti "aturan yang memutuskan, bukan AI".
2. Kelas Checker — ambil data lewat app.data.normal, panggil aturan,
   bungkus hasilnya jadi status formulir + kartu.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..catalog import rule
from ..schemas import Card, Claim, Evidence, FormStatus, Source


@dataclass
class Outcome:
    status: FormStatus
    why: str
    card: Optional[Card] = None  # kartu vonis (jika ada klaim) atau kartu info (temuan tanpa klaim)


class Checker:
    id: str = ""

    def run(self, ticker: str, claim: Optional[Claim], today: date) -> Outcome:  # pragma: no cover
        """claim=None → pemeriksaan standar untuk formulir.
        claim diisi → beri vonis untuk klaim itu (Outcome.card wajib ada kalau bisa)."""
        raise NotImplementedError


def card(
    *,
    verdict: str,
    check: str,
    headline: str,
    reason: str = "",
    rule_id: Optional[str] = None,
    evidence: Optional[list[Evidence]] = None,
    sources: Optional[list[Source]] = None,
    claim: Optional[Claim] = None,
    chart=None,
) -> Card:
    return Card(
        claim_id=claim.id if claim else None,
        verdict=verdict,  # type: ignore[arg-type]
        check=check,
        headline=headline,
        reason=reason,
        rule_id=rule_id,
        rule_text=rule(rule_id)["text"] if rule_id else None,
        evidence=evidence or [],
        chart=chart,
        sources=sources or [],
    )


# ---------- pembaca angka dari teks klaim (tanpa AI) ----------
_SATUAN = {"rb": 1e3, "ribu": 1e3, "ribuan": 1e3, "k": 1e3, "jt": 1e6, "juta": 1e6,
           "m": 1e9, "miliar": 1e9, "milyar": 1e9, "t": 1e12, "triliun": 1e12}


def angka_rupiah(teks: str) -> list[float]:
    """'dari 600 udah 14 ribuan' → [600, 14000]. 'Rp1,5 M' → [1.5e9]."""
    hasil = []
    for m in re.finditer(r"(\d+(?:[.,]\d+)*)\s*(ribuan|ribu|rb|k|juta|jt|miliar|milyar|triliun|m|t)?\b", teks.lower()):
        raw, sat = m.group(1), m.group(2)
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", raw):  # 14.650 = ribuan Indonesia
            n = float(raw.replace(".", ""))
        else:
            n = float(raw.replace(",", "."))
        hasil.append(n * _SATUAN.get(sat or "", 1))
    return hasil


def angka_persen(teks: str) -> Optional[float]:
    """'laba naik 200%' → 2.0"""
    m = re.search(r"(-?\d+(?:[.,]\d+)?)\s*(%|persen)", teks.lower())
    return float(m.group(1).replace(",", ".")) / 100 if m else None


def rp(x: float) -> str:
    """14650 → 'Rp14.650' (format Indonesia)."""
    return "Rp" + f"{x:,.0f}".replace(",", ".")
