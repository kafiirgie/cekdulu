"""Pemeriksa modul — "saham X = saham komoditas Y?". Aturan K-1, K-2.  [Lane D]"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..modul import komoditas as k
from ..schemas import Claim, Evidence, Source
from .base import Checker, Outcome, card


class MKomoditas(Checker):
    id = "m_komoditas"

    def run(self, ticker: str, claim: Optional[Claim], today: date) -> Outcome:
        jenis = k.komoditas_disebut(claim.text) if claim else None
        if claim is None or jenis is None:
            return Outcome("tidak_relevan", "Klaim tidak menyebut komoditas.")
        porsi = k.porsi_pendapatan(ticker, jenis)
        kor = k.korelasi(ticker, jenis)
        kategori = k.aturan_k2(kor)
        menyesatkan = k.aturan_k1(porsi)
        h = (f"Hanya {porsi:.0%} pendapatan {ticker} dari {jenis}." if menyesatkan
             else f"{porsi:.0%} pendapatan {ticker} memang dari {jenis}.")
        return Outcome(
            "modul_aktif", "Klaim menyebut komoditas.",
            card(verdict="menyesatkan" if menyesatkan else "sesuai", check=self.id, rule_id="K-1", claim=claim,
                 headline=h, reason=f"Hubungan harga saham dengan {jenis}: {kategori} ({kor:.2f}).",
                 evidence=[Evidence(label=f"Porsi pendapatan dari {jenis}", value=porsi, fmt="pct"),
                           Evidence(label=f"Korelasi bulanan dengan {jenis}", value=kor, fmt="num")],
                 sources=[Source(name="Sectors · get-segments"),
                          Source(name="World Bank Pink Sheet (CC BY)", as_of="2026-09-02")]),
        )
