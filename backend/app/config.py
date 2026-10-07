"""Pengaturan dari environment (.env di root repo). Lihat .env.example."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # dotenv opsional saat tes
    load_dotenv = None

ROOT = Path(__file__).resolve().parents[2]  # root repo
if load_dotenv:
    load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    # mock    = /api/klaim & /api/cek mengembalikan contract/examples (untuk FE di awal)
    # fixture = mesin aturan asli, data dari data/fixtures (0 kredit) — default demo
    # live    = mesin aturan asli, data dari Sectors API + simpan ke cache
    data_mode: str = os.getenv("CEKDULU_DATA_MODE", "fixture")
    sectors_api_key: str = os.getenv("SECTORS_API_KEY", "")
    sectors_base_url: str = os.getenv("SECTORS_BASE_URL", "https://api.sectors.app")
    # Batas kredit untuk mode live di satu proses server. 0 = tanpa panggilan live.
    sectors_credit_budget: int = int(os.getenv("SECTORS_CREDIT_BUDGET", "100"))
    llm_provider: str = os.getenv("LLM_PROVIDER", "none")  # none | gemini | openai_compat | ... (keputusan terbuka #1)
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")  # hanya untuk penyedia kompatibel OpenAI
    # Panel Tanya: klasifikasi TypeSafe/JEV, jawaban tetap disusun kode.
    tanya_mode: str = os.getenv("TANYA_MODE", "auto")  # auto = pakai JEV kalau kunci ada; off = selalu template kode
    jev_base_url: str = os.getenv("JEV_BASE_URL", "https://api.typesafe.ai/v1")
    jev_api_key: str = os.getenv("JEV_API_KEY", "")
    jev_model: str = os.getenv("JEV_MODEL", "jev-latest")
    cors_origins: tuple[str, ...] = tuple(
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
    )

    contract_dir: Path = ROOT / "contract"
    fixtures_dir: Path = ROOT / "data" / "fixtures"
    cache_dir: Path = ROOT / "data" / "cache"
    bahan_dir: Path = ROOT / "data" / "bahan_produk"


settings = Settings()
