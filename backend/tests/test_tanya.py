"""Tes panel Tanya (JEV + penyusun jawaban) dan penyedia OpenAI-compatible. TANPA jaringan.

Pola sama seperti tests/test_ai.py: httpx.post diganti palsu, jadi tidak ada tes yang
memanggil API sungguhan (AGENTS.md aturan 10).
"""
from __future__ import annotations

import json

import pytest

from app.ai import fallback, jev, provider, tanya
from app.ai.openai_compat import MIN_TOKEN, OpenAICompatLLM
from app.catalog import glosarium
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
    assert panggilan["json"]["max_tokens"] == MIN_TOKEN
    assert MIN_TOKEN >= 4096  # model nalar: jatah 1024/2048 kosong
    assert hasil.ticker == "MDKA" and hasil.claims[0].checks == ["m_komoditas"]
    assert hasil.claims[0].span == (0, 15)  # "MDKA saham emas"


def test_openai_compat_tidak_menebak_tanpa_teks():
    hasil = OpenAICompatLLM("https://ollama.com/v1", "key", "m").extract_claims(None, None, "bbri")
    assert hasil.ticker == "BBRI" and hasil.claims == [] and hasil.used_ai is False


# ---------- JEV sebagai pengaman kedua saat memecah klaim (prediksi tanpa angka) ----------

class JevPrediksi:
    """Klien JEV palsu: .saring() mengembalikan prediksi sesuai peta skor."""

    def __init__(self, skor: dict[str, float]):
        self._skor = skor
        self.dipanggil = 0

    def saring(self, kalimat):
        self.dipanggil += 1
        return {
            "klaim_saham": {"type": "noul", "noul": 0.9},
            "prediksi": {"type": "noul", "noul": self._skor.get(kalimat, 0.0)},
            "target_harga": {"type": "noul", "noul": 0.0},
        }


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


def test_klien_saring_memuat_pertanyaan_prediksi_tanpa_kartu(monkeypatch):
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
    hasil = jev.Jev("https://api.typesafe.ai/v1", "k", "jev-latest").saring("besok pasti ARA")

    body = panggilan["json"]
    assert set(body["questions"]) == {jev.KUNCI_KLAIM, jev.KUNCI_PREDIKSI, jev.KUNCI_TARGET}
    assert body["questions"][jev.KUNCI_PREDIKSI]["type"] == "noul"
    assert json.loads(body["state"]) == {"kalimat": "besok pasti ARA"}
    assert hasil[jev.KUNCI_PREDIKSI]["noul"] == 0.8


def test_saring_jev_ambang_dan_default_aman():
    """Satu panggilan -> tiga keputusan; JEV mati/jawaban aneh -> default aman."""
    assert jev.saring_jev(JevPrediksi({"x": jev.AMBANG_PREDIKSI}), "x")["prediksi"] is True
    assert jev.saring_jev(JevPrediksi({"x": jev.AMBANG_PREDIKSI - 0.01}), "x")["prediksi"] is False
    assert jev.saring_jev(JevKlaim({"x": jev.AMBANG_KLAIM - 0.01}), "x")["klaim"] is False
    assert jev.saring_jev(JevTarget(jev.AMBANG_TARGET), "x")["target"] is True

    class Rusak:
        def saring(self, kalimat):
            raise TimeoutError

    class Aneh:
        def saring(self, kalimat):
            return {}

    for klien in (Rusak(), Aneh()):
        d = jev.saring_jev(klien, "x")
        assert d == {"klaim": True, "prediksi": False, "target": False}  # default aman


def test_satu_panggilan_jev_untuk_satu_kalimat(monkeypatch):
    """Penghematan: satu kalimat -> SATU request JEV berisi tiga pertanyaan."""
    panggilan = []

    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            return {"answers": {"klaim_saham": {"choice": None, "noul": 0.9},
                                "prediksi": {"noul": 0.0}, "target_harga": {"noul": 0.0}}}

    monkeypatch.setattr("app.ai.jev.httpx.post",
                        lambda url, **k: panggilan.append(k["json"]) or ResponsePalsu())
    kalimat = "MGLV dari 600 udah 14 ribuan"

    jev.Jev("https://api.typesafe.ai/v1", "k", "jev-latest").saring(kalimat)
    assert len(panggilan) == 1, "harus satu request, bukan tiga"
    assert set(panggilan[0]["questions"]) == {"klaim_saham", "prediksi", "target_harga"}


def test_normalisasi_hanya_satu_panggilan_jev_per_klaim(monkeypatch):
    """Bukti hemat: tiga klaim -> tiga request (dulu sampai sembilan)."""
    hitung = {"n": 0}

    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            hitung["n"] += 1
            return {"answers": {"klaim_saham": {"noul": 0.9}, "prediksi": {"noul": 0.0},
                                "target_harga": {"noul": 0.0}}}

    monkeypatch.setattr("app.ai.jev.httpx.post", lambda url, **k: ResponsePalsu())
    kalimat = "laba BBRI naik 20% tahun ini"
    klien_jev = jev.Jev("https://api.typesafe.ai/v1", "k", "jev-latest")
    monkeypatch.setattr(provider, "_get_jev_prediksi", lambda: klien_jev)
    provider._normalisasi(
        KlaimResponse(ticker="BBRI", claims=[Claim(id="c1", text=kalimat, checks=["laba"])]),
        kalimat, None, used_ai=True, dari_gambar=False)
    assert hitung["n"] == 1


