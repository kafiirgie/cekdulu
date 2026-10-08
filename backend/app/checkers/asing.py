"""Pemeriksa 5 — Investor asing. Aturan A-1, tren A-2, konflik periode A-3.  [Lane B]"""
from __future__ import annotations

import re
from datetime import date
from math import isclose
from typing import Optional

from ..catalog import param
from ..data import normal
from ..data.sectors import DataUnavailable
from ..schemas import Chart, ChartSeries, Claim, Evidence, Source
from .base import Checker, Outcome, card, persen_id, rp_kata

_KATA_JUAL = ("jual", "kabur", "keluar", "lepas", "buang", "turun", "berkurang")


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
    if any((b.tanggal.year * 12 + b.tanggal.month) - (a.tanggal.year * 12 + a.tanggal.month) != 1
           for a, b in zip(rows, rows[1:])):
        raise DataUnavailable("Bulan dalam jendela A-2 tidak lengkap")
    return (rows[-1].porsi_asing - rows[0].porsi_asing,
            rows[-1].porsi_ritel_lokal - rows[0].porsi_ritel_lokal)


def arah_a2(perubahan: float) -> int:
    """Perubahan di bawah ambang katalog dianggap datar, termasuk pembulatan float."""
    batas = param("A-2", "batas_perubahan_porsi")
    if abs(perubahan) < batas and not isclose(abs(perubahan), batas):
        return 0
    return 1 if perubahan > 0 else -1 if perubahan < 0 else 0


def aturan_a3(arah_harian: int, perubahan_bulanan: float, ada_periode: bool) -> bool:
    """Konflik hanya mengubah vonis klaim yang tidak menyebut periode."""
    return not ada_periode and arah_harian * arah_a2(perubahan_bulanan) < 0


def _periode(teks: str) -> tuple[Optional[str], Optional[int]]:
    """Hanya jendela yang sudah ditetapkan A-1/A-2; periode lain tidak ditebak."""
    teks = teks.lower()
    angka_kata = {"tiga": 3, "empat": 4, "lima": 5, "enam": 6}
    for kata, angka in angka_kata.items():
        teks = re.sub(rf"\b{kata}\b", str(angka), teks)
    if re.search(r"\b(sejak|lalu|20\d{2}|januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\b", teks):
        raise DataUnavailable("Periode historis khusus belum didukung")
    cocok = list(re.finditer(r"\b(\d+)\s*(hari(?:\s+bursa)?|bulan|minggu|tahun)\b", teks))
    if len(cocok) == 1:
        n, satuan = int(cocok[0][1]), cocok[0][2]
        if satuan == "hari bursa" and n == param("A-1", "jendela_hari_bursa"):
            return "harian", None
        if satuan == "bulan" and param("A-2", "bulan_min") <= n <= param("A-2", "bulan_maks"):
            return "bulanan", n
    if cocok or re.search(r"\b(hari|bulan|minggu|tahun|kemarin|sejak|periode|kuartal|januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\b", teks):
        raise DataUnavailable("Periode klaim belum didukung; gunakan 20 hari bursa atau 3–6 bulan")
    return None, None


def _judul_asing(fakta: str, *, berlawanan: bool) -> str:
    """Judul kartu = temuan utamanya, dengan angka; "justru" kalau data berlawanan arah dengan klaim."""
    return ("Justru sebaliknya: " + fakta if berlawanan else fakta[0].upper() + fakta[1:]) + "."


