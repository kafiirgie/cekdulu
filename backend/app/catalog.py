"""Membaca contract/rules.json — satu-satunya tempat ambang aturan disimpan."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from .config import settings


@lru_cache
def catalog() -> dict[str, Any]:
    return json.loads((settings.contract_dir / "rules.json").read_text(encoding="utf-8"))


def rule(rule_id: str) -> dict[str, Any]:
    for r in catalog()["rules"]:
        if r["id"] == rule_id:
            return r
    raise KeyError(f"Aturan {rule_id} tidak ada di contract/rules.json")


def param(rule_id: str, name: str) -> Any:
    return rule(rule_id)["params"][name]


def standard_checks() -> list[dict[str, Any]]:
    return [c for c in catalog()["checks"] if c["standar"]]


def check_label(check_id: str) -> str:
    for c in catalog()["checks"] + catalog()["untold"]:
        if c["id"] == check_id:
            return c.get("step_label") or c["label"]
    return check_id


def known_ids() -> set[str]:
    cat = catalog()
    return {c["id"] for c in cat["checks"]} | {u["id"] for u in cat["untold"]}
