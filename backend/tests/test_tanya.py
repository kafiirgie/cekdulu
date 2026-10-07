"""Tes panel Tanya (JEV + penyusun jawaban) dan penyedia OpenAI-compatible. TANPA jaringan.

Pola sama seperti tests/test_ai.py: httpx.post diganti palsu, jadi tidak ada tes yang
memanggil API sungguhan (AGENTS.md aturan 10).
"""
from __future__ import annotations

import json

import pytest

from app.ai import fallback, jev, provider, tanya
from app.ai.openai_compat import OpenAICompatLLM
from app.schemas import Card, Claim, Evidence, KlaimResponse, Source

KARTU = Card(
    claim_id="c1", verdict="menyesatkan", check="m_komoditas",
    headline="Pendapatan emas bukan yang utama",
    reason="Proyek nikel menyumbang 82% pendapatan pada 2024.",
    rule_id="K-1", rule_text="Menyesatkan jika porsinya di bawah 50%.",
    evidence=[Evidence(label="Porsi nikel", value=0.82, fmt="pct"),
              Evidence(label="Nilai transaksi", value=9.35e12, fmt="rp"),
              Evidence(label="Korelasi emas", value=0.4, fmt="num")],
    sources=[Source(name="Sectors · get-segments", as_of="2024-12-31")],
)

KARTU_TANPA_SUMBER = Card(
    claim_id="c2", verdict="tidak_bisa_dicek", check=None,
    headline='"Pasti ikut naik" adalah prediksi. Kami tidak menebak harga.',
    reason="Data hanya bisa menunjukkan hubungan di masa lalu.", rule_id="T-1",
    rule_text="Prediksi, opini, dan rumor tanpa angka diberi vonis Tidak bisa dicek.",
    evidence=[], sources=[],
)


# ---------- penyusun jawaban deterministik ----------

def test_angka_diformat_seperti_layar():
    jawaban = tanya.jawab(KARTU, "angka")
    assert "Porsi nikel: 82%" in jawaban
    assert "Nilai transaksi: Rp9,35 T" in jawaban  # 9,35e12 → "Rp9,35 T"
    assert "Korelasi emas: 0,4" in jawaban


def test_sumber_memakai_tanggal_bahasa_indonesia():
    jawaban = tanya.jawab(KARTU, "sumber")
    assert "31 Des 2024" in jawaban and "Sectors · get-segments" in jawaban


def test_aturan_dan_istilah():
    assert tanya.jawab(KARTU, "aturan").startswith("Aturan K-1:")
    assert tanya.jawab(KARTU, "istilah", {"nama": "Korelasi", "arti": "gerak bersama"}) == \
        "Korelasi: gerak bersama"


def test_kartu_tanpa_angka_menjawab_jujur():
    assert "tidak memuat angka tambahan" in tanya.jawab(KARTU_TANPA_SUMBER, "angka")
    assert "tidak punya sumber" in tanya.jawab(KARTU_TANPA_SUMBER, "sumber")
    assert "tidak ada di kartu" in tanya.jawab(KARTU_TANPA_SUMBER, "istilah")


def test_peta_bagian_menutup_semua_label():
    assert tanya.peta_bagian("angka_bukti") == "angka"
    assert tanya.peta_bagian("alasan_aturan") == "aturan"
    assert tanya.peta_bagian("sumber_tanggal") == "sumber"
    assert tanya.peta_bagian("istilah") == "istilah"
    assert tanya.peta_bagian("di_luar_kartu") == "tidak_ada"
    assert tanya.peta_bagian(None) == "tidak_ada"


# ---------- orkestrasi: JEV memilih, kode merakit ----------

class JevPalsu:
    def __init__(self, bagian="angka_bukti", noul=0.9, istilah="korelasi"):
        self._bagian, self._noul, self._istilah = bagian, noul, istilah

    def klasifikasi(self, card, question):
        return {"bagian": {"type": "choice", "choice": self._bagian, "confidence": 0.9},
                "istilah_key": {"type": "choice", "choice": self._istilah, "confidence": 0.9},
                "tahu": {"type": "noul", "noul": self._noul}}


