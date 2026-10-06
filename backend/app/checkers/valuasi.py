"""Pemeriksa 2 — Valuasi. Aturan V-1.  [Lane B]"""
from __future__ import annotations

import re
from datetime import date
from typing import Optional

from ..catalog import param
from ..data import normal
from ..schemas import Claim, Evidence, Source
from .base import Checker, Outcome, card


def aturan_v1(klaim: float, aktual: float) -> bool:
    return aktual > 0 and abs(klaim - aktual) / aktual <= param("V-1", "toleransi_relatif")


def _angka_setelah(kata: str, teks: str) -> Optional[float]:
    m = re.search(kata + r"\D{0,12}(\d+(?:[.,]\d+)?)", teks.lower())
    return float(m.group(1).replace(",", ".")) if m else None


class Valuasi(Checker):
    id = "valuasi"

    def run(self, ticker: str, claim: Optional[Claim], today: date) -> Outcome:
        v = normal.valuasi(ticker)
        ev = [Evidence(label="PER", value=v.per, fmt="x"), Evidence(label="PBV", value=v.pbv, fmt="x"),
              Evidence(label="Forward PE", value=v.forward_pe if v.forward_pe is not None else "tidak tersedia",
                       fmt="x" if v.forward_pe is not None else "text")]
        src = [Source(name="Sectors · report valuation", as_of=str(today))]
        if claim is not None:
            for nama, aktual in (("per", v.per), ("pbv", v.pbv)):
                klaim = _angka_setelah(nama, claim.text)
                if klaim is not None and aktual:
                    ok = aturan_v1(klaim, aktual)
                    h = f"{nama.upper()} tercatat {aktual:.1f}× (klaim {klaim:.1f}×)."
                    return Outcome("aman", h, card(verdict="sesuai" if ok else "tidak_sesuai", check=self.id,
                                                    rule_id="V-1", claim=claim, headline=h, evidence=ev, sources=src))
        if v.per is None and v.pbv is None:
            return Outcome("data_kurang", "PER dan PBV tidak tersedia.")
        return Outcome("aman", "Valuasi dicatat untuk konteks; tidak ada aturan temuan tanpa klaim.")
