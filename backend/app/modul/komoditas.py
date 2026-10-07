"""Modul saham vs komoditas. Aturan K-1 (porsi pendapatan), K-2 (kategori korelasi).  [Lane D]

Pakai harga pasar World Bank (Newcastle untuk batu bara), BUKAN HBA.
Tanpa slider/skenario harga (terlalu dekat ke prediksi).
"""
from __future__ import annotations

from typing import Optional

from ..catalog import param
from ..data import bahan
from ..data.sectors import DataUnavailable
from ..schemas import KomoditasDetail, KomoditasItem, KomoditasList, Source

NAMA_SERI = {"batubara": "Coal, Australian", "nikel": "Nickel", "emas": "Gold",
             "tembaga": "Copper", "timah": "Tin"}
SNAPSHOT = "2026-09-30"

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
    if komoditas not in NAMA_SERI:
        raise DataUnavailable("Komoditas belum didukung")
    return sum(porsi for jenis, porsi in segmen_terpetakan(ticker) if jenis == komoditas)


def segmen_terpetakan(ticker: str) -> list[tuple[str, float]]:
    rows = bahan.baris("segmen_pendapatan", ticker)
    peta = {r["segmen"]: r["komoditas"] for r in bahan.baris("segmen_ke_komoditas", ticker)}
    hasil = []
    for r in rows:
        if r["segmen"] not in peta:
            raise DataUnavailable(f"Segmen {r['segmen']} belum dipetakan")
        porsi = bahan.wajib(r, "porsi")
        if not 0 <= porsi <= 1:
            raise DataUnavailable("Porsi pendapatan tidak sesuai")
        # Segmen campuran tetap terpisah; tidak dianggap pendapatan murni emas/tembaga.
        hasil.append((peta[r["segmen"]], porsi))
    return hasil


def komoditas_terbesar(ticker: str) -> tuple[str, float]:
    jumlah = {}
    for jenis, porsi in segmen_terpetakan(ticker):
        jumlah[jenis] = jumlah.get(jenis, 0) + porsi
    return max(jumlah.items(), key=lambda r: r[1])


def tahun_buku(ticker: str) -> int:
    rows = bahan.baris("segmen_pendapatan", ticker)
    tahun = {int(bahan.wajib(r, "tahun_buku")) for r in rows}
    if len(tahun) != 1:
        raise DataUnavailable("Segmen mencampur tahun buku")
    return tahun.pop()


def sumber_segmen(ticker: str) -> Source:
    tahun = tahun_buku(ticker)
    return Source(name=f"Sectors · get-segments · tahun buku {tahun}", as_of=f"{tahun}-12-31")


def korelasi(ticker: str, komoditas: str) -> float:
    return bahan.wajib(baris_korelasi(ticker, komoditas), "korelasi_bulanan")


def baris_korelasi(ticker: str, komoditas: str) -> dict:
    for r in bahan.baris("saham_vs_komoditas", ticker):
        if r["komoditas"] == NAMA_SERI.get(komoditas):
            return r
    raise DataUnavailable("Korelasi komoditas tidak tersedia")


def item(ticker: str, jenis: str) -> KomoditasItem:
    r = baris_korelasi(ticker, jenis)
    kor = bahan.wajib(r, "korelasi_bulanan")
    if not -1 <= kor <= 1:
        raise DataUnavailable("Korelasi tidak sesuai")
    porsi = terbesar = porsi_besar = tahun = None
    sumber = [Source(name="Sectors · total return saham · " + r["periode"], as_of=SNAPSHOT),
              Source(name="World Bank Pink Sheet · " + r["periode"], as_of="2026-09-02")]
    try:
        porsi = porsi_pendapatan(ticker, jenis)
        terbesar, porsi_besar = komoditas_terbesar(ticker)
        tahun = tahun_buku(ticker)
        sumber.append(sumber_segmen(ticker))
    except DataUnavailable:
        pass  # Korelasi tetap tersedia; porsi pendapatan yang hilang tidak dibuat-buat.
    return KomoditasItem(ticker=ticker, komoditas=jenis, porsi_pendapatan=porsi,
                         komoditas_terbesar=terbesar, porsi_terbesar=porsi_besar, tahun_buku=tahun,
                         korelasi=kor, kategori=aturan_k2(kor), periode=r["periode"],
                         n_bulan=int(bahan.wajib(r, "n_bulan")),
                         total_return_saham=bahan.angka(r.get("total_return_saham")),
                         perubahan_komoditas=bahan.angka(r.get("perubahan_komoditas")),
                         arah_tahunan=[s.strip() for s in r["arah_tahunan"].split(";") if s.strip()], sources=sumber)


def daftar(jenis: str) -> KomoditasList:
    if jenis not in NAMA_SERI:
        raise DataUnavailable("Komoditas belum didukung")
    tickers = sorted({r["symbol"] for r in bahan.baca("saham_vs_komoditas") if r["komoditas"] == NAMA_SERI[jenis]})
    return KomoditasList(as_of=SNAPSHOT, jenis=jenis, items=[item(t, jenis) for t in tickers])


def detail(ticker: str) -> KomoditasDetail:
    ticker = ticker.upper().removesuffix(".JK")
    rows = bahan.baris("saham_vs_komoditas", ticker)
    jenis = [k for k, seri in NAMA_SERI.items() if any(r["komoditas"] == seri for r in rows)]
    return KomoditasDetail(ticker=ticker, as_of=SNAPSHOT, items=[item(ticker, k) for k in jenis])
