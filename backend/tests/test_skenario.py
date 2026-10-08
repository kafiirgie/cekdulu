"""Skenario FINAL_PLAN §6 lewat pemecah klaim dan engine asli, tanpa API/LLM.

Skip hanya jika fixture belum dibagikan. Semua skenario memakai aturan
yang berlaku dan jendela data tercatat, bukan angka contoh yang dipaksakan.
"""
from dataclasses import replace
from datetime import date

import pytest

from app.ai.fallback import pecah_klaim
from app.config import settings
from app.data import normal, sectors
from app.engine import run_cek
from app.schemas import CekRequest

HARI = date(2026, 10, 7)
MGLV = "MGLV masih bakal terbang, dari 600 udah 14 ribuan, buruan!"


@pytest.fixture(autouse=True)
def tanpa_jaringan(monkeypatch):
    monkeypatch.setattr(sectors, "settings", replace(settings, data_mode="fixture"))
    monkeypatch.setattr(sectors, "_call_live", lambda *args: pytest.fail("Skenario tidak boleh memakai kredit Sectors"))


def perlu_fixture(ticker, *kunci):
    hilang = [k for k in kunci if not (settings.fixtures_dir / ticker / f"{k}.json").exists()]
    if hilang:
        pytest.skip(f"Fixture {ticker} belum tersedia: {', '.join(hilang)}")


def cek(teks):
    pecahan = pecah_klaim(teks)
    assert pecahan.ticker
    hasil = run_cek(CekRequest(ticker=pecahan.ticker, claims=pecahan.claims), today=HARI)
    assert len(hasil.claims) == len(pecahan.claims)
    assert not any(f.status == "gagal" for f in hasil.form)
    for kartu in hasil.claims + hasil.untold:
        if kartu.verdict != "tidak_bisa_dicek":
            assert kartu.sources, kartu
            assert all(s.as_of for s in kartu.sources), kartu
    return hasil


def test_mglv_prediksi_harga_dan_temuan_dari_fixture():
    perlu_fixture("MGLV", "report", "harga_harian", "aksi_korporasi", "filings", "suspensi")
    hasil = cek(MGLV)
    assert hasil.claims[0].verdict == "tidak_bisa_dicek"
    harga = normal.harga_harian("MGLV")
    kartu_harga = hasil.claims[1]
    assert kartu_harga.rule_id == "H-2"
    awal = min(harga, key=lambda h: abs(h.close - 600))
    assert [e.value for e in kartu_harga.evidence] == [awal.close, harga[-1].close]
    assert kartu_harga.verdict == "sesuai"
    assert [s.as_of for s in kartu_harga.sources] == [str(awal.tanggal), str(harga[-1].tanggal)]
    kartu = {k.check: k for k in hasil.untold}
    assert {"suspensi", "orang_dalam"} <= kartu.keys()
    assert kartu["suspensi"].evidence[0].value == 7
    assert [e.value for e in kartu["orang_dalam"].evidence if e.label.lower().startswith("nextier")] == pytest.approx([0.7874, 0.6271])


def test_mglv_kartu_tambahan_lane_d2():
    perlu_fixture("MGLV", "report", "harga_harian", "aksi_korporasi", "filings", "suspensi")
    kartu = {k.check for k in cek(MGLV).untold}
    assert {"papan_pemantauan", "aksi_korporasi"} <= kartu


def test_mdka_prediksi_tetap_tidak_bisa_dicek():
    hasil = cek("MDKA saham emas, emas lagi naik pasti ikut")
    assert hasil.claims[1].verdict == "tidak_bisa_dicek"


def test_mdka_klaim_saham_emas():
    perlu_fixture("MDKA", "segmen", "harga_harian")
    hasil = cek("MDKA saham emas, emas lagi naik pasti ikut")
    assert hasil.claims[0].verdict == "menyesatkan"
    assert hasil.claims[0].rule_id == "K-1"