# ---------- JEV menyaring kalimat yang BUKAN klaim saham (sapaan/pertanyaan/ngobrol) ----------

class JevKlaim:
    """Klien JEV palsu: .saring() mengembalikan skor klaim sesuai peta."""

    def __init__(self, skor: dict[str, float]):
        self._skor = skor
        self.dipanggil = 0

    def saring(self, kalimat):
        self.dipanggil += 1
        return {
            "klaim_saham": {"type": "noul", "noul": self._skor.get(kalimat, 1.0)},
            "prediksi": {"type": "noul", "noul": 0.0},
            "target_harga": {"type": "noul", "noul": 0.0},
        }


def test_jev_membuang_ngobrol_yang_lolos_heuristik(monkeypatch):
    """Heuristik lolos ("MGLV gimana nih masih bagus gak"); JEV membuangnya."""
    kalimat = "MGLV gimana nih masih bagus gak"
    assert not fallback.bukan_klaim(kalimat)
    jev_palsu = JevKlaim({kalimat: 0.21})
    monkeypatch.setattr(provider, "_get_jev_prediksi", lambda: jev_palsu)

    res = provider._normalisasi(
        KlaimResponse(ticker="MGLV", claims=[Claim(id="c1", text=kalimat, checks=[])]),
        kalimat, None, used_ai=True, dari_gambar=False)

    assert res.claims == []
    assert jev_palsu.dipanggil == 1


def test_jev_mempertahankan_klaim_asli(monkeypatch):
    """Kalimat klaim berangka tetap lolos dan pemeriksanya utuh."""
    kalimat = "laba BBRI naik 20% tahun ini"
    monkeypatch.setattr(provider, "_get_jev_prediksi", lambda: JevKlaim({kalimat: 0.98}))

    res = provider._normalisasi(
        KlaimResponse(ticker="BBRI", claims=[Claim(id="c1", text=kalimat, checks=["laba"])]),
        kalimat, None, used_ai=True, dari_gambar=False)

    assert [c.text for c in res.claims] == [kalimat]
    assert res.claims[0].checks == ["laba"]


def test_jev_mati_mempertahankan_klaim(monkeypatch):
    """JEV error saat menyaring -> klaim DIPERTAHANKAN (jangan sampai klaim asli hilang)."""
    monkeypatch.setattr(provider, "get_jev", lambda: (_ for _ in ()).throw(RuntimeError("matii")))
    kalimat = "laba BBRI naik 20% tahun ini"
    res = provider._normalisasi(
        KlaimResponse(ticker="BBRI", claims=[Claim(id="c1", text=kalimat, checks=["laba"])]),
        kalimat, None, used_ai=False, dari_gambar=False)
    assert [c.text for c in res.claims] == [kalimat]
    assert provider._get_jev_prediksi() is None


def test_klaim_jev_ambang_dan_default_aman():
    """Ambang klaim lewat saring_jev; jawaban aneh -> klaim DIPERTAHANKAN."""
    class Aneh:
        def saring(self, kalimat):
            return {}

    assert jev.saring_jev(Aneh(), "apapun")["klaim"] is True  # tak bisa dinilai -> pertahankan
    assert jev.saring_jev(JevKlaim({"x": jev.AMBANG_KLAIM}), "x")["klaim"] is True
    assert jev.saring_jev(JevKlaim({"x": jev.AMBANG_KLAIM - 0.01}), "x")["klaim"] is False


def test_heuristik_bukan_klaim_tanpa_jev():
    """Tanpa JEV pun, sapaan/pertanyaan jelas tidak jadi klaim."""
    assert fallback.bukan_klaim("makasih infonya bro")
    assert fallback.bukan_klaim("kapan ya bagi dividennya?")
    assert fallback.bukan_klaim("oke siap bos")
    assert not fallback.bukan_klaim("MGLV dari 600 udah 14 ribuan")
    assert not fallback.bukan_klaim("laba BBRI naik 20% tahun ini")


def test_klien_saring_memuat_pertanyaan_klaim_tanpa_kartu(monkeypatch):
    panggilan = {}

    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            return {"answers": {jev.KUNCI_KLAIM: {"type": "noul", "noul": 0.9}}}

    def post_palsu(url, **kwargs):
        panggilan.update({"url": url, **kwargs})
        return ResponsePalsu()

    monkeypatch.setattr("app.ai.jev.httpx.post", post_palsu)
    hasil = jev.Jev("https://api.typesafe.ai/v1", "k", "jev-latest").saring("halo semua")

    body = panggilan["json"]
    assert set(body["questions"]) == {jev.KUNCI_KLAIM, jev.KUNCI_PREDIKSI, jev.KUNCI_TARGET}
    assert body["questions"][jev.KUNCI_KLAIM]["type"] == "noul"
    assert json.loads(body["state"]) == {"kalimat": "halo semua"}
    assert hasil[jev.KUNCI_KLAIM]["noul"] == 0.9


