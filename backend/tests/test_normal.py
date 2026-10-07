"""Parser: JSON buatan lewat adapter fixture, tanpa jaringan atau kredit Sectors."""
import json
from dataclasses import replace
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import settings
from app.data import normal, sectors


@pytest.fixture
def simpan(monkeypatch, tmp_path):
    konfigurasi = replace(settings, data_mode="fixture", fixtures_dir=tmp_path, llm_provider="none")
    monkeypatch.setattr(sectors, "settings", konfigurasi)
    monkeypatch.setattr(main, "settings", konfigurasi)
    monkeypatch.setattr(sectors, "_call_live", lambda *args: pytest.fail("Tes tidak boleh memanggil Sectors"))
    monkeypatch.setattr(main.quota, "_pakai", {})
    monkeypatch.setattr(main, "_CEK", {})

    def tulis(kunci, data):
        p = tmp_path / "MGLV" / f"{kunci}.json"
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps(data), encoding="utf-8")
    return tulis


def test_harga_urut_volume_dan_ticker(simpan):
    simpan("harga_harian", [
        {"date": "2026-09-30", "close": "14650", "volume": "200"},
        {"date": "2026-01-02", "close": 600, "volume": 0},
        {"date": "2026-01-03", "close": 700, "volume": None},
    ])
    harga = normal.harga_harian(" mglv.jk ")
    assert [h.close for h in harga] == [600, 700, 14650]
    assert [h.nilai_transaksi_rp for h in harga] == [0, None, 14650 * 200]
    assert harga[0].tanggal == date(2026, 1, 2)


def test_nama_dan_free_float_desimal(simpan):
    simpan("report", {"symbol": "MGLV.JK", "company_name": " Emiten uji ", "ownership": {
        "major_shareholders": [{"name": "Pengendali", "share_percentage": "0.6708"},
                               {"name": "Public", "share_percentage": "0.3292"}]}})
    assert normal.nama_emiten("MGLV") == "Emiten uji"
    assert normal.free_float("MGLV") == pytest.approx(0.3292)


def test_filings_urut_persen_dan_nilai_rupiah(simpan):
    simpan("filings", {"results": [
        {"timestamp": "2026-09-25T09:00:00Z", "holder_name": "Nextier", "transaction_type": "sell",
         "transaction_value": 2e9, "amount_transaction": 10, "share_percentage_before": 70,
         "share_percentage_after": 62.71},
        {"timestamp": "2026-08-01T10:00:00+07:00", "holder_name": "Nextier", "transaction_type": "SELL",
         "transaction_value": "3000000000", "share_percentage_before": "78.74", "share_percentage_after": 70},
        {"timestamp": "2026-07-01", "holder_name": "Direksi", "transaction_type": "buy",
         "transaction_value": 1000, "share_percentage_before": 0, "share_percentage_after": None},
    ]})
    transaksi = normal.transaksi_orang_dalam("MGLV")
    assert [t.jenis for t in transaksi] == ["beli", "jual", "jual"]
    assert transaksi[0].nilai_rp == 1000 and transaksi[0].sebelum == 0 and transaksi[0].sesudah is None
    assert transaksi[1].sebelum == pytest.approx(0.7874)
    assert transaksi[-1].sesudah == pytest.approx(0.6271)
    assert transaksi[-1].nilai_rp == 2e9  # transaction_value, bukan jumlah saham


def test_filings_pemindahan_bukan_jual_beli(simpan):
    simpan("filings", {"results": [{"transaction_type": "others"}]})
    assert normal.transaksi_orang_dalam("MGLV") == []


def test_aksi_hanya_tanggal_ex(simpan):
    simpan("aksi_korporasi", {"corporate_actions": {
        "dividend": [{"ex_date": "2026-09-01", "payment_date": "2026-09-20"}],
        "right_issue": [{"ex_date": "2026-11-02"}],
        "stock_split": [{"date": "2026-08-01"}],
        "bonus": [{"ex_date": "2026-08-01"}, {"ex_date": None}],
        "upcoming_dividend": None, "agm": [{"date": "2026-07-01"}],
    }})
    assert normal.tanggal_aksi_korporasi("MGLV") == {
        date(2026, 9, 1), date(2026, 11, 2), date(2026, 8, 1)}


