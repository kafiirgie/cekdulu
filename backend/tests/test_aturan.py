"""Tes aturan murni. Ini bukti utama "aturan yang memutuskan, bukan AI".
Setiap aturan di contract/rules.json idealnya punya minimal satu tes di sini."""
from datetime import date, timedelta

from app.checkers.asing import arah_a2, aturan_a1, aturan_a2, aturan_a3
from app.checkers.base import angka_persen, angka_rupiah, rp
from app.checkers.dividen import aturan_d1, aturan_d1_periode, aturan_d2
from app.checkers.free_float import aturan_f1
from app.checkers.laba import arah_tren, aturan_l1, aturan_l2, pertumbuhan_yoy
from app.checkers.lonjakan_harga import aturan_h1, aturan_h2
from app.checkers.orang_dalam import OrangDalam, aturan_o1
from app.checkers.suspensi import aturan_s1
from app.checkers.valuasi import aturan_v1
from app.data.normal import AliranAsing, HargaHarian, KomposisiBulanan, Kuartal, Suspensi, TransaksiOrangDalam
from app.modul import free_float as ff
from app.modul.komoditas import aturan_k1, aturan_k2, komoditas_disebut

HARI = date(2026, 9, 30)


def harga_seri(closes, mulai=date(2026, 1, 1)):
    return [HargaHarian(mulai + timedelta(days=i), c) for i, c in enumerate(closes)]


# ---------- pembaca angka ----------
def test_angka_dari_teks_grup():
    assert angka_rupiah("dari 600 udah 14 ribuan") == [600, 14000]
    assert angka_rupiah("harga 14.650") == [14650]
    assert angka_persen("laba naik 200%") == 2.0
    assert rp(14650) == "Rp14.650"


# ---------- L ----------
def test_laba_yoy_dan_periode():
    k = [Kuartal(f"Q{i}", v) for i, v in enumerate([100, 120, 110, 90, 80])]
    assert round(pertumbuhan_yoy(k), 2) == -0.2
    assert arah_tren(k) == -1
    assert aturan_l2(2.0, -1) is True          # klaim naik, tren turun → menyesatkan
    assert aturan_l1(-0.18, -0.20) is True      # dalam toleransi 5 poin
    assert aturan_l1(2.0, -0.20) is False


def test_laba_dari_rugi_tidak_dihitung_persen():
    assert pertumbuhan_yoy([Kuartal(str(i), v) for i, v in enumerate([-5, 1, 2, 3, 10])]) is None


# ---------- V, D ----------
def test_valuasi_toleransi_15_persen():
    assert aturan_v1(10, 11) is True
    assert aturan_v1(5, 11) is False


def test_dividen():
    assert aturan_d1(0.09, 0.05) is True and aturan_d1(0.06, 0.05) is False
    assert aturan_d1_periode(0.25, 0.20) is True     # beda 5 poin → periode lain
    assert aturan_d2(1.14) is True and aturan_d2(0.6) is False and aturan_d2(None) is False


# ---------- O ----------
def test_orang_dalam_jendela_dan_batas():
    t = [TransaksiOrangDalam(HARI - timedelta(days=30), "A", "jual", 5e9, 0.78, 0.63),
         TransaksiOrangDalam(HARI - timedelta(days=30), "B", "beli", 5e8, None, None),   # < Rp1 M
         TransaksiOrangDalam(HARI - timedelta(days=400), "C", "jual", 9e9, None, None)]  # > 12 bulan
    assert [x.nama for x in aturan_o1(t, HARI)] == ["A"]
    assert aturan_o1([], HARI) == []  # tidak ada transaksi = aman


def test_orang_dalam_tidak_menggabungkan_pemegang_berbeda(monkeypatch):
    from app.data import normal
    transaksi = [TransaksiOrangDalam(HARI - timedelta(days=10), "Nextier", "jual", 2e9, 0.70, 0.6271),
                 TransaksiOrangDalam(HARI - timedelta(days=100), "Pemegang lain", "jual", 3e9, 0.04, 0.0),
                 TransaksiOrangDalam(HARI - timedelta(days=40), "Nextier", "jual", 3e9, 0.7874, 0.70)]
    monkeypatch.setattr(normal, "transaksi_orang_dalam", lambda t: transaksi)
    kartu = OrangDalam().run("MGLV", None, HARI).card
    assert [e.value for e in kartu.evidence if e.label.startswith("Nextier:")] == [0.7874, 0.6271]
    assert [e.value for e in kartu.evidence if e.label.startswith("Pemegang lain:")] == [0.04, 0.0]
    assert kartu.sources[0].as_of == str(HARI - timedelta(days=10))