# ---------- pemisah ribuan Indonesia tidak boleh memecah kalimat ----------

def test_pemisah_ribuan_tidak_memecah_kalimat():
    """"naik ke 20.000" adalah satu klaim; titik ribuan bukan akhir kalimat."""
    k = fallback.pecah_klaim("besok naik ke 20.000")
    assert [c.text for c in k.claims] == ["besok naik ke 20.000"]
    # titik yang memang akhir kalimat tetap memotong
    k2 = fallback.pecah_klaim("harga 14.650. besok naik")
    assert [c.text for c in k2.claims] == ["harga 14.650", "besok naik"]


# ---------- JEV mematikan vonis untuk target/prediksi harga (aturan T-1) ----------

class JevTarget:
    """Klien JEV palsu: .saring() mengembalikan skor target tetap."""

    def __init__(self, skor_target: float):
        self._skor = skor_target
        self.dipanggil = 0

    def saring(self, kalimat):
        self.dipanggil += 1
        return {
            "klaim_saham": {"type": "noul", "noul": 0.9},
            "prediksi": {"type": "noul", "noul": 0.0},
            "target_harga": {"type": "noul", "noul": self._skor},
        }


def test_jev_mematikan_vonis_target_berangka(monkeypatch):
    """LLM menempelkan lonjakan_harga ke "besok naik ke 20.000"; JEV mematikannya (T-1)."""
    kalimat = "besok naik ke 20.000"
    jev_palsu = JevTarget(0.97)
    monkeypatch.setattr(provider, "_get_jev_prediksi", lambda: jev_palsu)

    res = provider._normalisasi(
        KlaimResponse(ticker="MGLV", claims=[Claim(id="c1", text=kalimat, checks=["lonjakan_harga"])]),
        kalimat, None, used_ai=True, dari_gambar=False)

    assert res.claims[0].checks == []
    assert jev_palsu.dipanggil == 1


def test_jev_membiarkan_klaim_data_berangka(monkeypatch):
    """Klaim data yang benar ("dari 600 ke 14.650") tetap diperiksa."""
    kalimat = "dari 600 ke 14.650"
    monkeypatch.setattr(provider, "_get_jev_prediksi", lambda: JevTarget(0.07))

    res = provider._normalisasi(
        KlaimResponse(ticker="MGLV", claims=[Claim(id="c1", text=kalimat, checks=["lonjakan_harga"])]),
        kalimat, None, used_ai=True, dari_gambar=False)

    assert res.claims[0].checks == ["lonjakan_harga"]


def test_target_jev_ambang_lewat_saring():
    """Ambang target lewat saring_jev; JEV mati -> target False (vonis normal)."""
    class Rusak:
        def saring(self, kalimat):
            raise TimeoutError

    assert jev.saring_jev(Rusak(), "besok naik")["target"] is False
    assert jev.saring_jev(JevTarget(jev.AMBANG_TARGET), "x")["target"] is True
    assert jev.saring_jev(JevTarget(jev.AMBANG_TARGET - 0.01), "x")["target"] is False


def test_klien_saring_memuat_pertanyaan_target_tanpa_kartu(monkeypatch):
    panggilan = {}

    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            return {"answers": {jev.KUNCI_TARGET: {"type": "noul", "noul": 0.9}}}

    def post_palsu(url, **kwargs):
        panggilan.update({"url": url, **kwargs})
        return ResponsePalsu()

    monkeypatch.setattr("app.ai.jev.httpx.post", post_palsu)
    jev.Jev("https://api.typesafe.ai/v1", "k", "jev-latest").saring("besok naik ke 20.000")
    body = panggilan["json"]
    assert set(body["questions"]) == {jev.KUNCI_KLAIM, jev.KUNCI_PREDIKSI, jev.KUNCI_TARGET}
    assert json.loads(body["state"]) == {"kalimat": "besok naik ke 20.000"}


# ---------- regresi PR #34: kalimat fakta tanpa angka BUKAN prediksi ----------

