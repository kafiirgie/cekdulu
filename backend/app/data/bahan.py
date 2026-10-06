"""Pembaca CSV di data/bahan_produk/ (hasil skrip buat_bahan_produk.py).  [Lane D]

Arti kolom: data/bahan_produk/KAMUS_DATA.md. Persen disimpan sebagai desimal.
"""
from __future__ import annotations

import csv
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


def angka(x: str | None) -> float | None:
    if x is None or x.strip() == "":
        return None
    return float(x)