# ---------- A ----------
def test_asing_borong():
    masuk = [AliranAsing(HARI - timedelta(days=i), 1e9 if i % 3 else -5e8) for i in range(20)]
    borong, total, porsi = aturan_a1(masuk)
    assert borong and total > 0 and porsi >= 0.6
    keluar = [AliranAsing(HARI - timedelta(days=i), -1e9) for i in range(20)]
    assert aturan_a1(keluar)[0] is False


def test_asing_tren_bulanan_memakai_enam_bulan_terakhir():
    import pytest
    rows = [KomposisiBulanan(date(2026, i, 1), 0.8 - i / 100, i / 100, None) for i in range(1, 9)]
    asing, ritel = aturan_a2(list(reversed(rows)))
    assert asing == pytest.approx(-0.05)
    assert ritel == pytest.approx(0.05)
    assert aturan_a2(rows[-3:])[0] == pytest.approx(-0.02)


def test_asing_tren_bulanan_tidak_mengarang_data():
    import pytest
    from app.data.sectors import DataUnavailable
    rows = [KomposisiBulanan(date(2026, i, 1), 0.4, 0.2, None) for i in range(1, 4)]
    assert aturan_a2(rows) == (0, 0)
    for kurang in ([], rows[:2], [rows[0]] * 3):
        with pytest.raises(DataUnavailable):
            aturan_a2(kurang)


def test_asing_konflik_hanya_tanpa_periode():
    assert aturan_a3(1, -0.05, False)
    assert aturan_a3(-1, 0.05, False)
    assert not aturan_a3(1, -0.05, True)
    assert not aturan_a3(1, 0.05, False)
    assert not aturan_a3(0, -0.05, False)
    assert not aturan_a3(1, 0, False)


def test_asing_ambang_satu_poin_persen_dan_batas_float():
    for perubahan in (0, 0.009, -0.009, 0.009999, -0.009999):
        assert arah_a2(perubahan) == 0
        assert not aturan_a3(1, perubahan, False)
        assert not aturan_a3(-1, perubahan, False)
    for perubahan in (0.01, 0.011, 0.3 - 0.29):
        assert arah_a2(perubahan) == 1
        assert aturan_a3(-1, perubahan, False)
    for perubahan in (-0.01, -0.011, 0.29 - 0.3):
        assert arah_a2(perubahan) == -1
        assert aturan_a3(1, perubahan, False)


def test_asing_bulan_hilang_tidak_dianggap_periode_lengkap():
    import pytest
    from app.data.sectors import DataUnavailable
    rows = [KomposisiBulanan(date(2026, i, 1), 0.4, 0.2, None) for i in (1, 3, 4)]
    with pytest.raises(DataUnavailable, match="tidak lengkap"):
        aturan_a2(rows)


# ---------- H ----------
def test_lonjakan_terdeteksi():
    h = harga_seri([100] * 10 + [100 * 1.02 ** i for i in range(1, 22)])
    hasil = aturan_h1(h, set())
    assert hasil is not None and hasil[1] > 0.25


def test_lonjakan_abaikan_ex_dividen():
    # ADRO −25% karena ex-dividen tidak boleh dihitung sebagai lonjakan
    h = harga_seri([100] * 15 + [70] * 15)
    assert aturan_h1(h, set()) is not None
    assert aturan_h1(h, {h[15].tanggal}) is None


def test_klaim_dari_ke():
    assert aturan_h2(600, 14000, harga_jendela=[600, 378, 14650], terakhir=14650) is True
    assert aturan_h2(600, 20000, harga_jendela=[600, 378, 14650], terakhir=14650) is False
    assert not aturan_h2(600, 20000, [600, 20000, 14650], 14650)  # Harga akhir lama tidak menggantikan yang terbaru.


def test_klaim_harga_awal_harus_pernah_tercatat():
    assert not aturan_h2(600, 14000, [378, 700, 14650], 14650)
    assert not aturan_h2(600, 14000, [], 14650)
    assert not aturan_h2(0, 14000, [0, 14650], 14650)
    assert not aturan_h2(600, 0, [600, 14650], 0)


def test_klaim_harga_toleransi_di_kedua_ujung():
    for awal in (540, 660):
        for akhir in (12600, 15400):
            assert aturan_h2(600, 14000, [378, awal, akhir], akhir)
    assert not aturan_h2(600, 14000, [539, 14650], 14650)
    assert not aturan_h2(600, 14000, [661, 14650], 14650)
    assert not aturan_h2(600, 14000, [600, 12599], 12599)
    assert not aturan_h2(600, 14000, [600, 15401], 15401)