def test_pertanyaan_prediksi_tidak_menangkap_fakta_tanpa_angka(monkeypatch):
    """Rumusan lama ("TANPA angka") membuang pemeriksa dari fakta tanpa angka.

    Nyata: "MDKA saham emas" dinilai prediksi 0,82 sehingga pemeriksa nikel hilang dan
    demo utama rusak. Rumusan baru harus menanyakan ramalan MURNI, dan menyebut keadaan
    sekarang/lampau sebagai alasan menjawab "tidak".
    """
    panggilan = {}

    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            return {"answers": {"prediksi": {"type": "noul", "noul": 0.1}}}

    monkeypatch.setattr("app.ai.jev.httpx.post",
                        lambda url, **k: panggilan.update(k["json"]) or ResponsePalsu())
    jev.Jev("https://api.typesafe.ai/v1", "k", "jev-latest").saring("MDKA saham emas")

    instr = panggilan["questions"][jev.KUNCI_PREDIKSI]["instructions"]
    assert "MURNI ramalan" in instr or "murni ramalan" in instr.lower()
    assert "keadaan sekarang" in instr and "lewat" in instr
    # rumusan lama yang menyesatkan tidak boleh kembali
    assert "TANPA angka" not in instr


def test_fakta_tanpa_angka_menyimpan_pemeriksa(monkeypatch):
    """Ujung-ke-ujung: JEV bilang "bukan prediksi" -> pemeriksa tetap ada (demo MDKA)."""
    class JevFakta:
        def saring(self, kalimat):
            return {"klaim_saham": {"noul": 0.9}, "prediksi": {"noul": 0.12},
                    "target_harga": {"noul": 0.05}}

    monkeypatch.setattr(provider, "_get_jev_prediksi", lambda: JevFakta())
    kalimat = "MDKA saham emas"
    res = provider._normalisasi(
        KlaimResponse(ticker="MDKA", claims=[Claim(id="c1", text=kalimat, checks=["komoditas"])]),
        kalimat, None, used_ai=True, dari_gambar=False)
    assert res.claims[0].checks == ["komoditas"], "fakta tanpa angka tetap diperiksa"


def test_ramalan_murni_tetap_dimatikan(monkeypatch):
    """Perbaikan tidak boleh melonggarkan sisi lain: ramalan tetap kehilangan vonis."""
    class JevRamalan:
        def saring(self, kalimat):
            return {"klaim_saham": {"noul": 0.9}, "prediksi": {"noul": 0.88},
                    "target_harga": {"noul": 0.1}}

    monkeypatch.setattr(provider, "_get_jev_prediksi", lambda: JevRamalan())
    kalimat = "MGLV masih bakal terbang"
    res = provider._normalisasi(
        KlaimResponse(ticker="MGLV", claims=[Claim(id="c1", text=kalimat, checks=["lonjakan_harga"])]),
        kalimat, None, used_ai=True, dari_gambar=False)
    assert res.claims[0].checks == []


# ---------- tes pembunuh mutant: bentuk permintaan ke JEV ----------
# Mutasi pada teks/kunci payload tidak mengubah perilaku di jalur palsu, jadi hanya
# tes yang mengunci BENTUK permintaan yang bisa membunuhnya. Ini bagian dari kontrak
# integrasi dengan JEV (nama kunci, tipe pertanyaan), bukan detail implementasi.

def _tangkap(monkeypatch, answers=None):
    """Rekam body yang dikirim ke /systemone; kembalikan (daftar_body, klien)."""
    bodies = []

    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            return {"answers": answers or {}}

    monkeypatch.setattr("app.ai.jev.httpx.post",
                        lambda url, **k: bodies.append(k["json"]) or ResponsePalsu())
    return bodies, jev.Jev("https://api.typesafe.ai/v1", "k", "jev-latest")


def test_payload_saring_terkunci(monkeypatch):
    """saring(): state apa adanya, tiga pertanyaan noul, kriteria true/false berisi."""
    bodies, klien = _tangkap(monkeypatch)
    klien.saring("MDKA saham emas")

    body = bodies[0]
    assert body["state"] == '{"kalimat": "MDKA saham emas"}'
    assert body["model"] == "jev-latest"
    assert set(body["questions"]) == {jev.KUNCI_KLAIM, jev.KUNCI_PREDIKSI, jev.KUNCI_TARGET}
    for nama, isi in body["questions"].items():
        assert isi["type"] == "noul", nama
        assert set(isi["criteria"]) == {"true", "false"}, nama
        assert isi["criteria"]["true"].strip() and isi["criteria"]["false"].strip()
        assert isi["instructions"].strip()


def test_payload_saring_pertanyaan_prediksi_terkunci(monkeypatch):
    """Rumusan prediksi harus menanyakan ramalan MURNI (regresi PR #34)."""
    bodies, klien = _tangkap(monkeypatch)
    klien.saring("apa saja")
    instr = bodies[0]["questions"][jev.KUNCI_PREDIKSI]["instructions"]
    assert "murni ramalan" in instr.lower()
    assert "keadaan sekarang" in instr and "lewat" in instr
    assert "TANPA angka" not in instr


def test_payload_saran_terkunci(monkeypatch):
    bodies, klien = _tangkap(monkeypatch, answers={jev.KUNCI_SARAN: {"noul": 0.9}})
    klien.saran("masih bagus buat dibeli?")
    assert bodies[0]["state"] == '{"pertanyaan": "masih bagus buat dibeli?"}'
    assert set(bodies[0]["questions"]) == {jev.KUNCI_SARAN}
    assert bodies[0]["questions"][jev.KUNCI_SARAN]["type"] == "noul"


