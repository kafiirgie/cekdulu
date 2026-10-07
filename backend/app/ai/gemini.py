"""Penyedia Gemini untuk ekstraksi klaim. Vonis dan angka tetap diputuskan kode."""
from __future__ import annotations

import json
from typing import Optional

import httpx

from ..catalog import catalog
from ..schemas import Card, Claim, KlaimResponse

# Batas per fase dibuat berjumlah 8 detik agar connect + read tidak masing-masing
# menunggu 8 detik. Jika salah satu fase gagal, provider.py memakai NoLLM.
BATAS_WAKTU = httpx.Timeout(connect=2.0, read=5.0, write=1.0, pool=1.0)
URL_API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiLLM:
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("LLM_API_KEY belum diisi")
        if not model:
            raise ValueError("LLM_MODEL belum diisi")
        self.api_key = api_key
        self.model = model

    @staticmethod
    def _katalog() -> tuple[list[str], str]:
        semua = catalog()["checks"] + catalog()["untold"]
        ids = [item["id"] for item in semua]
        label = ", ".join(f'{item["id"]} = {item["label"]}' for item in semua)
        return ids, label

    @classmethod
    def _payload(cls, text: str, ticker: Optional[str]) -> dict:
        ids, label = cls._katalog()
        petunjuk_ticker = (
            f"Ticker dari pengguna adalah {ticker.upper()}."
            if ticker else
            "Ambil ticker 4 huruf kapital yang benar-benar tertulis di pesan."
        )
        prompt = f"""
Kamu memecah pesan saham Indonesia menjadi klaim, bukan memeriksa kebenarannya.
{petunjuk_ticker}

Aturan wajib:
- `text` harus substring persis dari pesan, tanpa parafrasa atau tambahan.
- Pilih maksimal dua `checks` dari katalog ini: {label}.
- Prediksi, opini, dan rumor tanpa fakta terukur memakai `checks: []`, walaupun
  menyebut komoditas. Contoh: "pasti ikut naik" dan "bakal ARA".
- `pemegang` berarti komposisi pemegang seperti ritel/pengendali. `likuiditas`
  hanya berarti kemudahan transaksi, nilai, atau volume perdagangan.
- Jika ada beberapa ticker, pilih ticker pertama dan hanya ambil klaim tentang
  ticker tersebut.
- Jangan menentukan vonis, menghitung angka, memilih data, atau memberi saran.

Pesan:
{text}
""".strip()
        klaim_schema = {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "checks": {
                    "type": "array",
                    "items": {"type": "string", "enum": ids},
                    "maxItems": 2,
                },
            },
            "required": ["text", "checks"],
        }
        schema = {
            "type": "object",
            "properties": {
                "ticker": {"type": ["string", "null"]},
                "claims": {"type": "array", "items": klaim_schema},
            },
            "required": ["ticker", "claims"],
        }
        return {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 1024,
                "responseMimeType": "application/json",
                "responseJsonSchema": schema,
            },
        }

    @staticmethod
    def _teks_response(data: dict) -> str:
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("Gemini tidak mengembalikan JSON klaim") from exc

    def extract_claims(self, text: Optional[str], image_base64: Optional[str],
                       ticker: Optional[str]) -> KlaimResponse:
        if image_base64:
            raise NotImplementedError("OCR screenshot dikerjakan di C2")
        if not text:
            return KlaimResponse(ticker=ticker.upper() if ticker else None, claims=[], used_ai=False)

        response = httpx.post(
            URL_API.format(model=self.model),
            headers={"x-goog-api-key": self.api_key},
            json=self._payload(text, ticker),
            timeout=BATAS_WAKTU,
        )
        response.raise_for_status()
        mentah = json.loads(self._teks_response(response.json()))
        claims = [
            Claim(id=f"c{i + 1}", text=item["text"], checks=item.get("checks", []))
            for i, item in enumerate(mentah.get("claims", []))
        ]
        return KlaimResponse(ticker=mentah.get("ticker"), claims=claims, used_ai=True)

    def answer(self, card: Card, question: str) -> str:
        raise NotImplementedError("Tanya dengan Gemini dikerjakan di C3")