def test_suspensi_urut_dan_alasan(simpan):
    simpan("suspensi", {"results": [
        {"suspension_date": "2026-09-20", "reason": "Alasan terbaru"},
        {"suspension_date": "2026-04-06", "reason": "Alasan lama"},
    ]})
    riwayat = normal.riwayat_suspensi("MGLV")
    assert [s.tanggal for s in riwayat] == [date(2026, 4, 6), date(2026, 9, 20)]
    assert riwayat[-1].alasan == "Alasan terbaru"


@pytest.mark.parametrize("aksi", [None, {}, {"dividend": None, "right_issue": []}])
def test_riwayat_kosong_bukan_data_kurang(simpan, aksi):
    simpan("filings", {"results": []})
    simpan("suspensi", {"results": []})
    simpan("aksi_korporasi", {"corporate_actions": aksi})
    assert normal.transaksi_orang_dalam("MGLV") == []
    assert normal.riwayat_suspensi("MGLV") == []
    assert normal.tanggal_aksi_korporasi("MGLV") == set()


@pytest.mark.parametrize("parser,kunci,data", [
    (normal.nama_emiten, "report", {"company_name": ""}),
    (normal.free_float, "report", {"ownership": {"major_shareholders": []}}),
    (normal.free_float, "report", {"ownership": {"major_shareholders": [{"name": "Public", "share_percentage": "32.92"}]}}),
    (normal.free_float, "report", {"ownership": None}),
    (normal.harga_harian, "harga_harian", []),
    (normal.harga_harian, "harga_harian", [{"date": "2026-09-30", "close": None}]),
    (normal.harga_harian, "harga_harian", [{"date": "2026-09-30", "close": "NaN"}]),
    (normal.harga_harian, "harga_harian", [{"date": "2026-09-30", "close": 0}]),
    (normal.harga_harian, "harga_harian", [{"date": "bukan tanggal", "close": 600}]),
    (normal.harga_harian, "harga_harian", [{"date": "2026-09-30", "close": 600, "volume": -1}]),
    (normal.riwayat_suspensi, "suspensi", {}),
    (normal.riwayat_suspensi, "suspensi", {"results": [{"suspension_date": "2026-09-30", "reason": None}]}),
    (normal.transaksi_orang_dalam, "filings", {"results": None}),
    (normal.transaksi_orang_dalam, "filings", {"results": [{"transaction_type": "unknown"}]}),
    (normal.transaksi_orang_dalam, "filings", {"results": [{"transaction_type": "sell", "timestamp": "2026-09-30",
                                                         "holder_name": "Nextier", "transaction_value": None}]}),
    (normal.tanggal_aksi_korporasi, "aksi_korporasi", {}),
    (normal.tanggal_aksi_korporasi, "aksi_korporasi", {"corporate_actions": {"stock_split": "tidak sesuai"}}),
])
def test_data_kosong_atau_rusak_tidak_ditebak(simpan, parser, kunci, data):
    simpan(kunci, data)
    with pytest.raises(sectors.DataUnavailable):
        parser("MGLV")


def test_fixture_hilang_tidak_memanggil_live(simpan):
    with pytest.raises(sectors.DataUnavailable, match="Fixture"):
        normal.harga_harian("MGLV")


def test_laba_urut_dan_rugi_tetap_negatif(simpan):
    simpan("keuangan_kuartalan", [
        {"date": "2026-06-30", "earnings": "120"},
        {"date": "2026-03-31", "earnings": -5},
    ])
    assert normal.laba_kuartalan("MGLV") == [normal.Kuartal("2026-03-31", -5), normal.Kuartal("2026-06-30", 120)]


def test_valuasi_tahun_terbaru_dan_null(simpan):
    simpan("report", {"valuation": {"historical_valuation": [
        {"year": 2026, "pe": "7.5", "pb": 1.4},
        {"year": 2024, "pe": 10, "pb": 2}], "forward_pe": None, "latest_close_date": "2026-09-28"}})
    assert normal.valuasi("MGLV") == normal.Valuasi(7.5, 1.4, None, date(2026, 9, 28))


