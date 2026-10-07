"""Validasi deterministik agar jawaban Tanya tidak menambah angka di luar kartu."""
from __future__ import annotations

import re
from typing import Iterable

from ..schemas import Card, Evidence

POLA_ANGKA = re.compile(
    r"(?<![\w])(?:Rp\s*)?[−-]?\d+(?:[.,]\d+)*(?:\s?(?:%|[x×]|[KkMmTt]))?",
    re.IGNORECASE,
)


def _normal(teks: str) -> str:
    return teks.replace(" ", "").replace("−", "-").lower()


def ambil_angka(teks: str) -> set[str]:
    return {_normal(m.group(0)) for m in POLA_ANGKA.finditer(teks)}


def _id(nilai: float, desimal: int) -> str:
    teks = f"{nilai:,.{desimal}f}"
    if desimal:
        teks = teks.rstrip("0").rstrip(".")
    return teks.replace(",", "_").replace(".", ",").replace("_", ".")


def _varian_bukti(bukti: Evidence) -> Iterable[str]:
    nilai = bukti.value
    if isinstance(nilai, bool) or not isinstance(nilai, (int, float)):
        yield str(nilai)
        return

    mentah = format(nilai, ".15g")
    yield mentah
    yield mentah.replace(".", ",")

    if bukti.fmt == "pct":
        persen = nilai * 100
        yield _id(persen, 1)
        yield f"{_id(persen, 1)}%"
        yield f"{persen:.1f}%"
    elif bukti.fmt == "rp":
        yield _id(nilai, 0)
        yield f"Rp{_id(nilai, 0)}"
        if abs(nilai) >= 1e12:
            yield f"{_id(nilai / 1e12, 2)} T"
            yield f"Rp{_id(nilai / 1e12, 2)} T"
        elif abs(nilai) >= 1e9:
            yield f"{_id(nilai / 1e9, 1)} M"
            yield f"Rp{_id(nilai / 1e9, 1)} M"
    elif bukti.fmt == "int":
        yield _id(nilai, 0)
    elif bukti.fmt == "x":
        yield _id(nilai, 1)
        yield f"{_id(nilai, 1)}x"
        yield f"{_id(nilai, 1)}×"
    elif bukti.fmt == "num":
        yield _id(nilai, 2)


def angka_di_kartu(card: Card) -> set[str]:
    teks_kartu = [card.headline, card.reason, card.rule_text or ""]
    teks_kartu.extend(f"{e.label} {e.value}" for e in card.evidence)
    teks_kartu.extend(f"{s.name} {s.as_of or ''}" for s in card.sources)
    diizinkan = ambil_angka(" ".join(teks_kartu))
    for bukti in card.evidence:
        for varian in _varian_bukti(bukti):
            diizinkan.update(ambil_angka(varian))
    return diizinkan


def jawaban_berdasarkan_kartu(card: Card, jawaban: str) -> bool:
    """Benar hanya bila setiap angka jawaban tersedia dalam salah satu format kartu."""
    return ambil_angka(jawaban) <= angka_di_kartu(card)
