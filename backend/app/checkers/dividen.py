"""Pemeriksa 3 — Dividen. Aturan D-1, D-2.  [Lane B]

⚠️ Keputusan terbuka #4: sumber rata-rata yield sektor (D-1).
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..catalog import param
from ..data import normal
from ..schemas import Claim, Evidence, Source
from .base import Checker, Outcome, angka_persen, card


def aturan_d1(yield_ttm: float, rata_sektor: float) -> bool:
    """'Dividen besar' sesuai jika yield ≥ 1,5× rata-rata sektor."""
    return yield_ttm >= param("D-1", "kelipatan_sektor") * rata_sektor


def aturan_d1_periode(klaim: float, yield_ttm: float) -> bool:
    """True = menyesatkan: angka klaim beda > 2 poin dari yield 12 bulan (periode lain)."""
    return abs(klaim - yield_ttm) > param("D-1", "selisih_periode_poin")


def aturan_d2(payout: Optional[float]) -> bool:
    return payout is not None and payout > param("D-2", "batas_payout")


class Dividen(Checker):
    id = "dividen"

    def run(self, ticker: str, claim: Optional[Claim], today: date) -> Outcome:
        d = normal.dividen(ticker)
        if d.yield_ttm is None:
            return Outcome("tidak_relevan", "Tidak ada dividen dalam 12 bulan terakhir.")
        src = [Source(name="Sectors · report dividend", as_of=str(today))]
        ev = [Evidence(label="Yield 12 bulan", value=d.yield_ttm, fmt="pct")]
        if d.payout_ratio is not None:
            ev.append(Evidence(label="Payout ratio", value=d.payout_ratio, fmt="pct"))

        if claim is not None:
            klaim = angka_persen(claim.text)
            if klaim is not None and aturan_d1_periode(klaim, d.yield_ttm):
                v, rid, h = "menyesatkan", "D-1", f"Yield 12 bulan tercatat {d.yield_ttm:.1%}, bukan {klaim:.0%}."
            elif klaim is not None:
                v, rid, h = "sesuai", "D-1", f"Benar, yield 12 bulan {d.yield_ttm:.1%}."
            elif d.yield_rata_sektor is not None:
                ok = aturan_d1(d.yield_ttm, d.yield_rata_sektor)
                v, rid = ("sesuai" if ok else "tidak_sesuai"), "D-1"
                h = f"Yield {d.yield_ttm:.1%} vs rata-rata sektor {d.yield_rata_sektor:.1%}."
            else:
                return Outcome("data_kurang", "Rata-rata yield sektor belum tersedia.")
            return Outcome("aman", h, card(verdict=v, check=self.id, rule_id=rid, claim=claim, headline=h,
                                            evidence=ev, sources=src))

        if aturan_d2(d.payout_ratio):
            h = f"Dividen dibayar {d.payout_ratio:.0%} dari laba: melebihi laba, belum tentu berulang."
            return Outcome("temuan", h, card(verdict="info", check=self.id, rule_id="D-2", headline=h,
                                              evidence=ev, sources=src))
        return Outcome("aman", "Dividen tidak melebihi laba.")
