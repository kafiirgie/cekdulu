"""Perubahan porsi ritel dan jumlah pemegang pada periode yang sama. [Lane D]"""
from datetime import date
from math import isclose

from ..catalog import param
from ..data import bahan
from ..data.sectors import DataUnavailable
from ..schemas import Claim, Evidence, Source
from .asing import _periode
from .base import Checker, Outcome, card


def aturan_p1(perubahan_ritel: float, perubahan_pemegang: float) -> str:
    batas = param("P-1", "batas_perubahan_porsi")
    ritel_naik = perubahan_ritel >= batas or isclose(perubahan_ritel, batas)
    pemegang_naik = perubahan_pemegang > 0
    return "sesuai" if ritel_naik and pemegang_naik else "menyesatkan" if ritel_naik or pemegang_naik else "tidak_sesuai"


def kartu_pemegang(ticker: str, claim: Claim | None = None, today: date | None = None):
    today = today or date.today()
    n = param("P-1", "bulan_maks")
    if claim:
        periode, jumlah = _periode(claim.text)
        if periode == "harian":
            raise DataUnavailable("Komposisi ritel hanya tersedia per bulan")
        n = jumlah or n
    rows = sorted((r for r in bahan.baris("komposisi_pemegang_saham", ticker)
                   if date.fromisoformat(r["tanggal"]) <= today), key=lambda r: r["tanggal"])[-n:]
    if len(rows) < (n if claim and jumlah else param("P-1", "bulan_min")):
        raise DataUnavailable("Observasi komposisi bulanan tidak cukup")
    bulan = [date.fromisoformat(r["tanggal"]).year * 12 + date.fromisoformat(r["tanggal"]).month for r in rows]
    if any(b - a != 1 for a, b in zip(bulan, bulan[1:])):
        raise DataUnavailable("Bulan komposisi tidak lengkap")
    awal, akhir = rows[0], rows[-1]
    ritel = [bahan.wajib(r, "porsi_ritel_lokal") for r in (awal, akhir)]
    jumlah_p = [bahan.wajib(r, "jumlah_pemegang") for r in (awal, akhir)]
    cakupan = [bahan.wajib(r, "cakupan") for r in (awal, akhir)]
    if any(not 0 < c <= 1.0001 for c in cakupan) or any(not 0 <= p <= c for p, c in zip(ritel, cakupan)):
        raise DataUnavailable("Porsi/cakupan komposisi tidak sesuai")
    if any(p <= 0 or not p.is_integer() for p in jumlah_p):
        raise DataUnavailable("Jumlah pemegang tidak sesuai")
    # Porsi CSV memakai seluruh saham emiten; samakan penyebut dengan komposisi tercatat A-2.
    perubahan = ritel[1] / cakupan[1] - ritel[0] / cakupan[0]
    verdict = aturan_p1(perubahan, jumlah_p[1] - jumlah_p[0]) if claim else "info"
    return card(verdict=verdict, check="pemegang", rule_id="P-1", claim=claim,
                headline=f"Porsi ritel {ritel[0]:.1%} → {ritel[1]:.1%}; pemegang {jumlah_p[0]:,.0f} → {jumlah_p[1]:,.0f}.",
                reason=f"{len(rows)} observasi bulanan: {awal['tanggal']}–{akhir['tanggal']}. Porsi ritel pada kartu memakai seluruh saham emiten; arah dihitung relatif terhadap saham tercatat. Cakupan berbeda per emiten; hanya bandingkan tren dalam satu emiten. Kenaikan porsi ritel tidak otomatis berarti jumlah pemegang naik.",
                evidence=[Evidence(label="Porsi ritel lokal awal", value=ritel[0], fmt="pct"),
                          Evidence(label="Porsi ritel lokal akhir", value=ritel[1], fmt="pct"),
                          Evidence(label="Jumlah pemegang awal", value=jumlah_p[0], fmt="int"),
                          Evidence(label="Jumlah pemegang akhir", value=jumlah_p[1], fmt="int"),
                          Evidence(label="Cakupan awal", value=cakupan[0], fmt="pct"),
                          Evidence(label="Cakupan akhir", value=cakupan[1], fmt="pct")],
                sources=[Source(name=f"Sectors · shareholders composition · {awal['tanggal']}–{akhir['tanggal']}", as_of=akhir["tanggal"])])


class Pemegang(Checker):
    id = "pemegang"

    def run(self, ticker: str, claim: Claim | None, today: date) -> Outcome:
        return Outcome("modul_aktif", "Porsi ritel dan jumlah pemegang diperiksa.", kartu_pemegang(ticker, claim, today))