def test_payload_klasifikasi_terkunci(monkeypatch):
    """klasifikasi(): tiga pertanyaan, label persis, criteria dari kartu."""
    bodies, klien = _tangkap(monkeypatch)
    klien.klasifikasi(KARTU, "berapa angkanya?")
    body = bodies[0]
    assert set(body["questions"]) == {jev.KUNCI_BAGIAN, jev.KUNCI_ISTILAH, jev.KUNCI_TAHU}
    q = body["questions"]
    assert q[jev.KUNCI_BAGIAN]["type"] == "choice"
    assert q[jev.KUNCI_ISTILAH]["type"] == "choice"
    assert q[jev.KUNCI_TAHU]["type"] == "noul"
    assert set(q[jev.KUNCI_BAGIAN]["criteria"]) == set(jev.aturan_bagian(KARTU))
    # state memuat isi kartu, bukan kosong
    isi = json.loads(body["state"])
    assert isi["headline"] == KARTU.headline and isi["pertanyaan"] == "berapa angkanya?"


def test_aturan_bagian_kunci_dan_isi():
    peta = jev.aturan_bagian(KARTU)
    assert set(peta) == {"angka_bukti", "alasan_aturan", "sumber_tanggal", "istilah", "di_luar_kartu"}
    assert all(v.strip() for v in peta.values())
    assert "angka" in peta["angka_bukti"].lower()
    assert "sumber" in peta["sumber_tanggal"].lower() or "data" in peta["sumber_tanggal"].lower()


def test_state_memuat_field_kartu():
    isi = json.loads(jev.state(KARTU, "berapa porsi nikelnya?"))
    assert isi["headline"] == KARTU.headline
    assert isi["verdict"] == KARTU.verdict
    assert isi["rule_id"] == KARTU.rule_id
    assert isi["rule_text"] == KARTU.rule_text
    assert len(isi["evidence"]) == len(KARTU.evidence)
    assert len(isi["sources"]) == len(KARTU.sources)


def test_ambang_jev_tepat_di_batas(monkeypatch):
    """Ambang inklusif (>=) untuk ketiga label, dan jawaban aneh -> default aman."""
    answers = {jev.KUNCI_KLAIM: {"noul": 0.4}, jev.KUNCI_PREDIKSI: {"noul": 0.5},
               jev.KUNCI_TARGET: {"noul": 0.39}}
    _, klien = _tangkap(monkeypatch, answers)
    assert jev.saring_jev(klien, "x") == {"klaim": True, "prediksi": True, "target": False}

    for aneh in ({jev.KUNCI_KLAIM: {"noul": "0.9"}}, {jev.KUNCI_KLAIM: {"noul": None}},
                 {jev.KUNCI_KLAIM: {}}, {jev.KUNCI_KLAIM: []}):
        _, klien = _tangkap(monkeypatch, aneh)
        assert jev.saring_jev(klien, "x")["klaim"] is True  # tak bisa dinilai -> pertahankan


def test_ambang_saran_batas(monkeypatch):
    for nilai, harus in ((0.5, True), (0.49, False)):
        _, klien = _tangkap(monkeypatch, {jev.KUNCI_SARAN: {"noul": nilai}})
        assert jev.minta_saran_jev(klien, "q") is harus
    _, klien = _tangkap(monkeypatch, {jev.KUNCI_SARAN: {"noul": "tinggi"}})
    assert jev.minta_saran_jev(klien, "q") is False
    _, klien = _tangkap(monkeypatch, {})
    assert jev.minta_saran_jev(klien, "q") is False


def test_pilih_bagian_dan_istilah_menolak_yang_asing():
    assert jev.pilih_bagian({jev.KUNCI_BAGIAN: {"choice": "istilah"}}) == "istilah"
    assert jev.pilih_bagian({jev.KUNCI_BAGIAN: {"choice": "tidak_ada"}}) is None
    assert jev.pilih_bagian({jev.KUNCI_BAGIAN: {}}) is None
    assert jev.pilih_bagian({}) is None

    kunci = sorted(i["key"] for i in glosarium()["istilah"])
    assert kunci, "glosarium tidak boleh kosong"
    assert jev.pilih_istilah({jev.KUNCI_ISTILAH: {"choice": kunci[0]}}) == kunci[0]
    assert jev.pilih_istilah({jev.KUNCI_ISTILAH: {"choice": "bukan_istilah"}}) is None
    assert jev.pilih_istilah({}) is None


def test_rupiah_batas_triliun_dan_miliar():
    assert tanya.rupiah(999_999_999_999) == "Rp1.000 M"
    assert tanya.rupiah(1e12) == "Rp1 T"              # batas inklusif: 1e12 masuk triliun
    assert tanya.rupiah(1_500_000_000_000) == "Rp1,5 T"
    assert tanya.rupiah(1e9) == "Rp1 M"               # batas inklusif: 1e9 masuk miliar
    assert tanya.rupiah(1_250_000_000) == "Rp1,2 M"    # satu desimal
    assert tanya.rupiah(14_650) == "Rp14.650"


