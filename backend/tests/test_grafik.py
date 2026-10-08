"""Grafik kartu: titiknya diambil dari data yang sama dengan vonis, bukan dibuat ulang."""
from datetime import date, timedelta

from app.checkers import laba as modul_laba
from app.checkers.laba import _label_kuartal
from app.checkers.lonjakan_harga import _TITIK_MAKS, _grafik_harga
from app.data import normal
from app.schemas import Claim


def test_label_kuartal():
    assert [_label_kuartal(p) for p in ("2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31")] == [
        "Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"]


def test_grafik_laba_memakai_kuartal_yang_sama_dengan_bukti(monkeypatch):
    kuartal = [normal.Kuartal(periode=p, laba_bersih=v) for p, v in
               (("2025-03-31", 100), ("2025-06-30", 90), ("2025-09-30", 80), ("2025-12-31", 70), ("2026-03-31", 130))]
    monkeypatch.setattr(normal, "laba_kuartalan", lambda ticker: kuartal)
    kartu = modul_laba.Laba().run("XXXX", Claim(id="c1", text="laba naik 30%", checks=["laba"]), date(2026, 9, 30)).card
    seri = kartu.chart.series[0]
    assert kartu.chart.type == "bar" and seri.fmt == "rp"
    assert seri.points == [("Q2 2025", 90), ("Q3 2025", 80), ("Q4 2025", 70), ("Q1 2026", 130)]
    assert [p[1] for p in seri.points] == [e.value for e in kartu.evidence]


def test_grafik_harga_dipangkas_tapi_ujungnya_tetap_harga_terakhir():
    mulai = date(2025, 1, 1)
    harga = [normal.HargaHarian(mulai + timedelta(days=i), 100 + i) for i in range(301)]
    seri = _grafik_harga(harga).series[0]
    assert len(seri.points) <= _TITIK_MAKS + 1
    assert seri.points[0] == (str(mulai), 100) and seri.points[-1] == (str(harga[-1].tanggal), 400)
    pendek = _grafik_harga(harga[:22]).series[0]
    assert len(pendek.points) == 22