def test_jev_memilih_sumber_kode_merakit():
    hasil = tanya.jawab_tanya(KARTU, "sumbernya dari mana?", jev=JevPalsu("sumber_tanggal"))
    assert hasil["used_ai"] is True and hasil["bagian"] == "sumber_tanggal"
    assert hasil["answer_kind"] == "sumber" and "31 Des 2024" in hasil["answer"]


def test_di_luar_kartu_menjawab_tidak_ada():
    """`bagian == di_luar_kartu` (penentu utama) → kode menjawab jujur 'tidak ada'."""
    hasil = tanya.jawab_tanya(KARTU, "besok naik?", jev=JevPalsu(bagian="di_luar_kartu"))
    assert hasil["answer_kind"] == "tidak_ada" and "tidak ada di kartu" in hasil["answer"]


def test_noul_hampir_nol_dianggap_rusak():
    """`noul` di bawah lantai sanity → jangan percaya labelnya."""
    hasil = tanya.jawab_tanya(KARTU, "apa isinya?", jev=JevPalsu(bagian="angka_bukti", noul=0.01))
    assert hasil["answer_kind"] == "tidak_ada"


def test_istilah_diambil_dari_glosarium_kontrak():
    hasil = tanya.jawab_tanya(KARTU, "korelasi itu apa?", jev=JevPalsu("istilah", istilah="korelasi"))
    assert hasil["answer_kind"] == "istilah"
    assert hasil["answer"].startswith("Korelasi: ")


def test_jev_gagal_jatuh_ke_ringkasan_kode():
    class JevError:
        def klasifikasi(self, card, question):
            raise TimeoutError("jev lambat")

    hasil = tanya.jawab_tanya(KARTU, "apa isinya?", jev=JevError())
    assert hasil["used_ai"] is False and hasil["answer_kind"] == "ringkasan"
    assert "Angka di kartu ini" in hasil["answer"]


# ---------- pengaman kedua penolakan saran: JEV (regex tetap jalan lebih dulu) ----------

class JevSaran:
    """Klien JEV palsu: .klasifikasi() tetap jalan, .saran() mengembalikan nilai tetap."""

    def __init__(self, noul_saran: float, bagian="angka_bukti"):
        self._noul, self._bagian = noul_saran, bagian
        self.dipanggil = 0

    def saran(self, pertanyaan):
        self.dipanggil += 1
        return {jev.KUNCI_SARAN: {"type": "noul", "noul": self._noul}}

    def klasifikasi(self, card, question):
        return {"bagian": {"type": "choice", "choice": self._bagian, "confidence": 0.9},
                "istilah_key": {"type": "choice", "choice": "korelasi", "confidence": 0.9},
                "tahu": {"type": "noul", "noul": 0.9}}


def test_regex_ditolak_tanpa_panggil_jev():
    """Regex menangkap lebih dulu -> JEV tidak dipanggil sama sekali."""
    jev_palsu = JevSaran(0.0)
    hasil = tanya.jawab_tanya(KARTU, "layak beli nggak?", jev=jev_palsu)
    assert hasil["refused"] is True and hasil["answer_kind"] == "saran"
    assert jev_palsu.dipanggil == 0


def test_jev_menolak_pertanyaan_yang_lolos_regex():
    """Pertanyaan saran yang lolos regex tetap ditolak kalau JEV menilainya minta saran.

    Contoh nyata hasil ukur: "harga wajarnya berapa?" (0,55) dan
    "masih bagus buat dibeli?" (0,90) lolos dari regex tapi ditangkap JEV.
    """
    assert not tanya.guard.minta_saran("masih bagus buat dibeli?")
    hasil = tanya.jawab_tanya(KARTU, "masih bagus buat dibeli?", jev=JevSaran(0.90))
    assert hasil["refused"] is True and hasil["answer_kind"] == "saran"
    assert hasil["answer"] == tanya.guard.PENOLAKAN


