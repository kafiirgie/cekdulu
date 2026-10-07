"""Pemeriksa 5 — Investor asing. Aturan A-1 dan tren bulanan A-2.  [Lane B]"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..catalog import param
from ..data import normal
from ..data.sectors import DataUnavailable
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


def aturan_a2(komposisi: list[normal.KomposisiBulanan]) -> tuple[float, float]:
    """Perubahan porsi asing dan ritel lokal dalam jendela bulanan satu emiten."""
    rows = sorted(komposisi, key=lambda r: r.tanggal)[-param("A-2", "bulan_maks"):]
    bulan = {(r.tanggal.year, r.tanggal.month) for r in rows}
    if len(rows) < param("A-2", "bulan_min") or len(bulan) != len(rows):
        raise DataUnavailable("Tren A-2 memerlukan bulan berbeda sesuai jendela aturan")
    return (rows[-1].porsi_asing - rows[0].porsi_asing,
            rows[-1].porsi_ritel_lokal - rows[0].porsi_ritel_lokal)


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
