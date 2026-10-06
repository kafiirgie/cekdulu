"""Pemeriksa 1 — Laba. Aturan L-1 (hitung ulang), L-2 (periode pilihan).  [Lane B]

⚠️ Keputusan terbuka #5: apakah data kuartalan Sectors memisahkan pos tidak
berulang. Kalau tidak, L-2 cukup memakai aturan periode (yang dipakai di sini).
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..catalog import param
from ..data import normal
from ..schemas import Claim, Evidence, Source
from .base import Checker, Outcome, angka_persen, card


def pertumbuhan_yoy(kuartal: list[normal.Kuartal]) -> Optional[float]:
    """Kuartal terakhir vs kuartal yang sama tahun lalu (butuh 5 kuartal)."""
    if len(kuartal) < 5:
        return None
    lalu, kini = kuartal[-5].laba_bersih, kuartal[-1].laba_bersih
    if lalu <= 0:
        return None  # pertumbuhan dari rugi tidak bermakna sebagai persen
    return kini / lalu - 1


def arah_tren(kuartal: list[normal.Kuartal]) -> int:
    """+1 naik, −1 turun, 0 datar — dari 4 kuartal terakhir (kemiringan sederhana)."""
    n = param("L-2", "jumlah_kuartal")
    v = [k.laba_bersih for k in kuartal[-n:]]
    if len(v) < 2:
        return 0
    naik = sum(1 for a, b in zip(v, v[1:]) if b > a)
    turun = sum(1 for a, b in zip(v, v[1:]) if b < a)
    return (naik > turun) - (turun > naik)


def aturan_l1(klaim: float, aktual: float) -> bool:
    return abs(klaim - aktual) <= param("L-1", "toleransi_poin_persen") / 100


def aturan_l2(klaim: float, tren: int) -> bool:
    """True = menyesatkan: klaim naik tapi tren 4 kuartal turun (atau sebaliknya)."""
    return tren != 0 and (klaim > 0) != (tren > 0)


class Laba(Checker):
    id = "laba"

    def run(self, ticker: str, claim: Optional[Claim], today: date) -> Outcome:
        k = sorted(normal.laba_kuartalan(ticker), key=lambda x: x.periode)
        yoy, tren = pertumbuhan_yoy(k), arah_tren(k)
        src = [Source(name="Sectors · laporan kuartalan", as_of=k[-1].periode if k else None)]
        ev = [Evidence(label=f"Laba bersih {x.periode}", value=x.laba_bersih, fmt="rp") for x in k[-4:]]

        if claim is not None and (klaim := angka_persen(claim.text)) is not None and yoy is not None:
            if aturan_l2(klaim, tren):
                v, rid, h = "menyesatkan", "L-2", "Klaim memakai periode pilihan; tren laba 4 kuartal berlawanan arah."
            elif aturan_l1(klaim, yoy):
                v, rid, h = "sesuai", "L-1", f"Sesuai: laba kuartal terakhir berubah {yoy:+.0%} dibanding tahun lalu."
            else:
                v, rid, h = "tidak_sesuai", "L-1", f"Tidak sesuai: hitungan kami {yoy:+.0%}, klaim {klaim:+.0%}."
            return Outcome("aman", h, card(verdict=v, check=self.id, rule_id=rid, claim=claim, headline=h,
                                            evidence=ev, sources=src))

        if tren < 0:
            return Outcome("temuan", "Laba turun dalam tren 4 kuartal terakhir.",
                           card(verdict="info", check=self.id, rule_id="L-2",
                                headline="Laba cenderung turun dalam 4 kuartal terakhir.", evidence=ev, sources=src))
        return Outcome("aman", "Tren laba 4 kuartal tidak turun.")
