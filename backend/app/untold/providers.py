"""Kartu konteks dari CSV Sectors dan snapshot BEI, tanpa AI. [Lane D]"""
from datetime import date, timedelta
import json
from typing import Callable

from ..catalog import param
from ..checkers.analis import kartu_analis
from ..checkers.base import card
from ..checkers.pemegang import kartu_pemegang
from ..data import bahan, normal
from ..data.sectors import DataUnavailable
from ..modul import komoditas
from ..schemas import Card, Claim, Evidence, Source

SNAPSHOT = "2026-09-30"
Provider = Callable[[str, list[Claim], date], Card | None]


def papan_pemantauan(ticker: str, claims: list[Claim], today: date | None = None) -> Card | None:
    today = today or date.today()
    rows = [r for r in bahan.baris("papan_pemantauan_khusus", ticker)
            if date.fromisoformat(r["tanggal_masuk"]) <= today]
    if not rows:
        return None
    r = max(rows, key=lambda r: r["tanggal_masuk"])
    kriteria = {k["kriteria"]: k for k in bahan.baca("papan_pemantauan_kriteria")}
    detail = []
    for nomor in r["kriteria"].split(","):
        k = kriteria.get(nomor.strip())
        if k is None:
            raise DataUnavailable("Arti kriteria pemantauan tidak tersedia")
        detail.append(f"Kriteria {nomor.strip()}: {k['keterangan']} ({k['status']}).")
    aktif = r["aktif"] == "ya"
    return card(verdict="info", check="papan_pemantauan",
                headline="Tercatat di Papan Pemantauan Khusus pada snapshot." if aktif else "Pernah masuk Papan Pemantauan Khusus.",
                reason=" ".join(detail) + " Snapshot hanya memuat satu episode per emiten, bukan seluruh riwayat; status bukan pembaruan langsung.",
                evidence=[Evidence(label="Tanggal masuk", value=r["tanggal_masuk"], fmt="text"),
                          Evidence(label="Tanggal keluar", value=r["tanggal_keluar"] or "belum tercatat", fmt="text"),
                          Evidence(label="Status snapshot", value="aktif" if aktif else "sudah keluar", fmt="text")],
                sources=[Source(name="BEI · Papan Pemantauan Khusus (unduh manual)", as_of=SNAPSHOT)])


def segmen(ticker: str, claims: list[Claim], today: date | None = None) -> Card | None:
    if not any(komoditas.komoditas_disebut(c.text) for c in claims) or any("m_komoditas" in c.checks for c in claims):
        return None
    jenis, porsi = komoditas.komoditas_terbesar(ticker)
    return card(verdict="info", check="segmen", headline=f"Sumber pendapatan terbesar: {jenis} ({porsi:.0%}).",
                reason="Pemetaan segmen berasal dari data pendapatan Sectors. Segmen campuran tidak dianggap murni satu komoditas.",
                evidence=[Evidence(label=jenis, value=porsi, fmt="pct")], sources=[komoditas.sumber_segmen(ticker)])


def analis(ticker: str, claims: list[Claim], today: date | None = None) -> Card | None:
    if not any("analis" in c.checks for c in claims):
        return None
    return kartu_analis(ticker)


def pemegang(ticker: str, claims: list[Claim], today: date | None = None) -> Card | None:
    if any("pemegang" in c.checks for c in claims) or not any("asing" in c.checks for c in claims):
        return None
    return kartu_pemegang(ticker, today=today)


def aturan_c1(tanggal: date, today: date) -> bool:
    return today <= tanggal <= today + timedelta(days=param("C-1", "jendela_hari"))


def aksi_korporasi(ticker: str, claims: list[Claim], today: date | None = None) -> Card | None:
    today = today or date.today()
    akhir = today + timedelta(days=param("C-1", "jendela_hari"))
    rows = sorted((r for r in bahan.baris("kalender_aksi_korporasi", ticker)
                   if aturan_c1(date.fromisoformat(r["tanggal"]), today)), key=lambda r: r["tanggal"])
    if not rows:
        return None
    ev = []
    src = [Source(name="Sectors · corporate actions · snapshot kalender", as_of=SNAPSHOT)]
    for r in rows:
        ev.append(Evidence(label=f"Tanggal ex {r['jenis']}", value=r["tanggal"], fmt="text"))
        if r["jenis"] == "right_issue":
            try:
                detail = json.loads(r["detail_json"])
            except (ValueError, TypeError) as e:
                raise DataUnavailable("Detail aksi korporasi tidak sesuai") from e
            harga = bahan.wajib(detail, "price")
            ev.append(Evidence(label="Harga pelaksanaan right issue", value=harga, fmt="rp"))
            for kolom, label in (("old_ratio", "Saham lama"), ("new_ratio", "Saham baru")):
                ev.append(Evidence(label=label, value=bahan.wajib(detail, kolom), fmt="num"))
            try:
                harga_harian = [h for h in normal.harga_harian(ticker) if h.tanggal <= today]
                if harga_harian:
                    terbaru = max(harga_harian, key=lambda h: h.tanggal)
                    ev.append(Evidence(label="Harga penutupan pembanding", value=terbaru.close, fmt="rp"))
                    src.append(Source(name="Sectors · harga harian pembanding", as_of=str(terbaru.tanggal)))
            except DataUnavailable:
                pass
    return card(verdict="info", check="aksi_korporasi", rule_id="C-1",
                headline="Ada aksi korporasi mendatang dalam jendela pemeriksaan.",
                reason=f"Jendela {today}–{akhir}. Kalender adalah snapshot {SNAPSHOT}; jadwal dapat berubah. Perbandingan harga bukan saran transaksi.",
                evidence=ev, sources=src)


def aturan_q1(nilai: list[float]) -> tuple[bool, float]:
    n = param("Q-1", "jendela_hari_bursa")
    if len(nilai) < n:
        raise DataUnavailable("Observasi likuiditas tidak cukup")
    rata = sum(nilai[-n:]) / n
    return rata < param("Q-1", "batas_nilai_harian_rp"), rata


def likuiditas(ticker: str, claims: list[Claim], today: date | None = None) -> Card | None:
    today = today or date.today()
    n = param("Q-1", "jendela_hari_bursa")
    harga = sorted((h for h in normal.harga_harian(ticker) if h.tanggal <= today), key=lambda h: h.tanggal)[-n:]
    if any(h.nilai_transaksi_rp is None for h in harga):
        raise DataUnavailable("Volume untuk likuiditas tidak lengkap")
    rendah, rata = aturan_q1([h.nilai_transaksi_rp for h in harga])
    if not rendah:
        return None
    return card(verdict="info", check="likuiditas", rule_id="Q-1", headline="Perkiraan nilai transaksi harian rendah.",
                reason=f"Dihitung dari close × volume pada {n} hari bursa ({harga[0].tanggal}–{harga[-1].tanggal}); bukan nilai transaksi aktual atau perkiraan kemampuan menjual.",
                evidence=[Evidence(label=f"Rata-rata perkiraan nilai transaksi {n} hari", value=rata, fmt="rp")],
                sources=[Source(name="Sectors · harga harian dan volume", as_of=str(harga[-1].tanggal))])


PROVIDERS: dict[str, Provider] = {
    "papan_pemantauan": papan_pemantauan, "segmen": segmen, "analis": analis,
    "pemegang": pemegang, "aksi_korporasi": aksi_korporasi, "likuiditas": likuiditas,
}
