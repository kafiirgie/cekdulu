"""Modul Radar Free Float. Aturan R-1 + tenggat Peraturan I-A (SE-00004/BEI/03-2026).  [Lane D]"""
from __future__ import annotations

from typing import Optional

from ..catalog import param
from ..data import bahan
from ..schemas import FreeFloatItem, FreeFloatList

KAP_BESAR = 5e12  # Rp5 T


def kelompok(market_cap: float, ff: float) -> tuple[str, float, str]:
    """(kelompok, target berikutnya, tenggat) sesuai tabel FINAL_PLAN §4.1."""
    if market_cap > KAP_BESAR and ff < 0.125:
        return "kap_besar_ff_rendah", 0.125, "2027-03-31"  # lalu 15% pada 2028-03-31
    if market_cap > KAP_BESAR:
        return "kap_besar_ff_menengah", 0.15, "2027-03-31"
    return "kap_kecil", 0.15, "2029-03-31"


def nilai_dilepas(target: float, ff: float, market_cap: float) -> float:
    return max(0.0, (target - ff) * market_cap)


def hari_serap(nilai: float, rata_transaksi_harian: Optional[float]) -> Optional[float]:
    if not rata_transaksi_harian or rata_transaksi_harian <= 0:
        return None
    return nilai / rata_transaksi_harian


def tekanan(hari: Optional[float]) -> Optional[str]:
    if hari is None:
        return None
    if hari < param("R-1", "hari_ringan"):
        return "ringan"
    return "sedang" if hari <= param("R-1", "hari_berat") else "berat"


def label_hari(hari: Optional[float]) -> str:
    """Untuk tampilan: '> 1.000 hari' kalau ekstrem (DUTI > 100.000 hari)."""
    if hari is None:
        return "tidak bisa dihitung"
    batas = param("R-1", "batas_tampil_hari")
    return f"> {batas:,} hari".replace(",", ".") if hari > batas else f"{hari:.0f} hari"


def hitung(ticker: str, company: Optional[str], ff: float, market_cap: float,
           rata_transaksi: Optional[float], papan: bool = False) -> FreeFloatItem:
    kel, target, tenggat = kelompok(market_cap, ff)
    nilai = nilai_dilepas(target, ff, market_cap)
    hari = hari_serap(nilai, rata_transaksi)
    return FreeFloatItem(ticker=ticker, company=company, free_float=ff, market_cap=market_cap,
                         kelompok=kel, target=target, tenggat=tenggat, nilai_dilepas=nilai,
                         hari_serap=hari, tekanan=tekanan(hari), papan_pemantauan=papan)


def daftar() -> FreeFloatList:
    """Dari bahan_produk/radar_free_float.csv. Hari serap dihitung ULANG di sini dengan aturan R-1
    (supaya ambang di rules.json yang berlaku), lalu dibandingkan dengan kolom CSV di tes.
    TODO(D1): tandai papan_pemantauan dari papan_pemantauan_khusus.csv (aktif = 'ya')."""
    rows = bahan.baca("radar_free_float")
    items = [
        hitung(r["symbol"], r.get("nama"), float(r["free_float"]), float(r["market_cap"]),
               bahan.angka(r.get("rata2_nilai_transaksi_60h")))
        for r in rows
    ]
    items.sort(key=lambda i: (i.tenggat, -(i.hari_serap or 0)))
    return FreeFloatList(as_of="2026-09-30", items=items)
