"""Modul saham vs komoditas. Aturan K-1 (porsi pendapatan), K-2 (kategori korelasi).  [Lane D]

Pakai harga pasar World Bank (Newcastle untuk batu bara), BUKAN HBA.
Tanpa slider/skenario harga (terlalu dekat ke prediksi).
"""
from __future__ import annotations

from typing import Optional

from ..catalog import param

KATA_KOMODITAS = {
    "emas": ("emas", "gold"),
    "nikel": ("nikel", "nickel"),
    "batubara": ("batu bara", "batubara", "coal"),
    "tembaga": ("tembaga", "copper"),
    "timah": ("timah", "tin"),
}


def komoditas_disebut(teks: str) -> Optional[str]:
    t = teks.lower()
    for kunci, kata in KATA_KOMODITAS.items():
        if any(k in t for k in kata):
            return kunci
    return None


def aturan_k1(porsi_pendapatan: float) -> bool:
    """True = menyesatkan: komoditas yang disebut bukan sumber utama pendapatan."""
    return porsi_pendapatan < param("K-1", "batas_porsi_pendapatan")


def aturan_k2(korelasi: float) -> str:
    if korelasi < param("K-2", "batas_lemah"):
        return "lemah"
    return "sedang" if korelasi < param("K-2", "batas_kuat") else "cukup kuat"


def porsi_pendapatan(ticker: str, komoditas: str) -> float:
    """TODO(D1): dari bahan_produk/segmen_pendapatan.csv (petakan nama segmen → komoditas).
    Contoh: MDKA 'proyek nikel' 82% → nikel."""
    from ..data.sectors import DataUnavailable
    raise DataUnavailable("TODO(D1): porsi_pendapatan dari segmen_pendapatan.csv")


def korelasi(ticker: str, komoditas: str) -> float:
    """TODO(D1): dari bahan_produk/saham_vs_komoditas.csv."""
    from ..data.sectors import DataUnavailable
    raise DataUnavailable("TODO(D1): korelasi dari saham_vs_komoditas.csv")
