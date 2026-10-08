"""Tes pengaman AI. Tidak ada tes yang memanggil network atau API sungguhan."""
from __future__ import annotations

import base64
import json

import pytest

from app.ai import gemini, guard
from app.ai import provider
from app.ai.gemini import GeminiLLM
from app.schemas import Claim, KlaimResponse


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


class LLMError:
    def extract_claims(self, text, image_base64, ticker):
        raise TimeoutError("lebih dari 8 detik")


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
    assert hasil.source_text == "MGLV dari 600 udah 14 ribuan, buruan!"


TEKS_SCREENSHOT = "MGLV dari 600 udah 14 ribuan, buruan!"


class LLMScreenshot:
    def __init__(self, ticker="MGLV"):
        self.ticker = ticker

    def extract_claims(self, text, image_base64, ticker):
        return KlaimResponse(
            ticker=self.ticker,
            source_text=TEKS_SCREENSHOT,
            claims=[
                Claim(id="a", text="dari 600 udah 14 ribuan", span=(0, 1), checks=["lonjakan_harga"]),
                Claim(id="b", text="teks halusinasi", checks=["laba"]),
            ],
            used_ai=True,
        )


def test_screenshot_disorot_pada_teks_bacaan_ai(monkeypatch):
    monkeypatch.setattr(provider, "get_llm", lambda: LLMScreenshot())
    hasil = provider.extract_with_fallback(None, "gambar-base64", None)

    assert hasil.used_ai is True
    assert hasil.source_text == TEKS_SCREENSHOT
    assert hasil.ticker == "MGLV"
    assert [(c.id, c.text, c.span) for c in hasil.claims] == [("c1", "dari 600 udah 14 ribuan", (5, 28))]


def test_ticker_screenshot_harus_tertulis_di_teks_bacaan(monkeypatch):
    monkeypatch.setattr(provider, "get_llm", lambda: LLMScreenshot(ticker="BBRI"))
    assert provider.extract_with_fallback(None, "gambar-base64", None).ticker == "MGLV"


def test_screenshot_tanpa_ai_tidak_menebak(monkeypatch):
    monkeypatch.setattr(provider, "get_llm", lambda: LLMError())
    hasil = provider.extract_with_fallback(None, "gambar-base64", None)

    assert hasil.used_ai is False
    assert hasil.ticker is None and hasil.claims == [] and hasil.source_text is None


def test_teks_biasa_tanpa_source_text(monkeypatch):
    monkeypatch.setattr(provider, "get_llm", lambda: LLMPalsu())
    assert provider.extract_with_fallback("BBRI asing net buy", None, None).source_text is None


@pytest.mark.parametrize("pertanyaan", [
    "Layak beli sekarang?",
    "Target harga berapa?",
    "Mending hold atau jual?",
    "Harus masuk hari ini?",
    "Rekomendasikan saham ini dong",
])
def test_lima_pertanyaan_saran_ditolak_sebelum_llm(pertanyaan):
    assert guard.minta_saran(pertanyaan)


@pytest.mark.parametrize("pertanyaan", [
    "target harganya berapa?",
    "TP-nya berapa?",
    "beli atau tunggu dulu?",
    "jual aja?",
    "cut loss aja?",
    "average down gak?",
])
def test_variasi_saran_ditolak(pertanyaan):
    assert guard.minta_saran(pertanyaan)


@pytest.mark.parametrize("pertanyaan", [
    "kapan asing masuk?",
    "asing masuk gak minggu ini?",
    "asing beli atau jual?",
    "berapa rekomendasi buy?",
    "kenapa targetnya 15%?",
    "kenapa harus 15%?",
])
def test_pertanyaan_data_tidak_ditolak(pertanyaan):
    assert not guard.minta_saran(pertanyaan)
