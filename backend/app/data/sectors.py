"""Adapter Sectors API — satu pintu untuk semua panggilan ke Sectors.  [Lane B]

Tiga mode (CEKDULU_DATA_MODE):
- fixture : baca data/fixtures/<TICKER>/<kunci>.json. 0 kredit. Default demo.
- live    : baca data/cache dulu; kalau belum ada, panggil Sectors, simpan ke cache.
            Dibatasi SECTORS_CREDIT_BUDGET supaya juri tidak menghabiskan kredit.
- mock    : adapter tidak dipakai (endpoint mengembalikan contract/examples).

Kunci (`kunci`) = nama file fixture. Daftar kunci + path endpoint ada di ENDPOINTS.
Header: `Authorization: <key>` TANPA "Bearer". 429 tidak memotong kredit, 404 memotong 1.
"""
from __future__ import annotations

import json
import threading
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import httpx

from ..config import settings


class DataUnavailable(Exception):
    """Data tidak ada (fixture belum ditarik, budget habis, atau Sectors kosong).
    Engine menerjemahkannya jadi status `data_kurang`, bukan `gagal`."""


# Path & params diambil dari skrip yang sudah terbukti jalan:
# D:\GitHub\cekdulu-datacheck\skrip\cek_data_cekdulu.py dan cek_eksplor.py.
# Tanggal relatif ({start}, {end}) diisi otomatis oleh _call_live (start = hari ini − hari).
ENDPOINTS: dict[str, dict[str, Any]] = {
    # kunci               path                                              params                                                   kredit
    # Bagian laporan untuk B1/B2. Kredit dihitung per bagian, bukan per request.
    "report":             {"path": "/v2/company/report/{ticker}/", "params": {"sections": "overview,ownership,valuation,dividend"}, "kredit": 4},
    "report_keuangan":    {"path": "/v2/company/report/{ticker}/", "params": {"sections": "valuation,dividend"}, "kredit": 2},
    "keuangan_kuartalan": {"path": "/v2/financials/quarterly/{ticker}/", "params": {"n_quarters": 5}, "kredit": 5},
    "harga_harian":       {"path": "/v2/daily/{ticker}/", "params": {"start": "-90", "end": "0"}, "kredit": 1},
    "aliran_asing":       {"path": "/v2/foreign-flow/{ticker}/", "params": {"start": "-90", "end": "0"}, "kredit": 1},
    "filings":            {"path": "/v2/filings/", "params": {"symbol": "{ticker}", "start": "-365", "end": "0", "limit": 30}, "kredit": 1},
    "suspensi":           {"path": "/v2/suspensions/", "params": {"symbol": "{ticker}", "limit": 30}, "kredit": 1},
    "aksi_korporasi":     {"path": "/v2/company/corporate-actions/{ticker}/", "params": {}, "kredit": 1},
    "segmen":             {"path": "/v2/company/get-segments/{ticker}/", "params": {}, "kredit": 1},
    "report_future":      {"path": "/v2/company/report/{ticker}/", "params": {"sections": "future"}, "kredit": 1},
    "komposisi_pemegang": {"path": "/v2/company/shareholders-composition/{ticker}/", "params": {"year": "{tahun}"}, "kredit": 1},
}

_budget_lock = threading.Lock()
_credits_used = 0


def _file(base: Path, ticker: str, kunci: str) -> Path:
    return base / ticker.upper() / f"{kunci}.json"


def credits_used() -> int:
    return _credits_used


def get(ticker: str, kunci: str) -> Any:
    """Ambil data mentah satu kunci untuk satu emiten."""
    ticker = ticker.upper()
    mode = settings.data_mode

    fx = _file(settings.fixtures_dir, ticker, kunci)
    if fx.exists():
        return json.loads(fx.read_text(encoding="utf-8"))
    if mode == "fixture":
        raise DataUnavailable(f"Fixture {fx.relative_to(settings.fixtures_dir.parent)} belum ada")

    cache = _file(settings.cache_dir, ticker, kunci)
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))

    if mode != "live":
        raise DataUnavailable(f"Mode {mode} tidak mengizinkan panggilan live Sectors")
    data = _call_live(ticker, kunci)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def _isi(v: Any, ticker: str) -> Any:
    """'{ticker}' → MGLV, '{tahun}' → 2026, '-90' → tanggal 90 hari lalu, '0' → hari ini."""
    if not isinstance(v, str):
        return v
    if v.lstrip("-").isdigit() and (v.startswith("-") or v == "0"):
        return (date.today() + timedelta(days=int(v))).isoformat()
    return v.format(ticker=ticker, tahun=date.today().year)


def _call_live(ticker: str, kunci: str) -> Any:
    global _credits_used
    spec = ENDPOINTS.get(kunci)
    if not spec or spec["path"] == "TODO":
        raise DataUnavailable(f"Endpoint '{kunci}' belum dipetakan (lihat TODO B0)")
    if not settings.sectors_api_key:
        raise DataUnavailable("SECTORS_API_KEY kosong")
    with _budget_lock:
        if _credits_used + spec["kredit"] > settings.sectors_credit_budget:
            raise DataUnavailable("Batas kredit live untuk server ini sudah habis")
        _credits_used += spec["kredit"]

    path = spec["path"].format(ticker=ticker)
    params = {k: _isi(v, ticker) for k, v in spec["params"].items()}
    r = httpx.get(
        settings.sectors_base_url + path,
        params=params,
        headers={"Authorization": settings.sectors_api_key},
        timeout=20,
    )
    if r.status_code == 404:
        raise DataUnavailable(f"Sectors tidak punya data '{kunci}' untuk {ticker}")
    r.raise_for_status()
    return r.json()
