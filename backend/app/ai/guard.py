"""Penolakan pertanyaan saran investasi di panel Tanya. Regex dari contract/rules.json.  [Lane C]
Dicek SEBELUM pertanyaan dikirim ke LLM."""
from __future__ import annotations

import re
from functools import lru_cache

from ..catalog import catalog

PENOLAKAN = ("Kami tidak memberi saran beli, jual, atau tahan. "
             "Kami hanya bisa menjelaskan angka dan aturan di kartu ini.")


@lru_cache
def _pola() -> re.Pattern[str]:
    return re.compile(catalog()["tanya_tolak_regex"], re.IGNORECASE)


def minta_saran(pertanyaan: str) -> bool:
    return bool(_pola().search(pertanyaan))
