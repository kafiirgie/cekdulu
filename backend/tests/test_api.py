"""Tes ujung-ke-ujung endpoint. Mesin dites dengan data buatan (monkeypatch app.data.normal),
jadi tidak butuh fixture maupun kredit Sectors."""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app import main
from app.ai.fallback import pecah_klaim
from app.ai.provider import NoLLM
from app.config import Settings
from app.data import normal
from app.engine import run_cek
from app.schemas import CekRequest, Claim

HARI = date(2026, 9, 30)


@pytest.fixture
def data_palsu(monkeypatch):
    """MGLV versi mini: harga naik dari 600 ke 14.650, 2 suspensi, pengendali menjual."""
    harga = [normal.HargaHarian(HARI - timedelta(days=60 - i), 600 * (14650 / 600) ** (i / 59)) for i in range(60)]
    monkeypatch.setattr(normal, "harga_harian", lambda t: harga)
    monkeypatch.setattr(normal, "tanggal_aksi_korporasi", lambda t: set())
    monkeypatch.setattr(normal, "riwayat_suspensi", lambda t: [
        normal.Suspensi(HARI - timedelta(days=20), "peningkatan harga kumulatif yang signifikan"),
        normal.Suspensi(HARI - timedelta(days=50), "peningkatan harga kumulatif yang signifikan")])
    monkeypatch.setattr(normal, "transaksi_orang_dalam", lambda t: [
        normal.TransaksiOrangDalam(HARI - timedelta(days=40), "Pengendali", "jual", 5e11, 0.7874, 0.6271)])
    monkeypatch.setattr(normal, "free_float", lambda t: 0.30)
    # laba, valuasi, dividen, asing dibiarkan TODO → harus jadi data_kurang, bukan crash


def test_engine_mglv(data_palsu):
    t = "MGLV masih bakal terbang, dari 600 udah 14 ribuan, buruan!"
    k = pecah_klaim(t)
    assert k.ticker == "MGLV"
    res = run_cek(CekRequest(ticker="MGLV", claims=k.claims), today=HARI)

    vonis = {c.claim_id: c.verdict for c in res.claims}
    teks = {c.id: c.text for c in k.claims}
    assert any(v == "tidak_bisa_dicek" and "terbang" in teks[i] for i, v in vonis.items())
    assert any(v == "sesuai" and "600" in teks[i] for i, v in vonis.items())

    status = {f.check: f.status for f in res.form}
    assert status["suspensi"] == "temuan" and status["orang_dalam"] == "temuan"
    assert status["laba"] == "data_kurang"          # parser belum ada → bukan gagal
    assert status["free_float"] == "aman"
    assert [f.check for f in res.form][:8] == ["laba", "valuasi", "dividen", "orang_dalam", "asing",
                                               "lonjakan_harga", "suspensi", "free_float"]
    assert {c.check for c in res.untold} >= {"suspensi", "orang_dalam"}
    assert "Dari" in res.summary


def test_pemeriksa_gagal_tidak_menjatuhkan_cek(data_palsu, monkeypatch):
    monkeypatch.setattr(normal, "free_float", lambda t: 1 / 0)
    res = run_cek(CekRequest(ticker="MGLV", claims=[]), today=HARI)
    assert {f.check: f.status for f in res.form}["free_float"] == "gagal"


def test_cek_umum_tanpa_klaim(data_palsu):
    res = run_cek(CekRequest(ticker="MGLV"), today=HARI)
    assert res.claims == [] and len(res.form) >= 8


def test_fallback_klaim_mdka():
    k = pecah_klaim("Kata grup, MDKA saham emas, emas lagi naik pasti ikut naik")
    assert k.ticker == "MDKA"
    assert any("m_komoditas" in c.checks for c in k.claims)
    assert any(c.checks == [] and "pasti" in c.text for c in k.claims)


@pytest.fixture
def client_mock(monkeypatch):
    monkeypatch.setattr(main, "settings", Settings(data_mode="mock"))
    monkeypatch.setattr(main, "get_llm", lambda: NoLLM())
    main.quota._pakai.clear()
    return TestClient(main.app)


def test_api_mock_alur_lengkap(client_mock):
    c = client_mock
    assert c.get("/api/health").json()["mode"] == "mock"
    k = c.post("/api/klaim", json={"text": "MGLV masih bakal terbang"}).json()
    assert k["ticker"] == "MGLV"
    r = c.post("/api/cek", json={"ticker": "MGLV", "claims": k["claims"]}, headers={"X-Device-Id": "d1"})
    assert r.status_code == 200
    cek = r.json()
    assert cek["quota"]["used"] == 1
    tolak = c.post("/api/tanya", json={"cek_id": cek["id"], "card": "c2", "question": "layak beli nggak?"}).json()
    assert tolak["refused"] is True
    jawab = c.post("/api/tanya", json={"cek_id": cek["id"], "card": "c2", "question": "angka ini dari mana?"}).json()
    assert jawab["refused"] is False and "Sectors" in jawab["answer"]
    assert c.get("/api/modul/free-float").status_code == 200


def test_api_kuota_habis(client_mock):
    for _ in range(5):
        assert client_mock.post("/api/cek", json={"ticker": "MDKA"}, headers={"X-Device-Id": "d2"}).status_code == 200
    r = client_mock.post("/api/cek", json={"ticker": "MDKA"}, headers={"X-Device-Id": "d2"})
    assert r.status_code == 429 and r.json()["detail"]["code"] == "kuota_habis"


def test_api_klaim_kosong_ditolak(client_mock):
    assert client_mock.post("/api/klaim", json={}).status_code == 422


def test_api_screenshot_base64_rusak_ditolak(client_mock):
    r = client_mock.post("/api/klaim", json={"image_base64": "bukan-base64"})
    assert r.status_code == 422
    assert r.json()["detail"] == "Screenshot bukan base64 yang valid."


def test_api_screenshot_lebih_dari_4mb_ditolak(client_mock):
    terlalu_besar = "A" * (4 * ((main.BATAS_GAMBAR + 2) // 3) + 1)
    r = client_mock.post("/api/klaim", json={"image_base64": terlalu_besar})
    assert r.status_code == 413
    assert r.json()["detail"] == "Ukuran screenshot maksimal 4 MB."


def test_tanya_hasil_lama_memberi_pesan_ramah(client_mock):
    r = client_mock.post("/api/tanya", json={
        "cek_id": "cek_yang_hilang",
        "card": "c1",
        "question": "Angkanya dari mana?",
    })
    assert r.status_code == 404
    assert "server mungkin restart" in r.json()["detail"]


def test_tanya_jatuh_ke_nollm_saat_jawaban_ai_ditolak(client_mock, monkeypatch):
    class LLMDitolak:
        def answer(self, card, question):
            raise ValueError("angka asing")

    cek = client_mock.post(
        "/api/cek",
        json={"ticker": "MDKA"},
        headers={"X-Device-Id": "tanya-fallback"},
    ).json()
    monkeypatch.setattr(main, "get_llm", lambda: LLMDitolak())
    r = client_mock.post("/api/tanya", json={
        "cek_id": cek["id"],
        "card": "u0",
        "question": "Jelaskan angka di kartu ini",
    })
    assert r.status_code == 200
    assert r.json()["refused"] is False
    assert "Angka di kartu ini" in r.json()["answer"]
