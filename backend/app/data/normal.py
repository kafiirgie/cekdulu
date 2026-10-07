"""Data yang sudah dirapikan untuk pemeriksa.  [Lane B]

Pemeriksa TIDAK membaca JSON mentah Sectors. Mereka memanggil fungsi di sini,
yang mengubah JSON mentah (dari sectors.get) jadi bentuk sederhana di bawah.
Keuntungannya: aturan di checkers/ bisa dites dengan data buatan tanpa API.

Parser B1 memakai bentuk JSON yang dicatat di docs/DATA_NOTES.md.
Parser laporan keuangan dan aliran asing menyusul di tugas B2.
Kalau field yang dibutuhkan kosong, `raise DataUnavailable(...)` — jangan isi 0.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Optional

from .sectors import DataUnavailable, get


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


def _ambil(ticker: str, kunci: str):
    data = get(ticker.strip().upper().removesuffix(".JK"), kunci)
    if kunci != "harga_harian" and not isinstance(data, dict):
        raise DataUnavailable(f"Bentuk data {kunci} tidak sesuai")
    return data


def _daftar(data, nama: str) -> list[dict]:
    if not isinstance(data, list) or any(not isinstance(r, dict) for r in data):
        raise DataUnavailable(f"Daftar {nama} tidak tersedia atau tidak sesuai")
    return data


def _teks(nilai, nama: str) -> str:
    if not isinstance(nilai, str) or not nilai.strip():
        raise DataUnavailable(f"{nama} tidak tersedia")
    return nilai.strip()


def _tanggal(nilai, nama: str) -> date:
    try:
        return date.fromisoformat(_teks(nilai, nama)[:10])
    except ValueError as e:
        raise DataUnavailable(f"Tanggal {nama} tidak sesuai") from e


def _angka(nilai, nama: str, opsional: bool = False) -> Optional[float]:
    if opsional and (nilai is None or nilai == ""):
        return None
    try:
        angka = float(nilai)
    except (TypeError, ValueError, OverflowError) as e:
        raise DataUnavailable(f"Angka {nama} tidak tersedia atau tidak sesuai") from e
    if isinstance(nilai, bool) or not isfinite(angka):
        raise DataUnavailable(f"Angka {nama} tidak sesuai")
    return angka


def nama_emiten(ticker: str) -> Optional[str]:
    return _teks(_ambil(ticker, "report").get("company_name"), "company_name")


def laba_kuartalan(ticker: str) -> list[Kuartal]:
    raise DataUnavailable("TODO(B2): parser keuangan_kuartalan")


def valuasi(ticker: str) -> Valuasi:
    raise DataUnavailable("TODO(B2): parser report section valuation")


def dividen(ticker: str) -> Dividen:
    raise DataUnavailable("TODO(B2): parser report section dividend")


def transaksi_orang_dalam(ticker: str) -> list[TransaksiOrangDalam]:
    rows = _daftar(_ambil(ticker, "filings").get("results"), "filings.results")
    hasil = []
    for r in rows:
        jenis = _teks(r.get("transaction_type"), "transaction_type").lower()
        if jenis not in ("buy", "sell"):
            raise DataUnavailable(f"Jenis transaksi {jenis} tidak dikenal")
        sebelum = _angka(r.get("share_percentage_before"), "share_percentage_before", opsional=True)
        sesudah = _angka(r.get("share_percentage_after"), "share_percentage_after", opsional=True)
        hasil.append(TransaksiOrangDalam(
            tanggal=_tanggal(r.get("timestamp"), "timestamp"),
            nama=_teks(r.get("holder_name"), "holder_name"),
            jenis="beli" if jenis == "buy" else "jual",
            nilai_rp=_angka(r.get("transaction_value"), "transaction_value"),
            sebelum=sebelum / 100 if sebelum is not None else None,
            sesudah=sesudah / 100 if sesudah is not None else None,
        ))
    return sorted(hasil, key=lambda r: r.tanggal)


def aliran_asing(ticker: str) -> list[AliranAsing]:
    raise DataUnavailable("TODO(B2): parser aliran_asing")


def harga_harian(ticker: str) -> list[HargaHarian]:
    rows = _daftar(_ambil(ticker, "harga_harian"), "harga_harian")
    if not rows:
        raise DataUnavailable("Harga harian kosong")
    hasil = []
    for r in rows:
        close = _angka(r.get("close"), "close")
        volume = _angka(r.get("volume"), "volume", opsional=True)
        if close <= 0 or (volume is not None and volume < 0):
            raise DataUnavailable("Harga atau volume harian tidak sesuai")
        hasil.append(HargaHarian(
            tanggal=_tanggal(r.get("date"), "date"), close=close,
            nilai_transaksi_rp=close * volume if volume is not None else None,
        ))
    return sorted(hasil, key=lambda r: r.tanggal)


def tanggal_aksi_korporasi(ticker: str) -> set[date]:
    """Tanggal ex-dividen / split / right issue. Dipakai aturan H-1."""
    data = _ambil(ticker, "aksi_korporasi")
    if "corporate_actions" not in data:
        raise DataUnavailable("corporate_actions tidak tersedia")
    aksi = data["corporate_actions"]
    if aksi is None:
        return set()
    if not isinstance(aksi, dict):
        raise DataUnavailable("Bentuk corporate_actions tidak sesuai")
    hasil = set()
    for jenis in ("dividend", "right_issue", "stock_split", "bonus", "upcoming_dividend"):
        rows = aksi.get(jenis)
        if rows is None:
            continue
        for r in _daftar(rows, jenis):
            # Sectors menamai tanggal stock split 'date'; jenis lain memakai 'ex_date'.
            tanggal = r.get("ex_date") or (r.get("date") if jenis == "stock_split" else None)
            if tanggal:
                hasil.add(_tanggal(tanggal, f"{jenis}.tanggal_ex"))
    return hasil


def riwayat_suspensi(ticker: str) -> list[Suspensi]:
    rows = _daftar(_ambil(ticker, "suspensi").get("results"), "suspensi.results")
    return sorted((Suspensi(
        tanggal=_tanggal(r.get("suspension_date"), "suspension_date"),
        alasan=_teks(r.get("reason"), "reason"),
    ) for r in rows), key=lambda r: r.tanggal)


def free_float(ticker: str) -> float:
    """Porsi entri 'Public' di major_shareholders (desimal)."""
    ownership = _ambil(ticker, "report").get("ownership")
    if not isinstance(ownership, dict):
        raise DataUnavailable("ownership tidak tersedia")
    for r in _daftar(ownership.get("major_shareholders"), "major_shareholders"):
        if r.get("name") == "Public":
            porsi = _angka(r.get("share_percentage"), "Public.share_percentage")
            if not 0 <= porsi <= 1:
                raise DataUnavailable("Porsi Public harus berupa desimal 0 sampai 1")
            return porsi
    raise DataUnavailable("Entri Public tidak tersedia")
