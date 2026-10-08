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
from .base import Checker, Outcome, angka_persen, card, persen_id


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


def _arah(x: float) -> str:
    return "naik" if x > 0 else "turun" if x < 0 else "tetap"


class Laba(Checker):
    id = "laba"

    def run(self, ticker: str, claim: Optional[Claim], today: date) -> Outcome:
        k = sorted(normal.laba_kuartalan(ticker), key=lambda x: x.periode)
        yoy, tren = pertumbuhan_yoy(k), arah_tren(k)
        src = [Source(name="Sectors · laporan kuartalan", as_of=k[-1].periode if k else None)]
        ev = [Evidence(label=f"Laba bersih {x.periode}", value=x.laba_bersih, fmt="rp") for x in k[-4:]]

        n = param("L-2", "jumlah_kuartal")
        if claim is not None and (klaim := angka_persen(claim.text)) is not None and yoy is not None:
            banding = f"Kami hitung ulang dari laporan keuangan: laba kuartal {k[-1].periode} dibanding kuartal yang sama tahun lalu ({k[-5].periode})."
            tol = f"{param('L-1', 'toleransi_poin_persen'):g} poin persen"
            if aturan_l2(klaim, tren):
                v, rid = "menyesatkan", "L-2"
                h = f"Klaim bilang laba {_arah(klaim)}, tapi selama {n} kuartal terakhir trennya justru {_arah(-klaim)}."
                alasan = f"Satu kuartal pilihan bisa menutupi tren yang sebaliknya. Lihat laba {n} kuartal terakhir di bawah."
            elif aturan_l1(klaim, yoy):
                v, rid = "sesuai", "L-1"
                h = f"Laba kuartal terakhir memang {_arah(yoy)} {persen_id(abs(yoy), 0)} dibanding tahun lalu."
                alasan = f"{banding} Bedanya dengan angka di klaim masih di bawah {tol}."
            else:
                v, rid = "tidak_sesuai", "L-1"
                h = f"Hitungan kami: laba kuartal terakhir {_arah(yoy)} {persen_id(abs(yoy), 0)}, bukan {_arah(klaim)} {persen_id(abs(klaim), 0)} seperti di klaim."
                alasan = f"{banding} Bedanya dengan angka di klaim lebih dari {tol}."
            return Outcome("aman", h, card(verdict=v, check=self.id, rule_id=rid, claim=claim, headline=h,
                                            reason=alasan, evidence=ev, sources=src))

        if tren < 0:
            return Outcome("temuan", "Laba turun dalam tren 4 kuartal terakhir.",
                           card(verdict="info", check=self.id, rule_id="L-2",
                                headline=f"Laba cenderung turun dalam {n} kuartal terakhir.",
                                reason=f"Dari {k[-n:][0].periode} sampai {k[-1].periode}, laba bersih lebih sering turun daripada naik.",
                                evidence=ev, sources=src))
        return Outcome("aman", "Tren laba 4 kuartal tidak turun.")