def test_jev_tidak_menolak_pertanyaan_data_biasa():
    """noul rendah -> bukan saran -> jawaban normal (JEV hanya menolak, tak mengizinkan)."""
    jev_palsu = JevSaran(0.03)
    hasil = tanya.jawab_tanya(KARTU, "berapa porsi nikelnya?", jev=jev_palsu)
    assert hasil["refused"] is False and hasil["answer_kind"] == "angka"
    assert jev_palsu.dipanggil == 1


def test_jev_mati_tidak_menolak_dan_tidak_menjatuhkan():
    """JEV error pada pengaman saran -> regex saja, tidak 500."""
    class JevRusak:
        def saran(self, pertanyaan):
            raise TimeoutError("jev mati")

        def klasifikasi(self, card, question):
            return {}

    hasil = tanya.jawab_tanya(KARTU, "berapa porsi nikelnya?", jev=JevRusak())
    assert hasil["refused"] is False


def test_batas_ambang_saran():
    """Batas AMBANG_SARAN: 0,5 ditolak; di bawahnya lolos. Nilai tengah (0,2–0,3) bukan saran."""
    assert tanya.jawab_tanya(KARTU, "q", jev=JevSaran(jev.AMBANG_SARAN))["refused"] is True
    assert tanya.jawab_tanya(KARTU, "q", jev=JevSaran(jev.AMBANG_SARAN - 0.01))["refused"] is False
    assert tanya.jawab_tanya(KARTU, "q", jev=JevSaran(0.23))["refused"] is False  # "berapa PER wajar"


def test_klien_saran_sunggal_memuat_satu_pertanyaan_tanpa_kartu(monkeypatch):
    """Jev.saran mengirim satu kunci noul; state = pertanyaan saja (tanpa kartu)."""
    panggilan = {}

    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            return {"answers": {jev.KUNCI_SARAN: {"type": "noul", "noul": 0.9}}}

    def post_palsu(url, **kwargs):
        panggilan.update({"url": url, **kwargs})
        return ResponsePalsu()

    monkeypatch.setattr("app.ai.jev.httpx.post", post_palsu)
    hasil = jev.Jev("https://api.typesafe.ai/v1", "k", "jev-latest").saran("layak beli?")

    assert panggilan["url"].endswith("/systemone")
    body = panggilan["json"]
    assert set(body["questions"]) == {jev.KUNCI_SARAN}
    assert body["questions"][jev.KUNCI_SARAN]["type"] == "noul"
    assert json.loads(body["state"]) == {"pertanyaan": "layak beli?"}
    assert hasil[jev.KUNCI_SARAN]["noul"] == 0.9


# ---------- kunci utama: JEV untuk pemilihan di luar Tanya, dan tak bisa melihat gambar ----------

def test_permintaan_jev_tidak_pernah_memuat_gambar(monkeypatch):
    """JEV tidak menerima gambar: state harus JSON teks, tanpa field biner/base64."""
    panggilan = {}

    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            return {"answers": {"bagian": {"choice": "angka_bukti", "confidence": 0.9},
                                "istilah_key": {"choice": "korelasi"},
                                "tahu": {"noul": 0.9}}}

    def post_palsu(url, **kwargs):
        panggilan.update({"json": kwargs["json"]})
        return ResponsePalsu()

    monkeypatch.setattr("app.ai.jev.httpx.post", post_palsu)
    jev.Jev("https://api.typesafe.ai/v1", "k", "jev-latest").klasifikasi(KARTU, "q")
    assert set(panggilan["json"]) == {"state", "model", "questions"}
    assert isinstance(panggilan["json"]["state"], str)


def test_tiga_tipe_pertanyaan_didukung():
    """JEV hanya punya choice/noul/score; modul memakai choice + noul saja."""
    assert jev.BAGIAN and all(isinstance(x, str) for x in jev.BAGIAN)
    assert 0 < jev.AMBANG_SARAN < 1 and 0 <= jev.AMBANG_SANITY < jev.AMBANG_SARAN


