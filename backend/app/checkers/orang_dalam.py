"""Pemeriksa 4 — Orang dalam. Aturan O-1 (jendela 12 bulan).  [Lane B]"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from ..catalog import param
from ..data import normal
from ..schemas import Claim, Evidence, Source
from .base import Checker, Outcome, card


def aturan_o1(transaksi: list[normal.TransaksiOrangDalam], today: date) -> list[normal.TransaksiOrangDalam]:
    """Transaksi > Rp1 M dalam 365 hari. Tidak ada transaksi = aman (bukan data kurang)."""
    awal = today - timedelta(days=param("O-1", "jendela_hari"))
    batas = param("O-1", "batas_nilai_rp")
    return [t for t in transaksi if t.tanggal >= awal and (t.nilai_rp or 0) > batas]


class OrangDalam(Checker):
    id = "orang_dalam"

    def run(self, ticker: str, claim: Optional[Claim], today: date) -> Outcome:
        besar = aturan_o1(normal.transaksi_orang_dalam(ticker), today)
        if not besar:
            return Outcome("aman", "Tidak ada transaksi orang dalam di atas Rp1 miliar dalam 12 bulan.")
        jual = sorted((t for t in besar if t.jenis == "jual"), key=lambda t: t.tanggal)
        teks = f"{len(besar)} transaksi orang dalam di atas Rp1 miliar dalam 12 bulan ({len(jual)} penjualan)."
        ev = []
        per_pemegang = {}
        for t in jual:
            per_pemegang.setdefault(t.nama, []).append(t)
        for nama, penjualan in per_pemegang.items():
            if penjualan[0].sebelum is not None and penjualan[-1].sesudah is not None:
                ev.extend([
                    Evidence(label=f"{nama}: kepemilikan sebelum penjualan pertama", value=penjualan[0].sebelum, fmt="pct"),
                    Evidence(label=f"{nama}: kepemilikan setelah penjualan terakhir", value=penjualan[-1].sesudah, fmt="pct"),
                ])
        return Outcome(
            "temuan", teks,
            card(verdict="info", check=self.id, rule_id="O-1", headline=teks, evidence=ev,
                 sources=[Source(name="Sectors · filings", as_of=str(max(t.tanggal for t in besar)))], claim=claim),
        )