def test_antm_analis_dan_konteks_proyeksi():
    perlu_fixture("ANTM", "report")
    hasil = cek("Semua analis rekomendasi buy ANTM")
    assert hasil.claims[0].verdict == "tidak_sesuai"  # 68/70 bukan seluruh rekomendasi.
    # Proyeksi analis tampil sebagai konteks di kartu klaim itu sendiri, tidak diulang di "Yang tidak diceritakan".
    assert any(e.label.startswith("Proyeksi") for e in hasil.claims[0].evidence)
    assert not any(k.check == "analis" for k in hasil.untold)


def test_antm_mayoritas_rekomendasi_buy():
    assert cek("Mayoritas analis rekomendasi buy ANTM").claims[0].verdict == "sesuai"


def test_bumi_asing_memakai_dataset_yang_tersedia():
    perlu_fixture("BUMI", "komposisi_pemegang", "aliran_asing")
    hasil = cek("BUMI diserbu ritel, asing juga masuk")
    assert hasil.claims[1].verdict == "tidak_sesuai"
    assert hasil.claims[1].rule_id in ("A-1", "A-2")


def test_bumi_asing_tanpa_aliran_harian_tetap_diputus(monkeypatch):
    perlu_fixture("BUMI", "komposisi_pemegang")
    def kosong(_):
        raise sectors.DataUnavailable("Aliran harian tidak tersedia")
    monkeypatch.setattr(normal, "aliran_asing", kosong)
    kartu = cek("BUMI asing juga masuk").claims[0]
    assert kartu.verdict == "tidak_sesuai" and kartu.rule_id == "A-2"


def test_bumi_ritel_dan_asing():
    perlu_fixture("BUMI", "komposisi_pemegang")
    hasil = cek("BUMI diserbu ritel, asing juga masuk")
    assert [k.verdict for k in hasil.claims] == ["menyesatkan", "tidak_sesuai"]


def test_psab_dividen_dan_payout():
    perlu_fixture("PSAB", "report")
    hasil = cek("PSAB dividennya 25%, gede banget")
    assert hasil.claims[0].verdict == "sesuai"
    payout = next(k for k in hasil.untold if k.rule_id == "D-2")
    assert next(e.value for e in payout.evidence if e.label == "Payout ratio") > 1


def test_ticker_saja_bren_mengaktifkan_radar():
    perlu_fixture("BREN", "report")
    hasil = cek("BREN")
    assert hasil.claims == []
    assert next(f for f in hasil.form if f.check == "free_float").status == "temuan"
    assert next(f for f in hasil.form if f.check == "m_free_float").status == "modul_aktif"
    kartu = next(k for k in hasil.untold if k.rule_id == "F-1")
    assert kartu.evidence[0].value == pytest.approx(normal.free_float("BREN"))


def test_klaim_yield_tidak_menyembunyikan_temuan_payout(monkeypatch):
    from app.schemas import Claim
    monkeypatch.setattr(normal, "dividen", lambda _: normal.Dividen(0.252, 1.145, None, HARI))
    klaim = Claim(id="c1", text="dividen 25%", checks=["dividen"])
    hasil = run_cek(CekRequest(ticker="UJI", claims=[klaim]), today=HARI)
    assert hasil.claims[0].verdict == "sesuai"
    assert [k.rule_id for k in hasil.untold if k.check == "dividen"] == ["D-2"]
    assert hasil.untold[-1].sources[0].as_of == str(HARI)


def test_kartu_info_klaim_tidak_diduplikasi_di_untold(monkeypatch):
    from app.schemas import Claim
    monkeypatch.setattr(normal, "riwayat_suspensi", lambda _: [normal.Suspensi(HARI, "Peningkatan harga")])
    klaim = Claim(id="c1", text="pernah suspensi", checks=["suspensi"])
    hasil = run_cek(CekRequest(ticker="UJI", claims=[klaim]), today=HARI)
    assert hasil.claims[0].rule_id == "S-1"
    assert "1 informasi" in hasil.summary
    assert not any(k.rule_id == "S-1" for k in hasil.untold)
