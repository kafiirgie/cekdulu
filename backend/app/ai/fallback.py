"""Pemecah klaim TANPA AI — dipakai kalau LLM mati/kuota habis, dan sebagai tes dasar.  [Lane C]

Cara kerja: cari kode saham (4 huruf kapital), pecah teks per koma/titik/"dan",
lalu cocokkan kata kunci → pemeriksa. Kalimat prediksi → tanpa pemeriksa (tidak bisa dicek).
Versi LLM boleh lebih pintar, tapi HARUS mengembalikan bentuk yang sama.
"""
from __future__ import annotations

import re
from typing import Optional

from ..schemas import Claim, KlaimResponse

# kata kunci → pemeriksa. Urutan menentukan prioritas.
KATA_CEK: list[tuple[tuple[str, ...], str]] = [
    (("emas", "nikel", "batu bara", "batubara", "tembaga", "timah", "coal", "gold"), "m_komoditas"),
    (("laba", "untung", "profit", "rugi"), "laba"),
    (("per ", "pbv", "murah", "valuasi", "undervalue"), "valuasi"),
    (("dividen", "dividend", "yield"), "dividen"),
    (("asing", "foreign"), "asing"),
    (("orang dalam", "direksi", "komisaris", "pengendali", "insider"), "orang_dalam"),
    (("suspen", "suspensi", "digembok"), "suspensi"),
    (("free float", "freefloat"), "free_float"),
    # Kartu Lane D yang juga bisa memberi vonis klaim (TODO D3: buat Checker-nya)
    (("analis", "rekomendasi buy", "sekuritas"), "analis"),
    (("ritel", "diserbu", "pemegang saham", "ramai"), "pemegang"),
]
# Dipakai hanya kalau tidak ada pemeriksa lain yang cocok
KATA_HARGA = ("dari ", "naik", "turun", "anjlok", " ara", " arb", "kali lipat")
KATA_PREDIKSI = ("pasti", "bakal", "akan", "besok", "target", "to the moon", "terbang", "buruan", "otw", "auto")
# Kata yang menandakan klaim DATA walau ada kata prediksi ("dari 600 ke 14 ribu")
POLA_ANGKA = re.compile(r"\d")

PEMBUKA = {"kata grup", "katanya", "info", "guys", "bro", "min", "fyi", "buruan", "gas", "gaskeun", "cuy", "mantap"}
STOP_TICKER ={"ARA", "ARB", "IHSG", "BEI", "IDX", "OJK", "PER", "PBV", "ROE", "EPS", "WA", "CEO", "USD", "IDR"}
POLA_TICKER = re.compile(r"\b[A-Z]{4}\b")


def cari_ticker(teks: str) -> Optional[str]:
    for m in POLA_TICKER.finditer(teks):
        if m.group(0) not in STOP_TICKER:
            return m.group(0)
    return None


def _potong(teks: str) -> list[tuple[str, int, int]]:
    hasil, awal = [], 0
    for m in re.finditer(r"[,.;!?\n]| dan | tapi ", teks):
        bagian = teks[awal:m.start()]
        if bagian.strip():
            s = awal + len(bagian) - len(bagian.lstrip())
            hasil.append((bagian.strip(), s, s + len(bagian.strip())))
        awal = m.end()
    sisa = teks[awal:]
    if sisa.strip():
        s = awal + len(sisa) - len(sisa.lstrip())
        hasil.append((sisa.strip(), s, s + len(sisa.strip())))
    return hasil


def pilih_cek(kalimat: str) -> list[str]:
    t = " " + kalimat.lower() + " "
    ada_angka = bool(POLA_ANGKA.search(t))
    if any(k in t for k in KATA_PREDIKSI) and not ada_angka:
        return []  # prediksi → tidak bisa dicek
    cocok = [cid for kata, cid in KATA_CEK if any(k in t for k in kata)][:2]
    if not cocok and ada_angka and any(k in t for k in KATA_HARGA):
        cocok = ["lonjakan_harga"]
    return cocok


def pecah_klaim(teks: str, ticker: Optional[str] = None) -> KlaimResponse:
    ticker = (ticker or cari_ticker(teks) or "").upper() or None
    claims: list[Claim] = []
    for kalimat, s, e in _potong(teks):
        bersih = kalimat.replace(ticker, "").strip() if ticker else kalimat
        if len(bersih) < 3 or kalimat.lower() in PEMBUKA:
            continue
        claims.append(Claim(id=f"c{len(claims) + 1}", text=kalimat, span=(s, e), checks=pilih_cek(kalimat)))
    return KlaimResponse(ticker=ticker, company=None, claims=claims, used_ai=False)
