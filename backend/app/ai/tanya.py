"""Penjawab Tanya DETERMINISTIK. Angka, kalimat, dan pilihan data disusun kode.  [Lane C]

JEV hanya memilih bagian kartu yang relevan (dan istilah mana yang ditanya); teks
jawabannya dirakit di sini dari field kartu. Jadi tidak ada angka karangan dan tidak
ada jawaban bebas-teks yang bisa melenceng.

Format angka & tanggal disamakan dengan frontend/src/lib/format.ts; salinannya kecil
dan dijaga tes supaya tidak berbeda (jawaban lewat curl pun enak dibaca).
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from ..catalog import glosarium
from ..schemas import Card, Evidence
from . import guard
from .jev import ambang, get_jev, istilah_card, minta_saran_jev, pilih_bagian, pilih_istilah, yakin

BULAN = ("Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des")


def _id(n: float, maks_desimal: int = 0) -> str:
    """Angka gaya Indonesia: 14650 → "14.650", 82.5 → "82,5", 2.0 → "2"."""
    teks = f"{n:,.{maks_desimal}f}"
    if "." in teks:
        teks = teks.rstrip("0").rstrip(".")
    # Tukar pemisah: koma ribuan → titik, titik desimal → koma.
    return teks.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def rupiah(n: float) -> str:
    """"14650 → "Rp14.650"; 9.35e12 → "Rp9,35 T" (sama dengan format.ts)."""
    a = abs(n)
    if a >= 1e12:
        return f"Rp{_id(n / 1e12, 2)} T"
    if a >= 1e9:
        return f"Rp{_id(n / 1e9, 1)} M"
    return f"Rp{_id(n)}"


def tanggal(teks: str) -> str:
    """"2026-09-30" → "30 Sep 2026"; selain tanggal lengkap dikembalikan apa adanya."""
    bagian = teks.split("-")
    if len(bagian) != 3 or len(bagian[0]) != 4 or not bagian[0].isdigit():
        return teks
    try:
        d = date(int(bagian[0]), int(bagian[1]), int(bagian[2][:2]))
    except ValueError:
        return teks
    return f"{d.day} {BULAN[d.month - 1]} {d.year}"


def _nilai(bukti: Evidence) -> str:
    """Format satu angka bukti sesuai `fmt` — sama gaya dengan tabel di layar."""
    v = bukti.value
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return str(v)
    if bukti.fmt == "pct":
        return f"{_id(v * 100, 1)}%"
    if bukti.fmt == "rp":
        return rupiah(v)
    if bukti.fmt == "int":
        return _id(v)
    if bukti.fmt == "x":
        return f"{_id(v, 1)}×"
    return _id(v, 2)


def _angka(card: Card) -> str:
    if not card.evidence:
        return "Kartu ini tidak memuat angka tambahan."
    baris = "; ".join(f"{e.label}: {_nilai(e)}" for e in card.evidence)
    return f"Angka di kartu ini — {baris}."


def _aturan(card: Card) -> Optional[str]:
    if card.rule_id and card.rule_text:
        return f"Aturan {card.rule_id}: {card.rule_text}"
    if card.rule_id:
        return f"Kartu ini memakai aturan {card.rule_id}."
    if card.rule_text:
        return f"Aturan yang dipakai: {card.rule_text}"
    return None


def _sumber(card: Card) -> str:
    if not card.sources:
        return "Kartu ini tidak punya sumber karena isinya vonis \"tidak bisa dicek\"."
    baris = "; ".join(f"{s.name} ({tanggal(s.as_of)})" if s.as_of else s.name for s in card.sources)
    return f"Sumber kartu ini — {baris}."


def _tak_ada() -> str:
    return ("Maaf, data ini tidak ada di kartu. Coba tanyakan angka, aturan, atau sumber "
            "yang tampak di kartu ini.")