def test_nilai_memformat_angka_dengan_benar():
    assert tanya._nilai(Evidence(label="x", value=True, fmt="num")) == "True"   # bool bukan angka
    assert tanya._nilai(Evidence(label="x", value=0.065, fmt="pct")) == "6,5%"
    assert tanya._nilai(Evidence(label="x", value=0.4, fmt="x")) == "0,4×"
    assert tanya._nilai(Evidence(label="x", value=1500, fmt="int")) == "1.500"
    assert tanya._nilai(Evidence(label="x", value=9.35e12, fmt="rp")) == "Rp9,35 T"


# ---------- pembunuh mutant: bentuk payload persis & cabang galat ----------

def test_payload_saring_persis_sama(monkeypatch):
    """Bandingkan SELURUH body dengan bentuk yang diharapkan.

    Mutasi pada nama kunci payload ("instructions" → "INSTRUCTIONS", "state" → "STATE",
    "type" → "TYPE"), pada kwargs json.dumps, dan pada teks kriteria semuanya muncul
    sebagai survivor kalau hanya sebagian yang diuji. Permintaan ke JEV adalah antarmuka
    nyata: salah nama kunci = panggilan rusak.
    """
    bodies, klien = _tangkap(monkeypatch)
    klien.saring("MDKA saham emas")

    assert bodies[0] == {
        "state": '{"kalimat": "MDKA saham emas"}',
        "model": "jev-latest",
        "questions": {
            jev.KUNCI_KLAIM: {
                "type": "noul",
                "instructions": bodies[0]["questions"][jev.KUNCI_KLAIM]["instructions"],
                "criteria": {
                    "true": "Klaim/kabar/pendapat tentang saham yang bisa diperiksa.",
                    "false": "Sapaan, terima kasih, pertanyaan, rencana pribadi, atau ngobrol.",
                },
            },
            jev.KUNCI_PREDIKSI: {
                "type": "noul",
                "instructions": jev.TEKS_PREDIKSI,
                "criteria": jev.KRITERIA_PREDIKSI,
            },
            jev.KUNCI_TARGET: {
                "type": "noul",
                "instructions": bodies[0]["questions"][jev.KUNCI_TARGET]["instructions"],
                "criteria": {
                    "true": "Target harga atau prediksi arah harga ke depan.",
                    "false": "Melaporkan data atau harga yang sudah terjadi.",
                },
            },
        },
    }


def test_payload_saran_persis_sama(monkeypatch):
    bodies, klien = _tangkap(monkeypatch)
    klien.saran("masih bagus buat dibeli?")
    assert bodies[0] == {
        "state": '{"pertanyaan": "masih bagus buat dibeli?"}',
        "model": "jev-latest",
        "questions": {
            jev.KUNCI_SARAN: {
                "type": "noul",
                "instructions": ("Apakah pengguna meminta saran investasi: beli, jual, atau tahan, "
                                 "atau menanyakan target harga?"),
                "criteria": {
                    "true": "Meminta saran investasi atau target harga.",
                    "false": "Hanya menanyakan data, angka, atau arti istilah.",
                },
            },
        },
    }


def test_payload_klasifikasi_persis_sama(monkeypatch):
    bodies, klien = _tangkap(monkeypatch)
    klien.klasifikasi(KARTU, "berapa angkanya?")
    body = bodies[0]
    assert set(body) == {"state", "model", "questions"}
    assert body["model"] == "jev-latest"
    assert body["state"] == jev.state(KARTU, "berapa angkanya?")
    q = body["questions"]
    assert set(q) == {jev.KUNCI_BAGIAN, jev.KUNCI_ISTILAH, jev.KUNCI_TAHU}
    assert q[jev.KUNCI_BAGIAN] == {
        "type": "choice",
        "instructions": "Bagian kartu mana yang menjawab pertanyaan pengguna?",
        "criteria": jev.aturan_bagian(KARTU),
    }
    assert q[jev.KUNCI_ISTILAH] == {
        "type": "choice",
        "instructions": "Istilah mana yang ditanyakan pengguna?",
        "criteria": jev.kriteria_istilah(KARTU),
    }
    assert q[jev.KUNCI_TAHU] == {
        "type": "noul",
        "instructions": "Apakah jawabannya tersedia penuh di field kartu di atas?",
    }


def test_klien_menolak_kredensial_kosong():
    """Jev() menolak base_url/api_key/model kosong, pesan menyebut nama variabelnya."""
    for kosong, nama in ((("", "k", "m"), "JEV_BASE_URL"), (("u", "", "m"), "JEV_API_KEY"),
                         (("u", "k", ""), "JEV_MODEL")):
        with pytest.raises(ValueError) as e:
            jev.Jev(*kosong)
        assert nama in str(e.value), (nama, str(e.value))