@pytest.mark.parametrize("nilai", [None, 0, 0.11])
def test_dividen_bukan_rata_rata_sektor(simpan, nilai):
    from app.checkers.dividen import Dividen
    simpan("report", {"dividend": {"yield_ttm": nilai, "payout_ratio": None, "dividend_yield_avg": 0.07},
                      "valuation": {"latest_close_date": "2026-09-28"}})
    assert normal.dividen("MGLV") == normal.Dividen(nilai, None, None, date(2026, 9, 28) if nilai else None)
    if nilai in (None, 0):
        assert Dividen().run("MGLV", None, date(2026, 9, 30)).status == "tidak_relevan"


def test_aliran_asing_urut_dan_nol_sah(simpan):
    simpan("aliran_asing", {"data": [
        {"date": "2026-09-30", "net_foreign_inflow": "-100"},
        {"date": "2026-09-29", "net_foreign_inflow": 0}]})
    assert normal.aliran_asing("MGLV") == [
        normal.AliranAsing(date(2026, 9, 29), 0), normal.AliranAsing(date(2026, 9, 30), -100)]


def test_komposisi_denominator_lokal_asing_dan_null(simpan):
    simpan("komposisi_pemegang", {"data": [
        {"date": "2026-08-31", "total_l": 60, "total_f": 40, "individual_l": 20,
         "shares_number": 1000, "numbers_of_shareholders": "25"},
        {"date": "2026-07-31", "total_l": 70, "total_f": 30, "individual_l": 10,
         "numbers_of_shareholders": None}]})
    hasil = normal.komposisi_bulanan("MGLV")
    assert hasil[-1] == normal.KomposisiBulanan(date(2026, 8, 31), 0.4, 0.2, 25)
    assert hasil[0].jumlah_pemegang is None


@pytest.mark.parametrize("parser,kunci,data", [
    (normal.laba_kuartalan, "keuangan_kuartalan", []),
    (normal.laba_kuartalan, "keuangan_kuartalan", [{"date": "2026-06-30", "earnings": None}]),
    (normal.valuasi, "report", {"valuation": {"historical_valuation": []}}),
    (normal.valuasi, "report", {"valuation": {"historical_valuation": [{"year": None}]}}),
    (normal.valuasi, "report", {"valuation": {"historical_valuation": [{"year": 2026, "pe": 10, "pb": 2}]}}),
    (normal.dividen, "report", {"dividend": {"yield_ttm": 0.1}}),
    (normal.dividen, "report", {"dividend": {}}),
    (normal.dividen, "report", {"dividend": None}),
    (normal.aliran_asing, "aliran_asing", {"data": []}),
    (normal.aliran_asing, "aliran_asing", {"data": [{"date": "2026-09-30", "net_foreign_inflow": None}]}),
    (normal.komposisi_bulanan, "komposisi_pemegang", {"data": []}),
    (normal.komposisi_bulanan, "komposisi_pemegang", {"data": [
        {"date": "2026-08-31", "total_l": 0, "total_f": 0, "individual_l": 0}]}),
    (normal.komposisi_bulanan, "komposisi_pemegang", {"data": [
        {"date": "2026-08-31", "total_l": 60, "total_f": 40, "individual_l": 70}]}),
])
def test_b2_data_hilang_tidak_ditebak(simpan, parser, kunci, data):
    simpan(kunci, data)
    with pytest.raises(sectors.DataUnavailable):
        parser("MGLV")


@pytest.mark.parametrize("ticker", ["BBRI", "BREN", "PTBA"])
def test_form_lengkap_fixture_b2(monkeypatch, ticker):
    from app.engine import run_cek
    from app.schemas import CekRequest
    diperlukan = ("report", "keuangan_kuartalan", "aliran_asing", "harga_harian", "aksi_korporasi", "filings", "suspensi")
    if not all((settings.fixtures_dir / ticker / f"{k}.json").exists() for k in diperlukan):
        pytest.skip(f"Fixture lengkap {ticker} belum tersedia")
    monkeypatch.setattr(sectors, "settings", replace(settings, data_mode="fixture"))
    monkeypatch.setattr(sectors, "_call_live", lambda *args: pytest.fail("Tes tidak boleh memanggil Sectors"))
    hasil = run_cek(CekRequest(ticker=ticker, claims=[]), today=date(2026, 9, 30))
    assert len([f for f in hasil.form if not f.check.startswith("m_")]) == 8
    assert all(f.status not in ("data_kurang", "gagal") for f in hasil.form), hasil.form
    assert normal.laba_kuartalan(ticker)[-1].periode == "2026-06-30"
    assert normal.komposisi_bulanan(ticker)[-1].tanggal == date(2026, 8, 31)
    assert normal.valuasi(ticker).as_of == date(2026, 9, 28)
    assert normal.dividen(ticker).as_of == date(2026, 9, 28)
    if ticker == "BREN":
        assert normal.valuasi(ticker).forward_pe is None


