"""Kalimat kartu (judul + penjelasan) ditulis kode, bukan AI: setiap cabang harus menyebut temuan yang benar."""
from datetime import date

import pytest

from app.checkers import laba as modul_laba
from app.checkers.asing import _judul_asing
from app.checkers.lonjakan_harga import _kalimat_h2
from app.checkers.pemegang import _alasan_pemegang, _judul_pemegang
from app.data import normal
from app.schemas import Claim

AWAL, AKHIR, MULAI = normal.HargaHarian(date(2025, 9, 26), 600), normal.HargaHarian(date(2026, 9, 29), 14650), date(2025, 9, 26)


def test_h2_sesuai_menyebut_kedua_harga():
    judul, alasan = _kalimat_h2(600, 14000, AWAL, AKHIR, MULAI, ok=True)
    assert judul == "Harga Rp600 memang pernah tercatat, dan harga terakhirnya Rp14.650."
    assert "dekat dengan Rp14.000 yang disebut di klaim" in alasan and "2025-09-26–2026-09-29" in alasan
    assert "lalu naik ke Rp14.650 pada 2026-09-29" in alasan


def test_h2_arah_hanya_ditulis_kalau_harga_awal_lebih_dulu():
    sesudah = normal.HargaHarian(date(2026, 10, 1), 600)
    _, alasan = _kalimat_h2(600, 14000, sesudah, AKHIR, MULAI, ok=True)
    assert "naik" not in alasan and "turun" not in alasan
    _, alasan = _kalimat_h2(600, 500, AWAL, normal.HargaHarian(date(2026, 9, 29), 480), MULAI, ok=True)
    assert "lalu turun ke Rp480" in alasan


def test_h2_tidak_sesuai_menyebut_bagian_yang_meleset():
    judul, alasan = _kalimat_h2(900, 14000, AWAL, AKHIR, MULAI, ok=False)
    assert judul == "Harga Rp900 tidak pernah tercatat di data kami."
    assert "paling dekat adalah Rp600" in alasan
    judul, _ = _kalimat_h2(600, 20000, AWAL, AKHIR, MULAI, ok=False)
    assert judul == "Harga terakhirnya Rp14.650, jauh dari Rp20.000 yang disebut di klaim."


def test_asing_berlawanan_memakai_justru():
    fakta = "dalam 20 hari bursa terakhir asing keluar bersih Rp224,1 miliar"
    assert _judul_asing(fakta, berlawanan=True) == "Justru sebaliknya: " + fakta + "."
    assert _judul_asing(fakta, berlawanan=False) == "Dalam 20 hari bursa terakhir asing keluar bersih Rp224,1 miliar."


def test_pemegang_judul_memakai_tapi_kalau_arah_beda():
    assert _judul_pemegang([0.224, 0.24], [591364, 546718]) == (
        "Porsi investor ritel naik dari 22,4% ke 24%, tapi jumlah pemegang sahamnya turun dari 591.364 ke 546.718.")
    assert ", dan jumlah" in _judul_pemegang([0.2, 0.25], [100, 120])


@pytest.mark.parametrize("verdict,pemegang_naik,bagian", [
    ("sesuai", True, "porsi investor ritel naik minimal 1 poin persen, dan jumlah pemegang saham naik"),
    ("menyesatkan", False, "porsi investor ritel naik minimal 1 poin persen, tapi jumlah pemegang saham tidak naik"),
    ("menyesatkan", True, "porsi investor ritel tidak naik minimal 1 poin persen, tapi jumlah pemegang saham naik"),
    ("tidak_sesuai", False, "porsi investor ritel tidak naik minimal 1 poin persen, dan jumlah pemegang saham tidak naik"),
])
def test_pemegang_alasan_menyebut_syarat_yang_terpenuhi(verdict, pemegang_naik, bagian):
    assert bagian in _alasan_pemegang(verdict, pemegang_naik, 6, "2026-03-31", "2026-08-31")


def test_pemegang_tanpa_klaim_hanya_menyebut_periode():
    assert _alasan_pemegang("info", False, 6, "2026-03-31", "2026-08-31").startswith("Data 6 bulan terakhir")


def _kuartal(*laba):
    return [normal.Kuartal(periode=f"2025-{i + 1:02d}-28", laba_bersih=v) for i, v in enumerate(laba)]


@pytest.mark.parametrize("teks,laba,judul", [
    ("laba naik 30%", (100, 90, 80, 70, 130), "Klaim bilang laba naik, tapi selama 4 kuartal terakhir trennya justru turun."),
    ("laba naik 30%", (100, 100, 110, 120, 130), "Laba kuartal terakhir memang naik 30% dibanding tahun lalu."),
    ("laba naik 80%", (100, 100, 110, 120, 130), "Hitungan kami: laba kuartal terakhir naik 30%, bukan naik 80% seperti di klaim."),
])
def test_laba_judul_per_vonis(monkeypatch, teks, laba, judul):
    monkeypatch.setattr(normal, "laba_kuartalan", lambda ticker: _kuartal(*laba))
    kartu = modul_laba.Laba().run("XXXX", Claim(id="c1", text=teks, checks=["laba"]), date(2026, 9, 30)).card
    assert kartu.headline == judul and kartu.reason