def test_klien_menyimpan_dan_membersihkan_konfigurasi():
    j = jev.Jev("https://api.typesafe.ai/v1/", "rahasia", "jev-latest")
    assert j.base_url == "https://api.typesafe.ai/v1"   # garis miring akhir dibuang
    assert j.api_key == "rahasia"
    assert j.model == "jev-latest"


def test_http_error_diteruskan_bukan_ditelan(monkeypatch):
    """raise_for_status() harus dipanggil: galat HTTP tidak boleh jadi jawaban kosong."""
    dipanggil = {"n": 0}

    class ResponseGagal:
        def raise_for_status(self):
            dipanggil["n"] += 1
            raise RuntimeError("503")

        def json(self):
            return {}

    monkeypatch.setattr("app.ai.jev.httpx.post", lambda url, **k: ResponseGagal())
    klien = jev.Jev("https://api.typesafe.ai/v1", "k", "jev-latest")
    for panggil in (klien.saring, klien.saran):
        with pytest.raises(RuntimeError):
            panggil("x")
    assert dipanggil["n"] == 2


def test_state_dan_kriteria_istilah_dari_glosarium():
    """Istilah kartu utama didahulukan; state memuat istilah itu."""
    utama = jev.istilah_card(KARTU)
    assert utama, "KARTU (m_komoditas) harus punya istilah utama"
    krit = jev.kriteria_istilah(KARTU)
    assert list(krit)[0] == utama, "istilah utama harus paling depan"
    assert set(krit) == {i["key"] for i in glosarium()["istilah"]}
    isi = json.loads(jev.state(KARTU, "q"))
    assert isi["istilah"] and isi["istilah"][0]["key"] == utama

    kartu_tanpa = Card(claim_id="c9", verdict="tidak_bisa_dicek", check=None, headline="h",
                       reason="r", rule_id="T-1", rule_text="t", evidence=[], sources=[])
    assert jev.istilah_card(kartu_tanpa) is None
    assert json.loads(jev.state(kartu_tanpa, "q"))["istilah"] == []


def test_pecah_klaim_membuang_ticker_dan_pembuka():
    """Ticker dibuang dari kalimat, dan kalimat sapaan murni tidak jadi klaim."""
    k = fallback.pecah_klaim("Kata grup, MDKA saham emas")
    assert [c.text for c in k.claims] == ["MDKA saham emas"]     # ticker tetap di klaim data
    assert k.ticker == "MDKA"

    kosong = fallback.pecah_klaim("halo semua apa kabar")
    assert kosong.claims == []

    pendek = fallback.pecah_klaim("halo")
    assert pendek.claims == []


def test_pilih_cek_dan_bukan_klaim():
    """Heuristik pemilih pemeriksa: prioritas, kata harga, dan penjaga non-klaim."""
    assert fallback.pilih_cek("laba naik dan dividen gede") == ["laba", "dividen"]  # urutan prioritas
    assert fallback.pilih_cek("ada emas di dalamnya") == ["m_komoditas"]
    assert fallback.pilih_cek("harganya naik") == []          # kata harga tanpa angka -> bukan pemeriksa

    assert fallback.bukan_klaim("halo semua") is True
    assert fallback.bukan_klaim("kapan bagi dividennya?") is True
    assert fallback.bukan_klaim("MDKA saham emas") is False


# ---------- pembunuh mutant: pemilihan provider & jalur tanpa AI ----------

def _settings_provider(monkeypatch, **ubah):
    """Ganti settings provider untuk satu tes (settings adalah objek beku)."""
    from app.config import Settings
    nilai = {"llm_provider": "none", "llm_api_key": "k", "llm_model": "m",
             "llm_base_url": "https://contoh/v1"}
    nilai.update(ubah)
    monkeypatch.setattr(provider, "settings", Settings(**nilai))


def test_get_llm_memilih_kelas_yang_benar(monkeypatch):
    """Setiap nilai LLM_PROVIDER harus memetakan ke kelas yang tepat."""
    for nama in ("", "none", "NONE"):
        _settings_provider(monkeypatch, llm_provider=nama)
        assert isinstance(provider.get_llm(), provider.NoLLM), nama

    for nama in ("openai_compat", "openai", "ollama_cloud", "OLLAMA_CLOUD"):
        _settings_provider(monkeypatch, llm_provider=nama)
        obj = provider.get_llm()
        assert isinstance(obj, OpenAICompatLLM), nama
        assert obj.base_url == "https://contoh/v1" and obj.model == "m"

    _settings_provider(monkeypatch, llm_provider="gemini")
    from app.ai.gemini import GeminiLLM
    assert isinstance(provider.get_llm(), GeminiLLM)


def test_get_llm_menolak_provider_tak_dikenal(monkeypatch):
    _settings_provider(monkeypatch, llm_provider="mistral")
    with pytest.raises(ValueError) as e:
        provider.get_llm()
    assert "mistral" in str(e.value)