class Asing(Checker):
    id = "asing"

    def run(self, ticker: str, claim: Optional[Claim], today: date) -> Outcome:
        try:
            periode, n_bulan = _periode(claim.text) if claim else (None, None)
        except DataUnavailable:
            alasan = "Periode ini belum didukung. Kami dapat memeriksa 20 hari bursa atau 3–6 observasi bulanan terakhir; kami tidak menggantinya dengan periode lain."
            return Outcome("data_kurang", alasan, card(verdict="tidak_bisa_dicek", check=self.id, rule_id="A-3",
                                                       claim=claim, headline="Periode klaim belum bisa diperiksa.", reason=alasan))
        ev, src = [], []
        arah_harian = perubahan = None
        konteks = []
        fakta_harian = fakta_bulanan = ""
        grafik_harian = grafik_bulanan = None
        try:
            aliran = [r for r in normal.aliran_asing(ticker) if r.tanggal <= today]
            n_hari = param("A-1", "jendela_hari_bursa")
            if len(aliran) < n_hari:
                raise DataUnavailable("Aliran asing belum mencakup jendela A-1")
            aliran = sorted(aliran, key=lambda r: r.tanggal)[-n_hari:]
            borong, total, porsi = aturan_a1(aliran)
            arah_harian = 1 if borong else (-1 if total < 0 else 0)
            hari_masuk = round(porsi * len(aliran))
            fakta_harian = (f"dalam {n_hari} hari bursa terakhir asing {'masuk' if total > 0 else 'keluar'} bersih {rp_kata(total)}"
                            if total else f"dalam {n_hari} hari bursa terakhir beli dan jual asing seimbang")
            if total > 0 and not borong:
                fakta_harian += f", tapi hanya {hari_masuk} dari {len(aliran)} hari yang masuk bersih"
            konteks.append(f"Dalam {n_hari} hari bursa terakhir, asing membeli lebih banyak daripada menjual di {hari_masuk} dari "
                           f"{len(aliran)} hari ({persen_id(porsi, 0)}); disebut borong kalau total masuk bersih dan minimal "
                           f"{persen_id(param('A-1', 'porsi_hari_masuk'), 0)} harinya masuk bersih.")
            ev.extend([Evidence(label=f"Aliran bersih asing {n_hari} hari bursa", value=total, fmt="rp"),
                       Evidence(label="Porsi hari masuk bersih", value=porsi, fmt="pct")])
            src.append(Source(name=f"Sectors · foreign flow · {aliran[0].tanggal}–{aliran[-1].tanggal}", as_of=str(aliran[-1].tanggal)))
            grafik_harian = Chart(type="bar", series=[ChartSeries(
                name="Beli bersih asing per hari (minus = jual bersih)", fmt="rp",
                points=[(str(r.tanggal), r.bersih_rp) for r in aliran])])
        except DataUnavailable:
            if periode == "harian":
                raise
            konteks.append("Aliran harian tidak tersedia untuk konteks.")

        try:
            komposisi = sorted((r for r in normal.komposisi_bulanan(ticker) if r.tanggal <= today), key=lambda r: r.tanggal)
            komposisi = komposisi[-(n_bulan or param("A-2", "bulan_maks")):]
            if n_bulan and len(komposisi) < n_bulan:
                raise DataUnavailable("Komposisi belum mencakup periode klaim")
            perubahan, perubahan_ritel = aturan_a2(komposisi)
            arah_bulanan = arah_a2(perubahan)
            gerak = "naik" if arah_bulanan > 0 else "turun" if arah_bulanan < 0 else "cenderung datar"
            fakta_bulanan = (f"porsi kepemilikan asing {gerak} dari {persen_id(komposisi[0].porsi_asing)} ke "
                             f"{persen_id(komposisi[-1].porsi_asing)} dalam {len(komposisi)} bulan")
            batas_poin = f"{param('A-2', 'batas_perubahan_porsi') * 100:g} poin persen"
            konteks.append(f"Porsi kepemilikan asing {gerak if arah_bulanan else f'datar (berubah kurang dari {batas_poin})'} "
                           f"selama {len(komposisi)} bulan ({komposisi[0].tanggal}–{komposisi[-1].tanggal}). "
                           "Porsi ini dihitung dari saham lokal + asing yang tercatat, bukan seluruh saham emiten.")
            ev.extend([Evidence(label="Porsi asing awal (komposisi tercatat)", value=komposisi[0].porsi_asing, fmt="pct"),
                       Evidence(label="Porsi asing akhir (komposisi tercatat)", value=komposisi[-1].porsi_asing, fmt="pct"),
                       Evidence(label="Perubahan porsi asing", value=perubahan, fmt="pct"),
                       Evidence(label="Perubahan porsi ritel lokal", value=perubahan_ritel, fmt="pct")])
            src.append(Source(name="Sectors · shareholders composition", as_of=str(komposisi[-1].tanggal)))
            grafik_bulanan = Chart(type="line", series=[ChartSeries(
                name="Porsi kepemilikan asing per bulan", fmt="pct",
                points=[(str(r.tanggal), r.porsi_asing) for r in komposisi])])
        except DataUnavailable:
            if periode == "bulanan":
                raise
            konteks.append("Tren bulanan tidak tersedia untuk konteks.")

        if arah_harian is None and perubahan is None:
            raise DataUnavailable("Aliran harian dan komposisi bulanan tidak tersedia")
        if claim is None:
            return Outcome("aman", "Aliran harian dan tren bulanan diperiksa." if arah_harian is not None and perubahan is not None
                           else "Tren bulanan diperiksa; aliran harian tidak tersedia." if arah_harian is None
                           else "Aliran harian diperiksa; tren bulanan tidak tersedia untuk konteks.")
        arah_klaim = -1 if any(k in claim.text.lower() for k in _KATA_JUAL) else 1
        konflik = perubahan is not None and aturan_a3(arah_harian or 0, perubahan, periode is not None)
        pakai_bulanan = periode == "bulanan" or arah_harian is None
        arah = arah_a2(perubahan) if pakai_bulanan else arah_harian
        if periode is None and (arah_harian is None or perubahan is None):
            konteks.append("Hanya satu dataset tersedia; vonis memakai tren kepemilikan bulanan." if pakai_bulanan
                           else "Hanya satu dataset tersedia; vonis memakai aliran harian.")
        verdict = "menyesatkan" if konflik else "sesuai" if arah == arah_klaim else "tidak_sesuai"
        h = (f"Tergantung jendela waktu: {fakta_harian}, tapi {fakta_bulanan}." if konflik
             else _judul_asing(fakta_bulanan if pakai_bulanan else fakta_harian, berlawanan=arah == -arah_klaim))
        return Outcome("aman", h, card(verdict=verdict, check=self.id, rule_id="A-3" if konflik else "A-2" if pakai_bulanan else "A-1",
                                        claim=claim, headline=h, reason=" ".join(konteks), evidence=ev, sources=src,
                                        chart=grafik_bulanan if pakai_bulanan else grafik_harian))
