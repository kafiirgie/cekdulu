"""Kartu "Yang tidak diceritakan" di luar 8 pemeriksa standar.  [Lane D]

Setiap provider: (ticker, klaim) → Card dengan verdict "info", atau None kalau tidak relevan.
Kalau data belum ada, raise DataUnavailable → kartu dilewati diam-diam.

Kartu dari pemeriksa standar yang berstatus "temuan" (suspensi, orang dalam, dst.)
otomatis masuk ke untold oleh engine — tidak perlu dibuat ulang di sini.
"""
from __future__ import annotations

from typing import Callable, Optional

from ..data.sectors import DataUnavailable
from ..schemas import Card, Claim

Provider = Callable[[str, list[Claim]], Optional[Card]]


def papan_pemantauan(ticker: str, claims: list[Claim]) -> Optional[Card]:
    """TODO(D2): bahan_produk/papan_pemantauan_khusus.csv. Contoh: MGLV 6–15 Apr 2026 (kriteria 10)."""
    raise DataUnavailable("TODO(D2)")


def segmen(ticker: str, claims: list[Claim]) -> Optional[Card]:
    """TODO(D2): muncul jika klaim menyebut komoditas/bisnis dan m_komoditas tidak dipakai."""
    raise DataUnavailable("TODO(D2)")


def analis(ticker: str, claims: list[Claim]) -> Optional[Card]:
    """TODO(D2): rating_analis.csv. Label 'jumlah rekomendasi', bukan 'jumlah analis'."""
    raise DataUnavailable("TODO(D2)")


def pemegang(ticker: str, claims: list[Claim]) -> Optional[Card]:
    """TODO(D2): komposisi_pemegang_saham.csv. Bandingkan tren dalam satu emiten saja."""
    raise DataUnavailable("TODO(D2)")


def aksi_korporasi(ticker: str, claims: list[Claim]) -> Optional[Card]:
    """TODO(D2): kalender_aksi_korporasi.csv — dividen/right issue/split dalam 90 hari."""
    raise DataUnavailable("TODO(D2)")


def likuiditas(ticker: str, claims: list[Claim]) -> Optional[Card]:
    """TODO(D2): rata-rata nilai transaksi 60 hari dari harga harian (ambang: usulkan di rules.json)."""
    raise DataUnavailable("TODO(D2)")


PROVIDERS: dict[str, Provider] = {
    "papan_pemantauan": papan_pemantauan,
    "segmen": segmen,
    "analis": analis,
    "pemegang": pemegang,
    "aksi_korporasi": aksi_korporasi,
    "likuiditas": likuiditas,
}
