"""Model Pydantic = kontrak FE–BE. Harus sama dengan frontend/src/lib/contract.ts
dan contract/examples/*.json (dicek oleh tests/test_contract.py)."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Verdict = Literal["sesuai", "menyesatkan", "tidak_sesuai", "tidak_bisa_dicek", "info"]
FormStatus = Literal["temuan", "aman", "modul_aktif", "tidak_relevan", "data_kurang", "gagal"]
Fmt = Literal["pct", "rp", "int", "num", "x", "text"]


class _Model(BaseModel):
    # "_catatan" di contoh JSON diabaikan; field lain yang tak dikenal = error
    model_config = ConfigDict(extra="forbid")


class _Lenient(BaseModel):
    model_config = ConfigDict(extra="ignore")


# ---------- /api/klaim ----------
class KlaimRequest(_Model):
    text: Optional[str] = None
    image_base64: Optional[str] = None
    ticker: Optional[str] = None


class Claim(_Model):
    id: str
    text: str
    span: Optional[tuple[int, int]] = None  # posisi di teks asli, untuk stabilo
    checks: list[str] = Field(default_factory=list)  # kosong = tidak bisa dicek


class KlaimResponse(_Lenient):
    ticker: Optional[str]
    company: Optional[str] = None
    claims: list[Claim]
    used_ai: bool = False  # False = fallback heuristik


# ---------- /api/cek ----------
class CekRequest(_Model):
    ticker: str
    claims: list[Claim] = Field(default_factory=list)  # kosong = "cek umum" (kode saham saja)


class Evidence(_Model):
    label: str
    value: Any
    fmt: Fmt = "num"


class Chart(_Model):
    type: Literal["line", "bar"]
    series: list[dict[str, Any]]


class Source(_Model):
    name: str
    as_of: Optional[str] = None


class Card(_Model):
    claim_id: Optional[str] = None  # None untuk kartu "Yang tidak diceritakan"
    verdict: Verdict
    check: Optional[str] = None
    headline: str
    reason: str = ""
    rule_id: Optional[str] = None
    rule_text: Optional[str] = None
    evidence: list[Evidence] = Field(default_factory=list)
    chart: Optional[Chart] = None
    sources: list[Source] = Field(default_factory=list)


class Step(_Model):
    check: str
    label: str
    ms: int


class FormRow(_Model):
    check: str
    status: FormStatus
    why: str = ""


class Quota(_Model):
    used: int
    limit: int
    reset_at: str


class CekResponse(_Lenient):
    id: str
    ticker: str
    company: Optional[str] = None
    data_as_of: Optional[str] = None
    summary: str
    steps: list[Step]
    claims: list[Card]
    untold: list[Card]
    form: list[FormRow]
    quota: Optional[Quota] = None


# ---------- /api/tanya ----------
class TanyaRequest(_Model):
    cek_id: str
    card: str
    question: str


class TanyaResponse(_Model):
    answer: str
    refused: bool


# ---------- modul ----------
class FreeFloatItem(_Lenient):
    ticker: str
    company: Optional[str] = None
    free_float: float
    market_cap: float
    kelompok: str
    target: float
    tenggat: str
    nilai_dilepas: Optional[float] = None
    hari_serap: Optional[float] = None
    tekanan: Optional[Literal["ringan", "sedang", "berat"]] = None
    papan_pemantauan: bool = False


class FreeFloatList(_Lenient):
    as_of: Optional[str] = None
    items: list[FreeFloatItem]
