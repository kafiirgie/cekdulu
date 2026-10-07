"""Tes pengaman AI. Tidak ada tes yang memanggil network atau API sungguhan."""
from __future__ import annotations

import base64
import json

import pytest

from app.ai import gemini, guard
from app.ai import provider
from app.ai.gemini import GeminiLLM
from app.ai.grounding import jawaban_berdasarkan_kartu
from app.schemas import Card, Claim, Evidence, KlaimResponse, Source


class LLMPalsu:
    def extract_claims(self, text, image_base64, ticker):
        return KlaimResponse(
            ticker="HALU",
            claims=[
                Claim(id="buatan-ai", text="BBRI asing net buy", span=(99, 123),
                      checks=["asing", "cek_rekaan"]),
                Claim(id="x", text="klaim yang tidak ada", checks=["laba"]),
                Claim(id="y", text="besok pasti ARA", checks=["lonjakan_harga"]),
            ],
        )

    def answer(self, card, question):
        return "tidak dipakai"


class LLMError:
    def extract_claims(self, text, image_base64, ticker):
        raise TimeoutError("lebih dari 8 detik")

    def answer(self, card, question):
        raise TimeoutError


def test_span_dihitung_ulang_dan_hasil_ai_disaring(monkeypatch):
    teks = "BBRI asing net buy, besok pasti ARA"
    monkeypatch.setattr(provider, "get_llm", lambda: LLMPalsu())

    hasil = provider.extract_with_fallback(teks, None, None)

    assert hasil.ticker == "BBRI"  # ticker halusinasi diganti dari teks asli
    assert hasil.used_ai is True
    assert [c.id for c in hasil.claims] == ["c1", "c2"]
    assert hasil.claims[0].span == (0, 18)
    assert hasil.claims[0].checks == ["asing"]  # ID rekaan dibuang
    assert hasil.claims[1].checks == []  # prediksi tidak boleh memilih pemeriksa
    assert all("tidak ada" not in c.text for c in hasil.claims)


def test_error_llm_kembali_ke_fallback(monkeypatch):
    monkeypatch.setattr(provider, "get_llm", lambda: LLMError())
    hasil = provider.extract_with_fallback(
        "MDKA saham emas, pasti ikut naik", None, None,
    )
    assert hasil.ticker == "MDKA"
    assert hasil.used_ai is False
    assert any(c.checks == ["m_komoditas"] for c in hasil.claims)
    assert any(c.checks == [] and "pasti" in c.text for c in hasil.claims)


def test_ticker_input_dipertahankan_tanpa_teks(monkeypatch):
    monkeypatch.setattr(provider, "get_llm", lambda: LLMPalsu())
    hasil = provider.extract_with_fallback(None, None, "bbri")
    assert hasil.ticker == "BBRI" and hasil.claims == []
    assert hasil.used_ai is False


def test_gemini_meminta_json_terstruktur_tanpa_network(monkeypatch):
    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            isi = {"source_text": "MDKA saham emas", "ticker": "MDKA", "claims": [
                {"text": "MDKA saham emas", "checks": ["m_komoditas"]},
            ]}
            return {"candidates": [{"content": {"parts": [{"text": json.dumps(isi)}]}}]}

    panggilan = {}

    def post_palsu(url, **kwargs):
        panggilan.update({"url": url, **kwargs})
        return ResponsePalsu()

    monkeypatch.setattr("app.ai.gemini.httpx.post", post_palsu)
    hasil = GeminiLLM("key-palsu", "model-palsu").extract_claims(
        "MDKA saham emas", None, None,
    )

    assert hasil.ticker == "MDKA"
    assert hasil.claims[0].checks == ["m_komoditas"]
    assert panggilan["timeout"] is gemini.BATAS_WAKTU
    config = panggilan["json"]["generationConfig"]
    assert config["responseMimeType"] == "application/json"
    assert "responseJsonSchema" in config


