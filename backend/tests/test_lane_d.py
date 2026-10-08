"""CSV, aturan modul, sumber, dan endpoint Lane D tanpa jaringan."""
from dataclasses import replace
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import settings
from app.data import bahan, normal, sectors
from app.modul import komoditas, free_float
from app.checkers.analis import kartu_analis
from app.checkers.pemegang import kartu_pemegang
from app.checkers.m_komoditas import MKomoditas
from app.schemas import Claim, KomoditasList, KomoditasDetail
from app.untold import providers

HARI = date(2026, 10, 7)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(sectors, "settings", replace(settings, data_mode="fixture"))
    monkeypatch.setattr(main, "settings", replace(settings, data_mode="fixture"))
    monkeypatch.setattr(sectors, "_call_live", lambda *args: pytest.fail("Lane D tidak boleh memakai kredit"))


def test_pemetaan_semua_segmen_dan_campuran():
    for ticker in {r["symbol"] for r in bahan.baca("segmen_pendapatan")}:
        assert komoditas.segmen_terpetakan(ticker)
    assert komoditas.porsi_pendapatan("MDKA", "emas") == 0
    assert komoditas.porsi_pendapatan("MDKA", "tembaga") == pytest.approx(0.0593)
    assert komoditas.komoditas_terbesar("MDKA") == ("nikel", 0.8239)
    assert komoditas.porsi_pendapatan("ANTM", "nikel") == pytest.approx(0.1374)


def test_kategori_semua_korelasi_sesuai_csv():
    for r in bahan.baca("saham_vs_komoditas"):
        assert komoditas.aturan_k2(float(r["korelasi_bulanan"])) == r["kategori"]


def test_komoditas_tanpa_segmen_tidak_mengarang_porsi(monkeypatch):
    asli = bahan.baris
    def tanpa_segmen(nama, ticker):
        if nama == "segmen_pendapatan":
            raise sectors.DataUnavailable("Segmen kosong")
        return asli(nama, ticker)
    monkeypatch.setattr(bahan, "baris", tanpa_segmen)
    item = komoditas.item("MDKA", "emas")
    assert item.porsi_pendapatan is None and item.korelasi == 0.4
    with pytest.raises(sectors.DataUnavailable):
        komoditas.porsi_pendapatan("MDKA", "emas")


def test_k1_tetap_bekerja_tanpa_korelasi(monkeypatch):
    def kosong(*args):
        raise sectors.DataUnavailable("Korelasi kosong")
    monkeypatch.setattr(komoditas, "item", kosong)
    kartu = MKomoditas().run("MDKA", Claim(id="c1", text="saham emas", checks=["m_komoditas"]), HARI).card
    assert kartu.verdict == "menyesatkan" and kartu.sources[0].as_of == "2024-12-31"


@pytest.mark.parametrize("jenis", list(komoditas.NAMA_SERI))
def test_endpoint_daftar_komoditas(jenis):
    res = TestClient(main.app).get("/api/modul/komoditas", params={"jenis": jenis})
    assert res.status_code == 200, res.text
    data = KomoditasList.model_validate(res.json())
    assert data.items and all(i.komoditas == jenis for i in data.items)
    assert all(s.as_of for i in data.items for s in i.sources)


def test_endpoint_detail_dan_data_tidak_ada():
    client = TestClient(main.app)
    res = client.get("/api/modul/komoditas/MDKA")
    assert res.status_code == 200
    data = KomoditasDetail.model_validate(res.json())
    assert {i.komoditas for i in data.items} == {"emas", "tembaga"}
    assert client.get("/api/modul/komoditas/UJI").status_code == 404
    assert client.get("/api/modul/komoditas?jenis=minyak").status_code == 422


def test_endpoint_mock_jujur_dan_valid(monkeypatch):
    monkeypatch.setattr(main, "settings", replace(settings, data_mode="mock"))
    client = TestClient(main.app)
    assert client.get("/api/modul/komoditas/MDKA").status_code == 200
    assert client.get("/api/modul/komoditas/ANTM").status_code == 404
    assert client.get("/api/modul/komoditas?jenis=emas").json()["items"]
    assert client.get("/api/modul/komoditas?jenis=nikel").json()["items"] == []


def test_radar_menandai_hanya_papan_aktif():
    aktif = {r["symbol"] for r in bahan.baca("papan_pemantauan_khusus") if r["aktif"] == "ya"}
    radar = free_float.daftar()
    assert any(i.papan_pemantauan for i in radar.items)
    assert all(i.papan_pemantauan == (i.ticker in aktif) for i in radar.items)


def test_mglv_kartu_snapshot_dan_right_issue(monkeypatch):
    board = providers.papan_pemantauan("MGLV", [], HARI)
    assert "dihapus 28 Sep 2026" in board.reason
    assert board.evidence[2].value == "sudah keluar"
    def tanpa_harga(*args):
        raise sectors.DataUnavailable("Harga kosong")
    monkeypatch.setattr(normal, "harga_harian", tanpa_harga)
    aksi = providers.aksi_korporasi("MGLV", [], HARI)
    assert any(e.value == 8880 for e in aksi.evidence)
    assert all(s.as_of for s in aksi.sources)


