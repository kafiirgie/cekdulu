"""Pemeriksa 8 — Free float. Aturan F-1. Temuan → modul Radar Free Float aktif.  [Lane B]"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..catalog import param
from ..data import normal
from ..schemas import Claim, Evidence, Source
from .base import Checker, Outcome, card


def aturan_f1(ff: float) -> bool:
    return ff < param("F-1", "batas_free_float")


class FreeFloat(Checker):
    id = "free_float"

    def run(self, ticker: str, claim: Optional[Claim], today: date) -> Outcome:
        ff = normal.free_float(ticker)
        if not aturan_f1(ff):
            return Outcome("aman", f"Saham publik {ff:.1%}, di atas batas 15%.")
        teks = f"Saham publik hanya {ff:.1%}, di bawah batas 15%."
        return Outcome(
            "temuan", teks + " Radar Free Float aktif.",
            card(verdict="info", check=self.id, rule_id="F-1", headline=teks,
                 reason="Emiten wajib menambah porsi saham publik sesuai tenggat BEI. Lihat Radar Free Float.",
                 evidence=[Evidence(label="Free float", value=ff, fmt="pct")],
                 sources=[Source(name="Sectors · major shareholders", as_of=str(today))], claim=claim),
        )
