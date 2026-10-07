"""Pemeriksa 7 — Suspensi. Aturan S-1.  [Lane B]"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from ..catalog import param
from ..data import normal
from ..schemas import Claim, Evidence, Source
from .base import Checker, Outcome, card


def aturan_s1(riwayat: list[normal.Suspensi], today: date) -> list[normal.Suspensi]:
    """Suspensi dalam 36 bulan terakhir (urut terbaru dulu)."""
    awal = today - timedelta(days=round(param("S-1", "jendela_bulan") * 30.44))
    return sorted((s for s in riwayat if s.tanggal >= awal), key=lambda s: s.tanggal, reverse=True)


class Suspensi(Checker):
    id = "suspensi"

    def run(self, ticker: str, claim: Optional[Claim], today: date) -> Outcome:
        dalam = aturan_s1(normal.riwayat_suspensi(ticker), today)
        if not dalam:
            return Outcome("aman", "Tidak ada suspensi dalam 36 bulan terakhir.")
        teks = f"Disuspensi {len(dalam)} kali dalam 36 bulan terakhir."
        return Outcome(
            "temuan", teks,
            card(verdict="info", check=self.id, rule_id="S-1", headline=teks,
                 reason=f"Alasan terakhir: {dalam[0].alasan}",
                 evidence=[Evidence(label="Jumlah suspensi", value=len(dalam), fmt="int")],
                 sources=[Source(name="Sectors · suspensi", as_of=str(dalam[0].tanggal))], claim=claim),
        )
