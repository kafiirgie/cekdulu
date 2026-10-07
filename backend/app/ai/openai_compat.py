"""Penyedia kompatibel OpenAI (mis. ollama-cloud). Hanya untuk ekstraksi klaim.  [Lane C]

Terpisah dari gemini.py secara sengaja: perilaku Gemini tidak diubah sama sekali.
Kalau penyedia ini gagal, provider.py jatuh ke NoLLM seperti biasa.
"""
from __future__ import annotations

import json
from typing import Optional

import httpx

from ..catalog import catalog
from ..schemas import Claim, KlaimResponse

# Model nalar menghabiskan jatahnya untuk berpikir sebelum menulis jawaban. Kalau
# max_tokens terlalu kecil, sisa untuk isi habis dan `content` kembali KOSONG walau
# status 200 (finish_reason "length") -- panggilan dianggap gagal dan app diam-diam
# jatuh ke heuristik (used_ai=false). Diukur pada deepseek-v4.1-flash dengan prompt
# ekstraksi 1365 karakter: 1024 -> kosong, 2048 -> kosong, 4096 -> isi 221 karakter.
BATAS_WAKTU = httpx.Timeout(connect=5.0, read=180.0, write=10.0, pool=2.0)
MIN_TOKEN = 4096


class OpenAICompatLLM:
    """POST {base_url}/chat/completions dengan response_format json_object."""

    def __init__(self, base_url: str, api_key: str, model: str):
        if not base_url:
            raise ValueError("LLM_BASE_URL belum diisi")
        if not api_key:
            raise ValueError("LLM_API_KEY belum diisi")
        if not model:
            raise ValueError("LLM_MODEL belum diisi")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    @staticmethod
    def _katalog() -> tuple[list[str], str]:
        semua = catalog()["checks"] + catalog()["untold"]
        ids = [item["id"] for item in semua]
        label = ", ".join(f'{item["id"]} = {item["label"]}' for item in semua)
        return ids, label

    @classmethod
    def _prompt(cls, text: str, ticker: Optional[str]) -> str:
        _, label = cls._katalog()
        petunjuk_ticker = (
            f"Ticker dari pengguna adalah {ticker.upper()}."
            if ticker else
            "Ambil ticker 4 huruf kapital yang benar-benar tertulis di source_text."
        )
        return f"""
Kamu memecah pesan saham Indonesia menjadi klaim, bukan memeriksa kebenarannya.
{petunjuk_ticker}
Isi `source_text` dengan Pesan di bawah ini secara persis.

Aturan wajib:
- Setiap `claims[].text` harus substring persis dari `source_text`, tanpa parafrasa.
- Pilih maksimal dua `checks` dari katalog ini: {label}.
- Prediksi, opini, dan rumor tanpa fakta terukur memakai `checks: []`, walaupun
  menyebut komoditas. Contoh: "pasti ikut naik" dan "bakal ARA".
- Jika ada beberapa ticker, pilih ticker pertama dan hanya ambil klaim tentang ticker itu.
- Jangan menentukan vonis, menghitung angka, memilih data, atau memberi saran.
Balas HANYA dengan JSON: {{"source_text": "...", "ticker": "...", "claims": [{{"text": "...", "checks": []}}]}}

Pesan:
{text}
""".strip()

    @staticmethod
    def _teks(data: dict) -> str:
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("Penyedia OpenAI-compatible tidak mengembalikan isi") from exc

    def extract_claims(self, text: Optional[str], image_base64: Optional[str],
                       ticker: Optional[str]) -> KlaimResponse:
        # Tanpa dukungan gambar di jalur ini: screenshot ditolak supaya tidak menebak.
        if not text or image_base64:
            return KlaimResponse(ticker=ticker.upper() if ticker else None, claims=[], used_ai=False)

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": self._prompt(text, ticker)}],
                "temperature": 0,
                "max_tokens": MIN_TOKEN,
                "response_format": {"type": "json_object"},
            },
            timeout=BATAS_WAKTU,
        )
        response.raise_for_status()
        mentah = json.loads(self._teks(response.json()))
        source_text = mentah.get("source_text")
        if not isinstance(source_text, str) or not source_text.strip():
            source_text = text  # pesan pengguna sudah verbatim; boleh dipakai sebagai sumber
        claims = []
        for item in mentah.get("claims", []):
            claim_text = item.get("text")
            if not isinstance(claim_text, str):
                continue
            awal = source_text.find(claim_text)
            if awal < 0:
                continue
            checks = [c for c in item.get("checks", []) if isinstance(c, str)]
            claims.append(Claim(id=f"c{len(claims) + 1}", text=claim_text,
                                span=(awal, awal + len(claim_text)), checks=checks))
        return KlaimResponse(ticker=mentah.get("ticker"), claims=claims, used_ai=True)
