"""Pembaca CSV di data/bahan_produk/ (hasil skrip buat_bahan_produk.py).  [Lane D]

Arti kolom: data/bahan_produk/KAMUS_DATA.md. Persen disimpan sebagai desimal.
"""
from __future__ import annotations

import csv
from math import isfinite
from functools import lru_cache

from ..config import settings
from .sectors import DataUnavailable


@lru_cache
def baca(nama: str) -> tuple[dict[str, str], ...]:
    """baca('radar_free_float') → baris-baris CSV sebagai dict (string)."""
    p = settings.bahan_dir / f"{nama}.csv"
    if not p.exists():
        raise DataUnavailable(f"data/bahan_produk/{nama}.csv belum disalin (tugas D0)")
    with p.open(encoding="utf-8-sig", newline="") as f:
        return tuple(csv.DictReader(f))


def angka(x: str | float | None) -> float | None:
    if x is None or (isinstance(x, str) and x.strip() == ""):
        return None
    try:
        nilai = float(x)
    except (TypeError, ValueError) as e:
        raise DataUnavailable("Angka CSV tidak sesuai") from e
    if isinstance(x, bool) or not isfinite(nilai):
        raise DataUnavailable("Angka CSV tidak berhingga")
    return nilai


def baris(nama: str, ticker: str) -> list[dict[str, str]]:
    simbol = ticker.strip().upper().removesuffix(".JK")
    rows = [r for r in baca(nama) if r.get("symbol") == simbol]
    if not rows:
        raise DataUnavailable(f"{simbol} tidak tersedia di {nama}")
    return rows


def wajib(row: dict, kolom: str) -> float:
    nilai = angka(row.get(kolom))
    if nilai is None:
        raise DataUnavailable(f"Kolom {kolom} kosong")
    return nilai
