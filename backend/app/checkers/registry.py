"""Daftar pemeriksa. Urutan 8 standar SELALU sama untuk semua saham (dari rules.json)."""
from __future__ import annotations

from .asing import Asing
from .analis import Analis
from .pemegang import Pemegang
from .base import Checker
from .dividen import Dividen
from .free_float import FreeFloat
from .laba import Laba
from .lonjakan_harga import LonjakanHarga
from .m_komoditas import MKomoditas
from .orang_dalam import OrangDalam
from .suspensi import Suspensi
from .valuasi import Valuasi

CHECKERS: dict[str, Checker] = {c.id: c for c in [
    Laba(), Valuasi(), Dividen(), OrangDalam(), Asing(), LonjakanHarga(), Suspensi(), FreeFloat(),
    MKomoditas(), Analis(), Pemegang(),
]}
