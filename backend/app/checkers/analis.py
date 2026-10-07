"""Rekomendasi analis dan konteks proyeksi yang dilaporkan Sectors. [Lane D]"""
from datetime import date

from ..catalog import param
from ..data import bahan
from ..data.sectors import DataUnavailable
from ..schemas import Claim, Evidence, Source
from .base import Checker, Outcome, card


def aturan_n1(porsi_buy: float, semua: bool) -> bool:
    return porsi_buy == param("N-1", "porsi_semua") if semua else porsi_buy >= param("N-1", "porsi_mayoritas")


def kartu_analis(ticker: str, claim: Claim | None = None):
    r = bahan.baris("rating_analis", ticker)[0]
    jumlah = bahan.wajib(r, "jumlah_rekomendasi")
    angka = [bahan.wajib(r, k) for k in ("buy", "strong_buy", "hold", "sell", "strong_sell")]
    if jumlah <= 0 or any(n < 0 or not n.is_integer() for n in angka) or sum(angka) != jumlah:
        raise DataUnavailable("Jumlah rekomendasi tidak sesuai")
    buy = angka[0] + angka[1]
    if not r.get("diperbarui"):
        raise DataUnavailable("Tanggal rekomendasi kosong")
    ev = [Evidence(label="Rekomendasi buy + strong buy", value=buy, fmt="int"),
          Evidence(label="Jumlah rekomendasi", value=jumlah, fmt="int"),
          Evidence(label="Porsi rekomendasi buy", value=buy / jumlah, fmt="pct")]
    for kolom, label in (("proyeksi_pertumbuhan_eps", "Proyeksi perubahan EPS"),
                         ("proyeksi_pertumbuhan_pendapatan", "Proyeksi perubahan pendapatan")):
        nilai = bahan.angka(r.get(kolom))
        if nilai is not None:
            if not r.get("tahun_proyeksi"):
                raise DataUnavailable("Tahun proyeksi kosong")
            ev.append(Evidence(label=f"{label} {r['tahun_proyeksi']} (analis)", value=nilai, fmt="pct"))
    verdict = "info"
    if claim:
        import re
        semua = bool(re.search(r"\b(semua|seluruh|all)\b", claim.text.lower()))
        verdict = "sesuai" if aturan_n1(buy / jumlah, semua) else "tidak_sesuai"
    return card(verdict=verdict, check="analis", rule_id="N-1", claim=claim,
                headline=f"{buy:.0f} dari {jumlah:.0f} rekomendasi adalah buy atau strong buy.",
                reason="Jumlah rekomendasi bukan jumlah analis. Proyeksi adalah estimasi analis yang dilaporkan Sectors, bukan prediksi atau saran kami.",
                evidence=ev, sources=[Source(name="Sectors · report future", as_of=r["diperbarui"])])


class Analis(Checker):
    id = "analis"

    def run(self, ticker: str, claim: Claim | None, today: date) -> Outcome:
        return Outcome("modul_aktif", "Rekomendasi dan proyeksi analis diperiksa.", kartu_analis(ticker, claim))
