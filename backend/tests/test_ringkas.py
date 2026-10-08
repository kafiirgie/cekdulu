"""'Artinya apa?': AI hanya menulis ulang; kode membuang tulisan yang menambah atau membalik fakta."""
import pytest
from fastapi.testclient import TestClient

from app import main
from app.ai import ringkas as r
from app.ai.provider import NoLLM
from app.config import Settings
from app.schemas import Card, CekResponse, Evidence

KARTU = Card(claim_id="c1", verdict="menyesatkan", check="m_komoditas",
             headline="Pendapatan MDKA paling banyak dari nikel (82%), sedangkan dari emas hanya 0%.",
             reason="Harga saham dan harga emas dunia punya hubungan sedang; hubungan ini bukan sebab-akibat.",
             evidence=[Evidence(label="Porsi pendapatan murni emas", value=0.0, fmt="pct"),
                       Evidence(label="Sumber terbesar: nikel", value=0.82, fmt="pct")])
PREDIKSI = Card(claim_id="c2", verdict="tidak_bisa_dicek", headline='"pasti ikut naik" tidak bisa kami cek ke data.',
                reason="Ini prediksi.")
ASING = Card(verdict="tidak_sesuai", check="asing",
             headline="Justru sebaliknya: dalam 20 hari bursa terakhir asing keluar bersih Rp224,1 miliar.",
             reason="Porsi kepemilikan asing turun selama 6 bulan.",
             evidence=[Evidence(label="Aliran bersih asing 20 hari bursa", value=-224.1e9, fmt="rp")])
CEK = CekResponse(id="cek_uji", ticker="MDKA", summary="s", steps=[], claims=[KARTU, PREDIKSI], untold=[ASING], form=[])
BAHAN = r.fakta("c1", KARTU)


def test_fakta_memakai_format_indonesia():
    assert BAHAN["angka"] == ["Porsi pendapatan murni emas: 0%", "Sumber terbesar: nikel: 82%"]
    assert r.fakta("u0", ASING)["angka"] == ["Aliran bersih asing 20 hari bursa: minus Rp224,1 miliar"]


@pytest.mark.parametrize("teks", [
    "Sebagian besar pendapatan MDKA datang dari nikel, bukan emas.",
    "MDKA lebih banyak hidup dari nikel (82%) daripada emas.",
])
def test_tulisan_yang_setia_pada_kartu_lolos(teks):
    assert r.periksa(teks, BAHAN, "menyesatkan", "MDKA")


@pytest.mark.parametrize("teks,alasan", [
    ("Sekitar 90% pendapatan MDKA datang dari nikel, bukan emas.", "angka baru"),
    ("Pendapatan MDKA dari emas sedang naik, jadi wajar ikut emas.", "arah yang tidak ada di kartu"),
    ("Klaim ini tidak sesuai karena MDKA dominan nikel, bukan emas.", "vonis lain"),
    ("Pendapatan MDKA dari nikel, jadi sebaiknya kamu tunggu dulu.", "saran"),
    ("Mirip ANTM, pendapatan MDKA lebih banyak dari nikel daripada emas.", "kode saham lain"),
    ("Nikel.", "terlalu pendek"),
    ("Pendapatan MDKA dari nikel. " * 20, "terlalu panjang"),
])
def test_tulisan_yang_menambah_atau_membalik_fakta_dibuang(teks, alasan):
    assert not r.periksa(teks, BAHAN, "menyesatkan", "MDKA"), alasan


def test_kata_yang_dipakai_kartu_sendiri_boleh():
    teks = "Dalam 20 hari terakhir asing lebih banyak keluar, dan porsinya juga turun."
    assert r.periksa(teks, r.fakta("u0", ASING), "tidak_sesuai", "MDKA")


def test_angka_asli_di_luar_judul_tetap_dibuang():
    """Angka penjelasan (6 bulan) memang ada di kartu, tapi AI bisa merangkainya jadi fakta salah."""
    teks = "Asing lebih banyak keluar, dan porsinya turun selama 6 bulan."
    assert not r.periksa(teks, r.fakta("u0", ASING), "tidak_sesuai", "MDKA")


def test_rapikan_membuang_label_dan_judul_yang_disalin():
    judul = KARTU.headline
    assert r.rapikan(f"Artinya apa?: {judul} Jadi MDKA lebih dekat ke nikel.", judul) == "Jadi MDKA lebih dekat ke nikel."
    assert r.rapikan("Artinya apa? Jadi MDKA lebih dekat ke nikel.", judul) == "Jadi MDKA lebih dekat ke nikel."
    assert r.rapikan("Jadi MDKA lebih dekat ke nikel.", judul) == "Jadi MDKA lebih dekat ke nikel."


