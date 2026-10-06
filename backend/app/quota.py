"""Kuota 5 cek/hari per perangkat (header X-Device-Id), tanpa login.
Disimpan di memori proses: reset kalau server restart. Cukup untuk hackathon."""
from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

from .catalog import catalog
from .schemas import Quota

WIB = timezone(timedelta(hours=7))
_lock = threading.Lock()
_pakai: dict[tuple[str, str], int] = {}


def _hari_ini() -> datetime:
    return datetime.now(WIB).replace(hour=0, minute=0, second=0, microsecond=0)


def status(device: str) -> Quota:
    h = _hari_ini()
    return Quota(used=_pakai.get((device, h.date().isoformat()), 0), limit=catalog()["quota"]["cek_per_hari"],
                 reset_at=(h + timedelta(days=1)).isoformat())


def pakai(device: str) -> Quota | None:
    """Catat satu cek. None = kuota habis."""
    with _lock:
        q = status(device)
        if q.used >= q.limit:
            return None
        _pakai[(device, _hari_ini().date().isoformat())] = q.used + 1
        return status(device)
