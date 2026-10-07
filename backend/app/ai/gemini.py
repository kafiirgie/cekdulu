"""Penyedia Gemini untuk ekstraksi klaim. Vonis dan angka tetap diputuskan kode."""
from __future__ import annotations

import base64
import binascii
import json
import re
from typing import Optional

import httpx

from ..catalog import catalog
from ..schemas import Card, Claim, KlaimResponse
from .grounding import jawaban_berdasarkan_kartu

# Model gratis saat ini menjawab dalam 10–14 detik, jadi read diberi 20 detik; write 10 detik
# untuk unggahan screenshot sampai 4 MB. Turunkan lagi kalau modelnya lebih cepat.
# Jika salah satu fase gagal, provider.py memakai NoLLM.
BATAS_WAKTU = httpx.Timeout(connect=3.0, read=20.0, write=10.0, pool=1.0)
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
    def _payload(cls, text: Optional[str], image_base64: Optional[str],
                 ticker: Optional[str]) -> dict:
        ids, label = cls._katalog()
        petunjuk_ticker = (
            f"Ticker dari pengguna adalah {ticker.upper()}."
            if ticker else
            "Ambil ticker 4 huruf kapital yang benar-benar tertulis di source_text."
        )
        petunjuk_sumber = (
            "Salin pesan saham yang terlihat pada screenshot ke `source_text` secara "
            "verbatim. Abaikan nama pengirim, jam, tombol, dan elemen antarmuka."
            if image_base64 else
            "Isi `source_text` dengan Pesan di bawah ini secara persis."
        )
        prompt = f"""
Kamu memecah pesan saham Indonesia menjadi klaim, bukan memeriksa kebenarannya.
{petunjuk_ticker}
{petunjuk_sumber}

Aturan wajib:
- Setiap `claims[].text` harus substring persis dari `source_text`, tanpa
  parafrasa atau tambahan.
- Pilih maksimal dua `checks` dari katalog ini: {label}.
- Prediksi, opini, dan rumor tanpa fakta terukur memakai `checks: []`, walaupun
  menyebut komoditas. Contoh: "pasti ikut naik" dan "bakal ARA".
- `pemegang` berarti komposisi pemegang seperti ritel/pengendali. `likuiditas`
  hanya berarti kemudahan transaksi, nilai, atau volume perdagangan.
- Jika ada beberapa ticker, pilih ticker pertama dan hanya ambil klaim tentang
  ticker tersebut.
- Jangan menentukan vonis, menghitung angka, memilih data, atau memberi saran.

Pesan:
{text or "(baca dari screenshot)"}
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
                "source_text": {"type": "string"},
                "ticker": {"type": ["string", "null"]},
                "claims": {"type": "array", "items": klaim_schema},
            },
            "required": ["source_text", "ticker", "claims"],
        }
        parts = [{"text": prompt}]
        if image_base64:
            parts.append({
                "inlineData": {
                    "mimeType": cls._mime_gambar(image_base64),
                    "data": image_base64,
                },
            })
        return {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 1024,
                "responseMimeType": "application/json",
                "responseJsonSchema": schema,
            },
        }

    @staticmethod
    def _mime_gambar(image_base64: str) -> str:
        """Kenali format dari magic bytes; request tidak membawa nama file."""
        try:
            awal = base64.b64decode(image_base64[:32], validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("Screenshot bukan base64 yang valid") from exc
        if awal.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if awal.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if awal.startswith(b"RIFF") and awal[8:12] == b"WEBP":
            return "image/webp"
        raise ValueError("Format screenshot harus JPEG, PNG, atau WebP")

    @staticmethod
    def _teks_response(data: dict) -> str:
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("Gemini tidak mengembalikan JSON klaim") from exc

    def extract_claims(self, text: Optional[str], image_base64: Optional[str],
                       ticker: Optional[str]) -> KlaimResponse:
        if not text and not image_base64:
            return KlaimResponse(ticker=ticker.upper() if ticker else None, claims=[], used_ai=False)

        response = httpx.post(
            URL_API.format(model=self.model),
            headers={"x-goog-api-key": self.api_key},
            json=self._payload(text, image_base64, ticker),
            timeout=BATAS_WAKTU,
        )
        response.raise_for_status()
        mentah = json.loads(self._teks_response(response.json()))
        source_text = mentah.get("source_text")
        if not isinstance(source_text, str) or not source_text.strip():
            raise ValueError("Gemini tidak mengembalikan source_text")

        claims = []
        for item in mentah.get("claims", []):
            claim_text = item.get("text")
            if not isinstance(claim_text, str):
                continue
            awal = source_text.find(claim_text)
            if awal < 0:
                continue
            claims.append(Claim(
                id=f"c{len(claims) + 1}",
                text=claim_text,
                span=(awal, awal + len(claim_text)),
                checks=item.get("checks", []),
            ))
        return KlaimResponse(ticker=mentah.get("ticker"), claims=claims, used_ai=True)

    def answer(self, card: Card, question: str) -> str:
        isi_kartu = {
            "headline": card.headline,
            "reason": card.reason,
            "evidence": [e.model_dump() for e in card.evidence],
            "rule_text": card.rule_text,
            "sources": [s.model_dump() for s in card.sources],
        }
        prompt = f"""
Jawab pertanyaan pengguna dalam maksimal 3 kalimat bahasa Indonesia yang mudah.
Gunakan HANYA informasi dalam kartu di bawah. Jangan menghitung angka baru,
membuat prediksi, atau memberi saran investasi. Jika jawabannya tidak tersedia,
katakan persis: "data ini tidak ada di kartu".

Kartu:
{json.dumps(isi_kartu, ensure_ascii=False)}

Pertanyaan:
{question}
""".strip()
        response = httpx.post(
            URL_API.format(model=self.model),
            headers={"x-goog-api-key": self.api_key},
            json={
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0, "maxOutputTokens": 256},
            },
            timeout=BATAS_WAKTU,
        )
        response.raise_for_status()
        jawaban = self._teks_response(response.json()).strip()
        jumlah_kalimat = len([x for x in re.split(r"(?<=[.!?])\s+", jawaban) if x.strip()])
        if jumlah_kalimat > 3:
            raise ValueError("Jawaban Gemini lebih dari 3 kalimat")
        if not jawaban_berdasarkan_kartu(card, jawaban):
            raise ValueError("Jawaban Gemini memuat angka yang tidak ada di kartu")
        return jawaban
