"""Pemeriksa 6 — Lonjakan harga. Aturan H-1, H-2.  [Lane B]"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..catalog import param
from ..data import normal
from ..schemas import Claim, Evidence, Source
from .base import Checker, Outcome, angka_rupiah, card, persen_id, rp, tanggal_id


def aturan_h1(harga: list[normal.HargaHarian], tanggal_aksi: set[date]) -> Optional[tuple[date, float]]:
    """Cari perubahan terbesar dalam jendela 21 hari bursa.

    Harga Sectors tidak disesuaikan aksi korporasi (ADRO −25% saat ex-dividen),
    jadi return harian pada tanggal aksi korporasi dianggap 0.
    Mengembalikan (tanggal_akhir_jendela, perubahan) jika |perubahan| > batas, else None.
    """
    batas = param("H-1", "batas_perubahan")
    n = param("H-1", "jendela_hari_bursa")
    h = sorted(harga, key=lambda x: x.tanggal)
    if len(h) <= n:
        return None
    ret = [1.0]
    for prev, cur in zip(h, h[1:]):
        ret.append(1.0 if cur.tanggal in tanggal_aksi or prev.close <= 0 else cur.close / prev.close)
    terbesar: Optional[tuple[date, float]] = None
    for i in range(n, len(h)):
        faktor = 1.0
        for r in ret[i - n + 1 : i + 1]:
            faktor *= r
        ubah = faktor - 1
        if abs(ubah) > batas and (terbesar is None or abs(ubah) > abs(terbesar[1])):
            terbesar = (h[i].tanggal, ubah)
    return terbesar


def aturan_h2(klaim_dari: float, klaim_ke: float, harga_jendela: list[float], terakhir: float) -> bool:
    """Harga awal pernah tercatat dalam jendela; harga akhir dibandingkan catatan terbaru."""
    tol = param("H-2", "toleransi_relatif")
    return (klaim_dari > 0 and klaim_ke > 0
            and any(abs(h - klaim_dari) <= tol * klaim_dari for h in harga_jendela)
            and abs(terakhir - klaim_ke) <= tol * klaim_ke)


def _kalimat_h2(dari: float, ke: float, awal: normal.HargaHarian, akhir: normal.HargaHarian,
                mulai: date, ok: bool) -> tuple[str, str]:
    """Judul + penjelasan klaim "dari A ke B"; kalau tidak sesuai, sebut bagian mana yang meleset."""
    tol = param("H-2", "toleransi_relatif")
    jendela = f"Data yang dicek: {mulai}–{akhir.tanggal}; kelonggaran {persen_id(tol, 0)} untuk tiap harga."
    if ok:
        return (f"Harga {rp(awal.close)} memang pernah tercatat, dan harga terakhirnya {rp(akhir.close)}.",
                f"Harga penutupan {rp(awal.close)} tercatat pada {awal.tanggal}. Harga penutupan terakhir {rp(akhir.close)} "
                f"pada {akhir.tanggal}, dekat dengan {rp(ke)} yang disebut di klaim. {jendela}")
    if abs(awal.close - dari) > tol * dari:
        return (f"Harga {rp(dari)} tidak pernah tercatat di data kami.",
                f"Harga penutupan yang paling dekat adalah {rp(awal.close)} pada {awal.tanggal}. {jendela}")
    return (f"Harga terakhirnya {rp(akhir.close)}, jauh dari {rp(ke)} yang disebut di klaim.",
            f"Harga {rp(awal.close)} memang tercatat pada {awal.tanggal}, tapi harga penutupan terakhir pada "
            f"{akhir.tanggal} berbeda lebih dari {persen_id(tol, 0)} dari klaim. {jendela}")


class LonjakanHarga(Checker):
    id = "lonjakan_harga"

    def run(self, ticker: str, claim: Optional[Claim], today: date) -> Outcome:
        harga = normal.harga_harian(ticker)
        src = [Source(name="Sectors · harga harian", as_of=str(max(x.tanggal for x in harga)))]

        if claim is not None:
            angka = angka_rupiah(claim.text)
            if len(angka) >= 2:
                awal = min(harga, key=lambda x: abs(x.close - angka[0]))
                akhir = max(harga, key=lambda x: x.tanggal)
                ok = aturan_h2(angka[0], angka[1], [x.close for x in harga], akhir.close)
                headline, reason = _kalimat_h2(angka[0], angka[1], awal, akhir, min(x.tanggal for x in harga), ok)
                return Outcome(
                    status="temuan" if ok else "aman",
                    why="Klaim harga dibandingkan dengan harga tercatat.",
                    card=card(
                        verdict="sesuai" if ok else "tidak_sesuai", check=self.id, rule_id="H-2", claim=claim,
                        headline=headline, reason=reason,
                        evidence=[Evidence(label="Harga awal terdekat tercatat", value=awal.close, fmt="rp"),
                                  Evidence(label="Harga terakhir", value=akhir.close, fmt="rp")],
                        sources=[Source(name="Sectors · harga harian · harga awal", as_of=str(awal.tanggal)),
                                 Source(name="Sectors · harga harian · harga terakhir", as_of=str(akhir.tanggal))],
                    ),
                )

        hasil = aturan_h1(harga, normal.tanggal_aksi_korporasi(ticker))
        if hasil is None:
            return Outcome("aman", "Tidak ada perubahan >25% dalam 21 hari bursa (setelah memperhitungkan aksi korporasi).")
        tgl, ubah = hasil
        n = param("H-1", "jendela_hari_bursa")
        teks = f"Harga pernah {'naik' if ubah > 0 else 'turun'} {persen_id(abs(ubah), 0)} hanya dalam {n} hari bursa (sekitar sebulan), sampai {tanggal_id(tgl)}."
        alasan = (f"Kami mencatat setiap perubahan harga lebih dari {persen_id(param('H-1', 'batas_perubahan'), 0)} dalam {n} hari bursa. "
                  "Lompatan di hari pembagian dividen, pemecahan saham, atau right issue tidak ikut dihitung.")
        return Outcome(
            "temuan", teks,
            card(verdict="info", check=self.id, rule_id="H-1", headline=teks, reason=alasan,
                 evidence=[Evidence(label=f"Perubahan {n} hari bursa", value=ubah, fmt="pct")], sources=src),
        )