class LlmPalsu:
    def __init__(self, items):
        self.items, self.prompt = items, None

    def minta_json(self, prompt, schema):
        self.prompt = prompt
        return {"items": self.items}


def test_ringkas_hanya_kartu_klaim_dan_tulisan_yang_lolos():
    llm = LlmPalsu([
        {"kunci": "c1", "teks": "MDKA bukan saham emas, karena pendapatan emasnya 90%."},  # angka baru: dibuang
        {"kunci": "c1", "teks": "Sebagian besar pendapatan MDKA datang dari nikel, bukan emas."},
        {"kunci": "c2", "teks": "Prediksi tidak bisa dicek dengan data apa pun ya."},  # kartu prediksi tidak dikirim
        {"kunci": "u0", "teks": "Asing lebih banyak keluar dari saham ini akhir-akhir ini."},  # bukan kartu klaim
    ])
    hasil = r.ringkas(CEK, llm)
    assert hasil.used_ai and [(i.kunci, i.teks) for i in hasil.items] == [
        ("c1", "Sebagian besar pendapatan MDKA datang dari nikel, bukan emas.")]
    assert '"c1"' in llm.prompt and '"c2"' not in llm.prompt and '"u0"' not in llm.prompt


def test_jawaban_ai_yang_rusak_dilewati_bukan_galat():
    llm = LlmPalsu(["bukan objek", {"kunci": "c1", "teks": 42}, {"kunci": "c1"}, None])
    assert r.ringkas(CEK, llm).items == []


@pytest.mark.parametrize("llm", [NoLLM(), type("Rusak", (), {"minta_json": lambda self, p, s: 1 / 0})()])
def test_ringkas_tanpa_ai_atau_ai_gagal_kosong(llm):
    hasil = r.ringkas(CEK, llm)
    assert hasil.items == [] and not hasil.used_ai


@pytest.fixture
def client_fixture(monkeypatch):
    monkeypatch.setattr(main, "settings", Settings(data_mode="fixture"))
    main._CEK.clear()
    main._RINGKAS.clear()
    return TestClient(main.app)


@pytest.mark.parametrize("used_ai,jumlah_panggilan", [(True, 1), (False, 2)])
def test_endpoint_menyimpan_hasil_ai_tapi_tidak_galatnya(client_fixture, monkeypatch, used_ai, jumlah_panggilan):
    panggilan = []
    monkeypatch.setattr(main, "ringkas_kartu",
                        lambda cek: panggilan.append(cek.id) or r.RingkasResponse(items=[], used_ai=used_ai))
    assert client_fixture.post("/api/ringkas", json={"cek_id": "cek_uji"}).status_code == 404
    main._CEK["cek_uji"] = CEK
    for _ in range(2):
        assert client_fixture.post("/api/ringkas", json={"cek_id": "cek_uji"}).json()["used_ai"] is used_ai
    assert len(panggilan) == jumlah_panggilan


def test_dua_permintaan_serentak_hanya_satu_panggilan_ai(client_fixture, monkeypatch):
    import threading
    import time
    panggilan = []

    def lambat(cek):
        panggilan.append(cek.id)
        time.sleep(0.3)
        return r.RingkasResponse(items=[r.RingkasItem(kunci="c1", teks="Teks yang sama untuk keduanya.")], used_ai=True)

    monkeypatch.setattr(main, "ringkas_kartu", lambat)
    main._CEK["cek_uji"] = CEK
    hasil = []
    utas = [threading.Thread(target=lambda: hasil.append(
        client_fixture.post("/api/ringkas", json={"cek_id": "cek_uji"}).json())) for _ in range(2)]
    for u in utas:
        u.start()
    for u in utas:
        u.join()
    assert panggilan == ["cek_uji"] and hasil[0] == hasil[1] and hasil[0]["items"][0]["kunci"] == "c1"


def test_endpoint_mode_mock_hanya_untuk_contoh_mdka(monkeypatch):
    monkeypatch.setattr(main, "settings", Settings(data_mode="mock"))
    c = TestClient(main.app)
    res = c.post("/api/ringkas", json={"cek_id": "cek_contoh_mdka"}).json()
    assert res["used_ai"] and res["items"][0]["kunci"] == "c1"
    assert c.post("/api/ringkas", json={"cek_id": "cek_contoh_mglv"}).json() == {"items": [], "used_ai": False}