@pytest.mark.parametrize("pertanyaan", ["layak beli?", "target harga berapa?", "mending hold?"])
def test_saran_ditolak_sebelum_jev(pertanyaan):
    hasil = tanya.jawab_tanya(KARTU, pertanyaan, jev=JevPalsu())
    assert hasil["refused"] is True and hasil["answer_kind"] == "saran"


def test_panggilan_jev_memuat_glosarium_dan_state(monkeypatch):
    panggilan = {}

    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            return {"answers": {"bagian": {"choice": "angka_bukti"},
                                "istilah_key": {"choice": "laba"},
                                "tahu": {"noul": 0.8}}}

    def post_palsu(url, **kwargs):
        panggilan.update({"url": url, **kwargs})
        return ResponsePalsu()

    monkeypatch.setattr("app.ai.jev.httpx.post", post_palsu)
    jawaban = jev.Jev("https://api.typesafe.ai/v1", "key-palsu", "jev-latest").klasifikasi(
        KARTU, "angkanya dari mana?")
    assert panggilan["url"].endswith("/systemone")
    body = panggilan["json"]
    assert set(body["questions"]) == {"bagian", "istilah_key", "tahu"}
    assert body["model"] == "jev-latest"
    assert "korelasi" in body["questions"]["istilah_key"]["criteria"]  # opsi dari glosarium
    assert "Pendapatan emas" in body["state"] and "angkanya dari mana?" in body["state"]
    assert jawaban["bagian"]["choice"] == "angka_bukti"


# ---------- penyedia OpenAI-compatible (ollama-cloud) ----------

def test_openai_compat_meminta_json_dan_token_besar(monkeypatch):
    panggilan = {}

    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            isi = {"source_text": "MDKA saham emas",
                   "ticker": "MDKA",
                   "claims": [{"text": "MDKA saham emas", "checks": ["m_komoditas"]}]}
            return {"choices": [{"message": {"role": "assistant",
                                              "content": json.dumps(isi),
                                              "reasoning": "diabaikan"}}]}

    def post_palsu(url, **kwargs):
        panggilan.update({"url": url, **kwargs})
        return ResponsePalsu()

    monkeypatch.setattr("app.ai.openai_compat.httpx.post", post_palsu)
    hasil = OpenAICompatLLM("https://ollama.com/v1", "key-palsu", "deepseek-v4.1-flash").extract_claims(
        "MDKA saham emas", None, None)

    assert panggilan["url"] == "https://ollama.com/v1/chat/completions"
    assert panggilan["json"]["max_tokens"] >= 768  # model nalar: jangan sampai kosong
    assert hasil.ticker == "MDKA" and hasil.claims[0].checks == ["m_komoditas"]
    assert hasil.claims[0].span == (0, 15)  # "MDKA saham emas"


def test_openai_compat_tidak_menebak_tanpa_teks():
    hasil = OpenAICompatLLM("https://ollama.com/v1", "key", "m").extract_claims(None, None, "bbri")
    assert hasil.ticker == "BBRI" and hasil.claims == [] and hasil.used_ai is False


# ---------- JEV sebagai pengaman kedua saat memecah klaim (prediksi tanpa angka) ----------

class JevPrediksi:
    """Klien JEV palsu untuk .prediksi(): peta kalimat -> skor."""

    def __init__(self, skor: dict[str, float]):
        self._skor = skor
        self.dipanggil = 0

    def prediksi(self, kalimat):
        self.dipanggil += 1
        return {jev.KUNCI_PREDIKSI: {"type": "noul", "noul": self._skor.get(kalimat, 0.0)}}