def test_keputusan_b3_final_tanpa_mengubah_ambang():
    from app.catalog import rule
    for id_aturan, nama, nilai in (("L-1", "toleransi_poin_persen", 5),
                                  ("H-2", "toleransi_relatif", 0.10),
                                  ("K-1", "batas_porsi_pendapatan", 0.50)):
        assert rule(id_aturan)["status"] == "final"
        assert rule(id_aturan)["params"][nama] == nilai
    import json
    from app.config import settings
    contoh = json.loads((settings.contract_dir / "examples" / "cek_res_mglv.json").read_text(encoding="utf-8"))
    kartu = next(c for c in contoh["claims"] if c["rule_id"] == "H-2")
    assert kartu["rule_text"] == rule("H-2")["text"]


# ---------- S, F ----------
def test_suspensi_36_bulan():
    s = [Suspensi(HARI - timedelta(days=100), "peningkatan harga kumulatif"),
         Suspensi(HARI - timedelta(days=1200), "lama")]
    assert len(aturan_s1(s, HARI)) == 1


def test_free_float():
    assert aturan_f1(0.11) and not aturan_f1(0.2)


# ---------- R (radar) ----------
def test_radar_kelompok_dan_tenggat():
    assert ff.kelompok(8e12, 0.10) == ("kap_besar_ff_rendah", 0.125, "2027-03-31")
    assert ff.kelompok(8e12, 0.13) == ("kap_besar_ff_menengah", 0.15, "2027-03-31")
    assert ff.kelompok(1e12, 0.05) == ("kap_kecil", 0.15, "2029-03-31")


def test_radar_hari_serap_dan_tekanan():
    item = ff.hitung("XXXX", None, ff=0.10, market_cap=8e12, rata_transaksi=1e9)
    assert item.nilai_dilepas == (0.125 - 0.10) * 8e12
    assert round(item.hari_serap) == 200 and item.tekanan == "berat"
    assert ff.tekanan(10) == "ringan" and ff.tekanan(40) == "sedang"
    assert ff.label_hari(100_000) == "> 1.000 hari"
    assert ff.hitung("X", None, 0.1, 8e12, None).hari_serap is None


# ---------- K ----------
def test_komoditas():
    assert komoditas_disebut("MDKA saham emas") == "emas"
    assert komoditas_disebut("ADRO batu bara") == "batubara"
    assert aturan_k1(0.12) is True and aturan_k1(0.82) is False
    assert aturan_k2(0.11) == "lemah" and aturan_k2(0.46) == "sedang" and aturan_k2(0.63) == "cukup kuat"


def test_n1_semua_berbeda_dari_mayoritas():
    from app.checkers.analis import aturan_n1
    assert not aturan_n1(68 / 70, True)
    assert aturan_n1(68 / 70, False)
    assert aturan_n1(1, True)
    assert aturan_n1(0.9, False)
    assert not aturan_n1(0.899, False)


def test_p1_kedua_indikator_dan_ambang():
    from app.checkers.pemegang import aturan_p1
    assert aturan_p1(0.01, 100) == "sesuai"
    assert aturan_p1(0.009, 100) == "menyesatkan"
    assert aturan_p1(0.02, -100) == "menyesatkan"
    assert aturan_p1(0, 0) == "tidak_sesuai"
    assert aturan_p1(-0.01, -100) == "tidak_sesuai"


def test_q1_batas_dan_observasi_lengkap():
    import pytest
    from app.untold.providers import aturan_q1
    from app.data.sectors import DataUnavailable
    assert aturan_q1([1e9] * 60) == (False, 1e9)
    assert aturan_q1([5e8] * 60) == (True, 5e8)
    with pytest.raises(DataUnavailable):
        aturan_q1([5e8] * 59)


def test_c1_batas_jendela_kalender():
    from app.untold.providers import aturan_c1
    assert aturan_c1(HARI, HARI)
    assert aturan_c1(HARI + timedelta(days=90), HARI)
    assert not aturan_c1(HARI + timedelta(days=91), HARI)
    assert not aturan_c1(HARI - timedelta(days=1), HARI)


def test_radar_cocok_dengan_csv_lab_data():
    """Hari serap hitungan R-1 harus sama dengan hasil skrip lab data (cekdulu-datacheck)."""
    import pytest
    from app.data import bahan
    try:
        rows = bahan.baca("radar_free_float")
    except Exception:
        pytest.skip("bahan_produk belum disalin")
    cek = 0
    for r in rows:
        if r["hari_serap"] and r["rata2_nilai_transaksi_60h"]:
            it = ff.hitung(r["symbol"], None, float(r["free_float"]), float(r["market_cap"]),
                           float(r["rata2_nilai_transaksi_60h"]))
            assert it.target == float(r["target_pertama"]), r["symbol"]
            assert abs(it.hari_serap - float(r["hari_serap"])) < 0.01 * float(r["hari_serap"]) + 0.01, r["symbol"]
            cek += 1
    assert cek >= 50
