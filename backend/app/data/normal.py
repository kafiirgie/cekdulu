"""Data yang sudah dirapikan untuk pemeriksa.  [Lane B]

Pemeriksa TIDAK membaca JSON mentah Sectors. Mereka memanggil fungsi di sini,
yang mengubah JSON mentah (dari sectors.get) jadi bentuk sederhana di bawah.
Keuntungannya: aturan di checkers/ bisa dites dengan data buatan tanpa API.

Parser memakai bentuk JSON yang dicatat di docs/DATA_NOTES.md.
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
    periode: str          # tanggal akhir kuartal, ISO
    laba_bersih: float    # Rupiah penuh


@dataclass
class Valuasi:
    per: Optional[float]
    pbv: Optional[float]
    forward_pe: Optional[float]  # None = tidak tersedia (jangan 0)
    as_of: Optional[date] = None


@dataclass
class Dividen:
    yield_ttm: Optional[float]       # 0.25 = 25%
    payout_ratio: Optional[float]    # 1.14 = 114%
    yield_rata_sektor: Optional[float]
    as_of: Optional[date] = None


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
class KomposisiBulanan:
    tanggal: date
    porsi_asing: float
    porsi_ritel_lokal: float
    jumlah_pemegang: Optional[int]


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
    if kunci not in ("harga_harian", "keuangan_kuartalan") and not isinstance(data, dict):
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
    rows = _daftar(_ambil(ticker, "keuangan_kuartalan"), "keuangan_kuartalan")
    if not rows:
        raise DataUnavailable("Laba kuartalan kosong")
    return sorted((Kuartal(
        periode=str(_tanggal(r.get("date"), "date")),
        laba_bersih=_angka(r.get("earnings"), "earnings"),
    ) for r in rows), key=lambda r: r.periode)


def _bagian_laporan(ticker: str, bagian: str) -> dict:
    data = _ambil(ticker, "report").get(bagian)
    if not isinstance(data, dict) and bagian in ("valuation", "dividend"):
        # Laporan tambahan tidak menimpa snapshot overview/ownership yang dibagikan tim.
        data = _ambil(ticker, "report_keuangan").get(bagian)
    if not isinstance(data, dict):
        raise DataUnavailable(f"Bagian {bagian} tidak tersedia")
    return data


def valuasi(ticker: str) -> Valuasi:
    data = _bagian_laporan(ticker, "valuation")
    rows = _daftar(data.get("historical_valuation"), "historical_valuation")
    if not rows:
        raise DataUnavailable("Riwayat valuasi kosong")
    terbaru = max(rows, key=lambda r: _angka(r.get("year"), "year"))
    return Valuasi(
        per=_angka(terbaru.get("pe"), "pe", opsional=True),
        pbv=_angka(terbaru.get("pb"), "pb", opsional=True),
        forward_pe=_angka(data.get("forward_pe"), "forward_pe", opsional=True),
        as_of=_tanggal(data.get("latest_close_date"), "latest_close_date"),
    )


def dividen(ticker: str) -> Dividen:
    data = _bagian_laporan(ticker, "dividend")
    if "yield_ttm" not in data:
        raise DataUnavailable("yield_ttm tidak tersedia")
    yield_ttm = _angka(data["yield_ttm"], "yield_ttm", opsional=True)
    tanggal = _bagian_laporan(ticker, "valuation").get("latest_close_date") if yield_ttm else None
    return Dividen(
        yield_ttm=yield_ttm,
        payout_ratio=_angka(data.get("payout_ratio"), "payout_ratio", opsional=True),
        yield_rata_sektor=None,  # Rata-rata emiten sendiri bukan rata-rata sektor (B3).
        as_of=_tanggal(tanggal, "latest_close_date") if yield_ttm else None,
    )


def transaksi_orang_dalam(ticker: str) -> list[TransaksiOrangDalam]:
    rows = _daftar(_ambil(ticker, "filings").get("results"), "filings.results")
    hasil = []
    for r in rows:
        jenis = _teks(r.get("transaction_type"), "transaction_type").lower()
        if jenis == "others":
            continue  # Pemindahan saham bukan pembelian/penjualan untuk aturan O-1.
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
    rows = _daftar(_ambil(ticker, "aliran_asing").get("data"), "aliran_asing.data")
    if not rows:
        raise DataUnavailable("Aliran asing kosong")
    return sorted((AliranAsing(
        tanggal=_tanggal(r.get("date"), "date"),
        bersih_rp=_angka(r.get("net_foreign_inflow"), "net_foreign_inflow"),
    ) for r in rows), key=lambda r: r.tanggal)


def komposisi_bulanan(ticker: str) -> list[KomposisiBulanan]:
    rows = _daftar(_ambil(ticker, "komposisi_pemegang").get("data"), "komposisi_pemegang.data")
    if not rows:
        raise DataUnavailable("Komposisi pemegang kosong")
    hasil = []
    for r in rows:
        lokal = _angka(r.get("total_l"), "total_l")
        asing = _angka(r.get("total_f"), "total_f")
        ritel = _angka(r.get("individual_l"), "individual_l")
        pemegang = _angka(r.get("numbers_of_shareholders"), "numbers_of_shareholders", opsional=True)
        if lokal < 0 or asing < 0 or lokal + asing <= 0 or not 0 <= ritel <= lokal:
            raise DataUnavailable("Jumlah saham komposisi tidak sesuai")
        if pemegang is not None and (pemegang < 0 or not pemegang.is_integer()):
            raise DataUnavailable("Jumlah pemegang tidak sesuai")
        hasil.append(KomposisiBulanan(
            tanggal=_tanggal(r.get("date"), "date"),
            porsi_asing=asing / (lokal + asing),
            porsi_ritel_lokal=ritel / (lokal + asing),
            jumlah_pemegang=int(pemegang) if pemegang is not None else None,
        ))
    return sorted(hasil, key=lambda r: r.tanggal)


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
