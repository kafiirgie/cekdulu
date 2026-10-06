"""Data yang sudah dirapikan untuk pemeriksa.  [Lane B]

Pemeriksa TIDAK membaca JSON mentah Sectors. Mereka memanggil fungsi di sini,
yang mengubah JSON mentah (dari sectors.get) jadi bentuk sederhana di bawah.
Keuntungannya: aturan di checkers/ bisa dites dengan data buatan tanpa API.

Setiap fungsi masih TODO. Isi dengan parser setelah fixture ditarik (tugas B0/B1).
Kalau field yang dibutuhkan kosong, `raise DataUnavailable(...)` — jangan isi 0.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from .sectors import DataUnavailable, get  # noqa: F401  (dipakai saat TODO diisi)


@dataclass
class Kuartal:
    periode: str          # "2026-Q2"
    laba_bersih: float    # Rupiah penuh


@dataclass
class Valuasi:
    per: Optional[float]
    pbv: Optional[float]
    forward_pe: Optional[float]  # None = tidak tersedia (jangan 0)


@dataclass
class Dividen:
    yield_ttm: Optional[float]       # 0.25 = 25%
    payout_ratio: Optional[float]    # 1.14 = 114%
    yield_rata_sektor: Optional[float]


@dataclass
class TransaksiOrangDalam:
    tanggal: date
    nama: str
    jenis: str             # beli / jual
    nilai_rp: Optional[float]
    sebelum: Optional[float]   # porsi kepemilikan, desimal
    sesudah: Optional[float]


@dataclass
class AliranAsing:
    tanggal: date
    bersih_rp: float       # positif = masuk bersih


@dataclass
class HargaHarian:
    tanggal: date
    close: float
    nilai_transaksi_rp: Optional[float] = None


@dataclass
class Suspensi:
    tanggal: date
    alasan: str


def nama_emiten(ticker: str) -> Optional[str]:
    raise DataUnavailable("TODO(B1): ambil nama perusahaan dari report")


def laba_kuartalan(ticker: str) -> list[Kuartal]:
    raise DataUnavailable("TODO(B2): parser keuangan_kuartalan")


def valuasi(ticker: str) -> Valuasi:
    raise DataUnavailable("TODO(B2): parser report section valuation")


def dividen(ticker: str) -> Dividen:
    raise DataUnavailable("TODO(B2): parser report section dividend")


def transaksi_orang_dalam(ticker: str) -> list[TransaksiOrangDalam]:
    raise DataUnavailable("TODO(B1): parser filings")


def aliran_asing(ticker: str) -> list[AliranAsing]:
    raise DataUnavailable("TODO(B2): parser aliran_asing")


def harga_harian(ticker: str) -> list[HargaHarian]:
    raise DataUnavailable("TODO(B1): parser harga_harian")


def tanggal_aksi_korporasi(ticker: str) -> set[date]:
    """Tanggal ex-dividen / split / right issue. Dipakai aturan H-1."""
    raise DataUnavailable("TODO(B1): parser aksi_korporasi")


def riwayat_suspensi(ticker: str) -> list[Suspensi]:
    raise DataUnavailable("TODO(B1): parser suspensi")


def free_float(ticker: str) -> float:
    """Porsi entri 'Public' di major_shareholders (desimal)."""
    raise DataUnavailable("TODO(B1): parser report major_shareholders")