def test_api_mglv_melewati_parser_asli(simpan):
    hari = date.today()
    simpan("report", {"company_name": "Emiten uji", "ownership": {
        "major_shareholders": [{"name": "Public", "share_percentage": "0.3292"}]}})
    simpan("harga_harian", [{"date": str(hari - timedelta(days=59 - i)),
                             "close": 600 * (14650 / 600) ** (i / 59), "volume": 100}
                            for i in range(60)])
    simpan("aksi_korporasi", {"corporate_actions": {}})
    simpan("suspensi", {"results": [
        {"suspension_date": str(hari - timedelta(days=20)), "reason": "Kenaikan harga"},
        {"suspension_date": str(hari - timedelta(days=50)), "reason": "Kenaikan harga"}]})
    simpan("filings", {"results": [
        {"timestamp": str(hari - timedelta(days=10)), "holder_name": "Nextier", "transaction_type": "sell",
         "transaction_value": 2e9, "share_percentage_before": 70, "share_percentage_after": 62.71},
        {"timestamp": str(hari - timedelta(days=40)), "holder_name": "Nextier", "transaction_type": "sell",
         "transaction_value": 3e9, "share_percentage_before": 78.74, "share_percentage_after": 70}]})
    client = TestClient(main.app)
    klaim = client.post("/api/klaim", json={"text": "MGLV masih bakal terbang, dari 600 udah 14 ribuan, buruan!"})
    assert klaim.status_code == 200
    jawaban = client.post("/api/cek", json={"ticker": "MGLV", "claims": klaim.json()["claims"]})
    assert jawaban.status_code == 200
    hasil = jawaban.json()
    assert hasil["company"] == "Emiten uji"
    assert [k["verdict"] for k in hasil["claims"]] == ["tidak_bisa_dicek", "sesuai"]
    status = {f["check"]: f["status"] for f in hasil["form"]}
    assert {k: status[k] for k in ("suspensi", "orang_dalam", "lonjakan_harga", "free_float")} == {
        "suspensi": "temuan", "orang_dalam": "temuan", "lonjakan_harga": "temuan", "free_float": "aman"}
    assert status["laba"] == "data_kurang"  # B2 menyusul
    kartu = {k["check"]: k for k in hasil["untold"]}
    assert kartu["suspensi"]["sources"][0]["as_of"] == str(hari - timedelta(days=20))
    assert kartu["orang_dalam"]["sources"][0]["as_of"] == str(hari - timedelta(days=10))
    assert [e["value"] for e in kartu["orang_dalam"]["evidence"]] == pytest.approx([0.7874, 0.6271])
    assert all(k["sources"] for k in hasil["claims"] + hasil["untold"] if k["verdict"] != "tidak_bisa_dicek")


def test_fixture_snapshot_mglv_september(monkeypatch):
    diperlukan = ("report", "harga_harian", "aksi_korporasi", "suspensi", "filings")
    if not all((settings.fixtures_dir / "MGLV" / f"{k}.json").exists() for k in diperlukan):
        pytest.skip("Fixture MGLV asli belum tersedia; tes JSON buatan tetap berjalan")
    monkeypatch.setattr(sectors, "settings", replace(settings, data_mode="fixture"))
    harga = normal.harga_harian("MGLV")
    if harga[-1].tanggal > date(2026, 9, 30):
        pytest.skip("Fixture diperbarui setelah snapshot demo September; angka FINAL_PLAN belum diverifikasi")
    assert len(normal.riwayat_suspensi("MGLV")) == 7
    assert any(t.nama.lower().startswith("nextier") and t.jenis == "jual" and
               t.sesudah == pytest.approx(0.6271) for t in normal.transaksi_orang_dalam("MGLV"))
    assert harga[0].close == 600 and harga[-1].close == 14650
    assert normal.free_float("MGLV") == pytest.approx(0.33, abs=0.005)