def test_nollm_tanpa_teks_dengan_ticker():
    """Ticker saja (cek umum) -> ticker dinormalkan, tanpa klaim, used_ai=False."""
    res = provider.NoLLM().extract_claims(None, None, "bbri")
    assert res.ticker == "BBRI" and res.claims == [] and res.used_ai is False
    # ada teks -> pecah_klaim dipakai, bukan jalur ticker-saja
    res2 = provider.NoLLM().extract_claims("MDKA saham emas", None, "mdka")
    assert res2.claims and res2.claims[0].checks == ["m_komoditas"]


def test_nollm_tidak_menebak_tanpa_teks_dan_tanpa_ticker():
    res = provider.NoLLM().extract_claims(None, None, None)
    assert res.ticker is None and res.claims == []


def test_sanitize_membuang_pemeriksa_karang():
    """AI tidak boleh mengarang pemeriksa: yang tak ada di katalog dibuang."""
    res = KlaimResponse(ticker="MDKA", claims=[
        Claim(id="c1", text="a", checks=["m_komoditas", "karangan"])])
    bersih = provider.sanitize(res)
    assert bersih.claims[0].checks == ["m_komoditas"]


def test_ticker_valid_menolak_empat_huruf_yang_bukan_saham():
    """Empat huruf kapital tidak cukup: harus kata utuh di teks dan cocok polanya."""
    assert provider._ticker_valid("MDKA saham emas", "mdka") == "MDKA"
    assert provider._ticker_valid("saham ini bagus", "MDKA") is None  # tidak ada di teks
    assert provider._ticker_valid("MDKA bagus", "MDKAA") is None      # pola bukan 4 huruf
    assert provider._ticker_valid("", "mdka") == "MDKA"               # tanpa teks: asal polanya benar
    # CATATAN: _ticker_valid TIDAK menyaring kata umum; daftar STOP_TICKER ada di
    # fallback.cari_ticker. "HALO semua" tetap lolos di sini (bug yang tercatat di skill).
    assert provider._ticker_valid("HALO semua", "HALO") == "HALO"


def test_instruksi_dan_kriteria_prediksi_terkunci():
    """Teks yang dipakai JEV dikunci supaya parafrase tak sengaja mengubah perilaku."""
    assert jev.TEKS_PREDIKSI.startswith("Apakah kalimat ini MURNI ramalan")
    assert "keadaan sekarang" in jev.TEKS_PREDIKSI and "lewat" in jev.TEKS_PREDIKSI
    assert jev.KRITERIA_PREDIKSI["true"].startswith("Murni ramalan")


def test_aturan_bagian_teks_terkunci():
    peta = jev.aturan_bagian(KARTU)
    assert peta["angka_bukti"] == "Pertanyaan tentang angka/bukti di kartu."
    assert peta["alasan_aturan"] == "Pertanyaan kenapa begitu, aturan mana yang dipakai."
    assert peta["sumber_tanggal"] == "Pertanyaan dari mana datanya atau tanggalnya."
    assert peta["istilah"] == "Pertanyaan arti istilah/istilah teknis di kartu."
    assert peta["di_luar_kartu"] == "Tidak berkaitan dengan kartu ini."


def test_teks_jawaban_deterministik_terkunci():
    """Kalimat yang disusun kode untuk pengguna; bunyinya bagian dari UX."""
    assert tanya._angka(KARTU) == ("Angka di kartu ini — Porsi nikel: 82%; "
                                   "Nilai transaksi: Rp9,35 T; Korelasi emas: 0,4.")
    assert tanya._tak_ada().startswith("Maaf, data ini tidak ada di kartu.")
    # `or True` di sini dulu membuat assert-nya selalu lolos; sekarang diuji sungguhan.
    glos = {"nama": "Korelasi emas", "arti": "Seberapa erat harga saham mengikuti emas."}
    assert tanya.jawab(KARTU, "istilah", glos) == \
        "Korelasi emas: Seberapa erat harga saham mengikuti emas."
    assert tanya.jawab(KARTU, "istilah") == tanya._tak_ada()   # tanpa glosarium -> jujur
    assert tanya.jawab(KARTU, "tidak_ada") == tanya._tak_ada()


def test_get_jev_none_saat_mode_off_atau_tanpa_kunci(monkeypatch):
    """get_jev() menolak mode off dan kunci kosong -> None, bukan error."""
    import dataclasses
    for tanya_mode, kunci, harus_none in (("off", "kunci", True), ("auto", "", True),
                                          ("auto", "kunci", False)):
        obj = dataclasses.replace(jev.settings, tanya_mode=tanya_mode, jev_api_key=kunci,
                                   jev_base_url="https://api.typesafe.ai/v1", jev_model="jev-latest")
        monkeypatch.setattr(jev, "settings", obj)
        hasil = jev.get_jev()
        assert (hasil is None) is harus_none, (tanya_mode, kunci)
        if hasil is not None:
            assert hasil.model == "jev-latest" and hasil.api_key == "kunci"
