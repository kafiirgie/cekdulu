"""Pemeriksa 5 — Investor asing. Aturan A-1 (A-2 tren bulanan: TODO B2).  [Lane B]"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..catalog import param
from ..data import normal
from ..schemas import Claim, Evidence, Source
from .base import Checker, Outcome, card

_KATA_JUAL = ("jual", "kabur", "keluar", "lepas", "buang")


def aturan_a1(aliran: list[normal.AliranAsing]) -> tuple[bool, float, float]:
    """(asing_borong?, total_bersih_rp, porsi_hari_masuk) dari 20 hari bursa terakhir."""
    n = param("A-1", "jendela_hari_bursa")
    a = sorted(aliran, key=lambda x: x.tanggal)[-n:]
    if not a:
        return False, 0.0, 0.0
    total = sum(x.bersih_rp for x in a)
    porsi = sum(1 for x in a if x.bersih_rp > 0) / len(a)
    return total > 0 and porsi >= param("A-1", "porsi_hari_masuk"), total, porsi


class Asing(Checker):
    id = "asing"

    def run(self, ticker: str, claim: Optional[Claim], today: date) -> Outcome:
        aliran = normal.aliran_asing(ticker)
        borong, total, porsi = aturan_a1(aliran)
        ev = [Evidence(label="Aliran bersih asing 20 hari bursa", value=total, fmt="rp"),
              Evidence(label="Porsi hari masuk bersih", value=porsi, fmt="pct")]
        src = [Source(name="Sectors · foreign flow", as_of=str(max((x.tanggal for x in aliran), default=today)))]

        if claim is not None:
            klaim_jual = any(k in claim.text.lower() for k in _KATA_JUAL)
            cocok = (not borong) if klaim_jual else borong
            h = ("Sesuai data: " if cocok else "Tidak sesuai: ") + (
                f"aliran bersih asing 20 hari bursa {'positif' if total > 0 else 'negatif'}, "
                f"{porsi:.0%} hari masuk bersih.")
            return Outcome("aman", h, card(verdict="sesuai" if cocok else "tidak_sesuai", check=self.id,
                                            rule_id="A-1", claim=claim, headline=h, evidence=ev, sources=src))
        return Outcome("aman", f"Aliran bersih asing 20 hari bursa {'masuk' if total > 0 else 'keluar'}.")