def test_jev_menghapus_pemeriksa_dari_prediksi_yang_lolos_heuristik(monkeypatch):
    """Heuristik melewatkan "momen bagus buat masuk, gaskeun"; JEV menghapus pemeriksanya."""
    kalimat = "momen bagus buat masuk, gaskeun"
    assert not fallback.prediksi_tanpa_angka(kalimat)  # heuristik memang lolos
    jev_palsu = JevPrediksi({kalimat: 0.91})
    monkeypatch.setattr(provider, "_get_jev_prediksi", lambda: jev_palsu)

    res = provider._normalisasi(
        KlaimResponse(ticker="MGLV", claims=[Claim(id="c1", text=kalimat, checks=["lonjakan_harga"])]),
        kalimat, None, used_ai=False, dari_gambar=False)

    assert res.claims[0].checks == []
    assert jev_palsu.dipanggil == 1


def test_jev_tidak_menambah_pemeriksa_dan_menghormati_angka(monkeypatch):
    """JEV hanya boleh MENGHAPUS. Kalimat berangka tetap punya pemeriksanya."""
    kalimat = "laba naik 20% tahun ini"
    jev_palsu = JevPrediksi({kalimat: 0.02})
    monkeypatch.setattr(provider, "_get_jev_prediksi", lambda: jev_palsu)

    res = provider._normalisasi(
        KlaimResponse(ticker="BBRI", claims=[Claim(id="c1", text=kalimat, checks=["laba"])]),
        kalimat, None, used_ai=False, dari_gambar=False)

    assert res.claims[0].checks == ["laba"]


def test_jev_mati_saat_pecah_klaim_pakai_heuristik(monkeypatch):
    """JEV error -> heuristik saja, tidak menjatuhkan /api/klaim."""
    def rusak():
        raise RuntimeError("jev mati")

    monkeypatch.setattr(provider, "get_jev", rusak)
    kalimat = "besok pasti ARA"
    res = provider._normalisasi(
        KlaimResponse(ticker="MGLV", claims=[Claim(id="c1", text=kalimat, checks=["lonjakan_harga"])]),
        kalimat, None, used_ai=False, dari_gambar=False)
    assert res.claims[0].checks == []  # heuristik tetap menghapusnya
    assert provider._get_jev_prediksi() is None


def test_tanpa_jev_hasil_sama_seperti_sebelumnya(monkeypatch):
    """Mode kode (tanpa kunci): perilaku identik dengan sebelum ada pengaman JEV."""
    monkeypatch.setattr(provider, "_get_jev_prediksi", lambda: None)
    teks = "MGLV masih bakal terbang, dari 600 udah 14 ribuan"
    hasil = provider.extract_with_fallback(teks, None, None)
    checks = {c.text: c.checks for c in hasil.claims}
    assert checks["MGLV masih bakal terbang"] == []
    assert checks["dari 600 udah 14 ribuan"] == ["lonjakan_harga"]


def test_klien_prediksi_memuat_satu_noul_tanpa_kartu(monkeypatch):
    panggilan = {}

    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            return {"answers": {jev.KUNCI_PREDIKSI: {"type": "noul", "noul": 0.8}}}

    def post_palsu(url, **kwargs):
        panggilan.update({"url": url, **kwargs})
        return ResponsePalsu()

    monkeypatch.setattr("app.ai.jev.httpx.post", post_palsu)
    hasil = jev.Jev("https://api.typesafe.ai/v1", "k", "jev-latest").prediksi("besok pasti ARA")

    body = panggilan["json"]
    assert set(body["questions"]) == {jev.KUNCI_PREDIKSI}
    assert body["questions"][jev.KUNCI_PREDIKSI]["type"] == "noul"
    assert json.loads(body["state"]) == {"kalimat": "besok pasti ARA"}
    assert hasil[jev.KUNCI_PREDIKSI]["noul"] == 0.8


def test_prediksi_jev_ambang_dan_nilai_rusak():
    assert jev.prediksi_jev(JevPrediksi({"x": jev.AMBANG_PREDIKSI}), "x") is True
    assert jev.prediksi_jev(JevPrediksi({"x": jev.AMBANG_PREDIKSI - 0.01}), "x") is False

    class Rusak:
        def prediksi(self, kalimat):
            raise TimeoutError

    assert jev.prediksi_jev(Rusak(), "x") is False