def test_c1_batas_jendela_dan_tanggal_berlalu(monkeypatch):
    def rows(nama, ticker):
        return [{"jenis": "dividend", "tanggal": str(HARI + timedelta(days=n))} for n in (-1, 0, 90, 91)]
    monkeypatch.setattr(bahan, "baris", rows)
    kartu = providers.aksi_korporasi("UJI", [], HARI)
    assert [e.value for e in kartu.evidence] == [str(HARI), str(HARI + timedelta(days=90))]


def test_analis_data_kosong_tidak_menjadi_nol(monkeypatch):
    monkeypatch.setattr(bahan, "baris", lambda *args: [{"jumlah_rekomendasi": ""}])
    with pytest.raises(sectors.DataUnavailable):
        kartu_analis("UJI")


def _rating(buy, strong_buy, hold):
    return [{"jumlah_rekomendasi": str(buy + strong_buy + hold), "buy": str(buy), "strong_buy": str(strong_buy),
             "hold": str(hold), "sell": "0", "strong_sell": "0", "diperbarui": "2026-09-30"}]


@pytest.mark.parametrize("teks,rating,judul", [
    ("Semua analis rekomendasi buy UJI", (60, 8, 2), "Tidak semua: 68 dari 70 rekomendasi adalah buy atau strong buy."),
    ("Mayoritas analis bilang buy UJI", (50, 6, 14),
     "56 dari 70 rekomendasi adalah buy atau strong buy (80%), di bawah batas 90% untuk disebut mayoritas."),
    ("Semua analis rekomendasi buy UJI", (60, 10, 0), "70 dari 70 rekomendasi adalah buy atau strong buy."),
])
def test_analis_judul_menyebut_syarat_yang_gagal(monkeypatch, teks, rating, judul):
    from app.schemas import Claim
    monkeypatch.setattr(bahan, "baris", lambda *args: _rating(*rating))
    assert kartu_analis("UJI", Claim(id="c1", text=teks, checks=["analis"])).headline == judul


@pytest.mark.parametrize("teks", ["emas lagi naik", "harga emas dunia naik terus"])
def test_klaim_harga_komoditas_saja_tidak_dinilai_k1(teks):
    """'emas lagi naik' bukan klaim 'MDKA = saham emas'; jangan salin vonis K-1 ke klaim ini."""
    from app.checkers.m_komoditas import MKomoditas
    from app.schemas import Claim
    out = MKomoditas().run("MDKA", Claim(id="c2", text=teks, checks=["m_komoditas"]), HARI)
    assert out.card.verdict == "tidak_bisa_dicek" and out.card.check == "m_komoditas"
    assert "bukan saham MDKA" in out.card.headline


@pytest.mark.parametrize("teks", ["MDKA saham emas", "katanya ini saham emas", "mdka emiten emas"])
def test_klaim_yang_mengaitkan_saham_dan_komoditas_tetap_dinilai(teks):
    from app.checkers.m_komoditas import _tentang_saham
    assert _tentang_saham(teks, "MDKA")


def test_kartu_konteks_tidak_mengulang_kartu_klaim(monkeypatch):
    """Penyedia 'analis' menambah kartu konteks yang sama persis dengan kartu klaim N-1; jangan dobel."""
    from app.engine import run_cek
    from app.schemas import CekRequest, Claim
    monkeypatch.setattr(bahan, "baris", lambda nama, ticker: _rating(60, 8, 2) if nama == "rating_analis" else [])
    res = run_cek(CekRequest(ticker="UJI", claims=[Claim(id="c1", text="Semua analis rekomendasi buy UJI",
                                                          checks=["analis"])]), HARI)
    assert [c.check for c in res.claims] == ["analis"]
    assert not any(c.check == "analis" for c in res.untold)


def test_pemegang_data_kosong_dan_bulan_hilang(monkeypatch):
    asli = bahan.baris("komposisi_pemegang_saham", "BUMI")[-6:]
    rows = [dict(r) for r in asli]
    rows[-1]["jumlah_pemegang"] = ""
    monkeypatch.setattr(bahan, "baris", lambda *args: rows)
    with pytest.raises(sectors.DataUnavailable):
        kartu_pemegang("BUMI", today=HARI)
    monkeypatch.setattr(bahan, "baris", lambda *args: asli[:2] + asli[3:])
    with pytest.raises(sectors.DataUnavailable, match="tidak lengkap"):
        kartu_pemegang("BUMI", today=HARI)


def test_likuiditas_volume_kosong_dan_tanggal_sumber(monkeypatch):
    harga = [normal.HargaHarian(HARI - timedelta(days=59 - i), 100, 5e8) for i in range(60)]
    monkeypatch.setattr(normal, "harga_harian", lambda _: harga)
    kartu = providers.likuiditas("UJI", [], HARI)
    assert kartu.evidence[0].value == 5e8 and kartu.sources[0].as_of == str(HARI)
    harga[-1].nilai_transaksi_rp = None
    with pytest.raises(sectors.DataUnavailable):
        providers.likuiditas("UJI", [], HARI)