def test_gemini_screenshot_satu_request_dan_span_dari_ocr(monkeypatch):
    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            isi = {
                "source_text": "MGLV dari 600 udah 14 ribuan, buruan!",
                "ticker": "MGLV",
                "claims": [
                    {"text": "dari 600 udah 14 ribuan", "checks": ["lonjakan_harga"]},
                    {"text": "teks halusinasi", "checks": ["laba"]},
                ],
            }
            return {"candidates": [{"content": {"parts": [{"text": json.dumps(isi)}]}}]}

    panggilan = []

    def post_palsu(url, **kwargs):
        panggilan.append({"url": url, **kwargs})
        return ResponsePalsu()

    monkeypatch.setattr("app.ai.gemini.httpx.post", post_palsu)
    jpeg = base64.b64encode(b"\xff\xd8\xffgambar-palsu").decode()
    hasil = GeminiLLM("key-palsu", "model-palsu").extract_claims(None, jpeg, None)

    assert len(panggilan) == 1
    parts = panggilan[0]["json"]["contents"][0]["parts"]
    assert parts[1] == {"inlineData": {"mimeType": "image/jpeg", "data": jpeg}}
    assert hasil.ticker == "MGLV"
    assert [c.text for c in hasil.claims] == ["dari 600 udah 14 ribuan"]
    assert hasil.claims[0].span == (5, 28)


def test_screenshot_tidak_memanggil_llm_sebelum_kontrak_source_text(monkeypatch):
    class JanganDipanggil:
        def extract_claims(self, text, image_base64, ticker):
            raise AssertionError("LLM tidak boleh dipanggil sebelum kontrak siap")

    monkeypatch.setattr(provider, "get_llm", lambda: JanganDipanggil())
    hasil = provider.extract_with_fallback(None, "base64-belum-divalidasi", None)

    assert hasil.used_ai is False
    assert hasil.claims == []


KARTU = Card(
    claim_id="c1",
    verdict="menyesatkan",
    check="m_komoditas",
    headline="Pendapatan emas bukan yang utama",
    reason="Proyek nikel menyumbang 82% pendapatan pada 2024.",
    rule_id="K-1",
    rule_text="Menyesatkan jika porsinya di bawah 50%.",
    evidence=[
        Evidence(label="Porsi nikel", value=0.82, fmt="pct"),
        Evidence(label="Korelasi", value=0.25, fmt="num"),
        Evidence(label="Nilai transaksi", value=9.35e12, fmt="rp"),
    ],
    sources=[Source(name="Sectors · get-segments", as_of="2024-12-31")],
)


@pytest.mark.parametrize("jawaban", [
    "Porsi pendapatan nikel yang tercantum adalah 82% pada 2024.",
    "Korelasinya tercatat 0,25.",
    "Nilai transaksi di kartu adalah Rp9,35 T.",
    "Sumber kartu bertanggal 31 Desember 2024.",
    "data ini tidak ada di kartu",
])
def test_lima_jawaban_wajar_tidak_mengarang_angka(monkeypatch, jawaban):
    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": jawaban}]}}]}

    monkeypatch.setattr("app.ai.gemini.httpx.post", lambda *args, **kwargs: ResponsePalsu())
    hasil = GeminiLLM("key-palsu", "model-palsu").answer(KARTU, "Jelaskan kartu ini")
    assert hasil == jawaban
    assert jawaban_berdasarkan_kartu(KARTU, hasil)


@pytest.mark.parametrize("pertanyaan", [
    "Layak beli sekarang?",
    "Target harga berapa?",
    "Mending hold atau jual?",
    "Harus masuk hari ini?",
    "Rekomendasikan saham ini dong",
])
def test_lima_pertanyaan_saran_ditolak_sebelum_llm(pertanyaan):
    assert guard.minta_saran(pertanyaan)


def test_jawaban_dengan_angka_asing_ditolak(monkeypatch):
    class ResponsePalsu:
        def raise_for_status(self):
            return None

        def json(self):
            return {"candidates": [{"content": {"parts": [{
                "text": "Porsi pendapatannya 99%.",
            }]}}]}

    monkeypatch.setattr("app.ai.gemini.httpx.post", lambda *args, **kwargs: ResponsePalsu())
    with pytest.raises(ValueError, match="angka"):
        GeminiLLM("key-palsu", "model-palsu").answer(KARTU, "Berapa porsinya?")