def _ringkasan(card: Card) -> str:
    """Jawaban kode tanpa klasifikasi JEV: angka + aturan + sumber sekaligus.

    Dipakai saat JEV mati/gagal. Tetap sepenuhnya dari field kartu, jadi tidak ada
    angka karangan, dan menjawab pertanyaan angka maupun sumber.
    """
    bagian = [_angka(card)]
    aturan = _aturan(card)
    if aturan:
        bagian.append(aturan)
    bagian.append(_sumber(card))
    return " ".join(bagian)


def jawab(card: Card, bagian: str, glos: Optional[dict[str, str]] = None) -> str:
    """Rakit jawaban dari field kartu. `bagian` sudah dipilih kode (dari JEV)."""
    if bagian == "angka":
        return _angka(card)
    if bagian == "aturan":
        return _aturan(card) or _tak_ada()
    if bagian == "sumber":
        return _sumber(card)
    if bagian == "istilah" and glos:
        return f"{glos['nama']}: {glos['arti']}"
    if bagian == "ringkasan":
        return _ringkasan(card)
    return _tak_ada()


def peta_bagian(bagian_jev: Optional[str]) -> str:
    """Label JEV → bagian internal. di_luar_kartu dan None → tidak ada di kartu."""
    return {
        "angka_bukti": "angka",
        "alasan_aturan": "aturan",
        "sumber_tanggal": "sumber",
        "istilah": "istilah",
    }.get(bagian_jev or "", "tidak_ada")


def _glosarium_untuk(card: Card, jawaban_jev: dict) -> Optional[dict[str, str]]:
    """Istilah yang ditanya (dari JEV), kalau tidak masuk akal pakai istilah utama kartu."""
    by_key = {i["key"]: i for i in glosarium()["istilah"]}
    kunci = pilih_istilah(jawaban_jev) or istilah_card(card)
    return by_key.get(kunci or "")


def _ditolak(question: str, jev: Any | None) -> bool:
    """Regex dulu (cepat, offline, deterministik); JEV jadi pengaman kedua kalau regex lolos.

    Hasil ukur JEV menandai "berapa PER wajar saham ini?" (0,51) yang lolos dari regex.
    JEV di sini HANYA menolak, tidak pernah mengizinkan; kalau JEV mati/gagal, hasil regex
    yang dipakai (tanpa panggilan jaringan).
    """
    if guard.minta_saran(question):
        return True
    if jev is None:
        return False
    return minta_saran_jev(jev, question)


def jawab_tanya(card: Card, question: str, jev: Any | None = None) -> dict:
    """Penjawab panel Tanya: JEV memilih bagian, kode merakit kalimatnya.

    Selalu mengembalikan bentuk lengkap, termasuk saat JEV mati/gagal (fallback kode)
    supaya /api/tanya tidak pernah 500. `jev` boleh disuntik (untuk tes dan endpoint).
    """
    if jev is None:
        try:
            jev = get_jev()
        except Exception:
            jev = None

    if _ditolak(question, jev):
        return {"answer": guard.PENOLAKAN, "refused": True, "used_ai": False,
                "answer_kind": "saran", "bagian": None}

    if jev is None:
        # Tanpa JEV: kode menjawab ringkas (angka + aturan + sumber), tanpa klasifikasi.
        return {"answer": jawab(card, "ringkasan"), "refused": False, "used_ai": False,
                "answer_kind": "ringkasan", "bagian": None}

    try:
        jawaban = jev.klasifikasi(card, question)
    except Exception:
        return {"answer": jawab(card, "ringkasan"), "refused": False, "used_ai": False,
                "answer_kind": "ringkasan", "bagian": None}

    bagian_jev = pilih_bagian(jawaban)
    bagian = peta_bagian(bagian_jev)
    if yakin(jawaban) < ambang():
        # Keluaran terlalu rendah untuk dipercaya: jangan pakai labelnya untuk memilih
        # jawaban, tapi `bagian` tetap melaporkan label mentah supaya bisa dilacak.
        bagian = "tidak_ada"
    glos = _glosarium_untuk(card, jawaban) if bagian == "istilah" else None
    return {"answer": jawab(card, bagian, glos), "refused": False, "used_ai": True,
            "answer_kind": bagian, "bagian": bagian_jev}
