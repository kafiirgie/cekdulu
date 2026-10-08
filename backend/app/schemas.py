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
    # Teks yang dibaca AI dari screenshot; span klaim menunjuk ke teks ini. None untuk input teks.
    source_text: Optional[str] = None


# ---------- /api/cek ----------
class CekRequest(_Model):
    ticker: str
    claims: list[Claim] = Field(default_factory=list)  # kosong = "cek umum" (kode saham saja)


class Evidence(_Model):
    label: str
    value: Any
    fmt: Fmt = "num"


class ChartSeries(_Model):
    name: str
    points: list[tuple[str, float]]  # (label: tanggal ISO atau nama kategori, nilai mentah)
    fmt: Fmt = "num"


class Chart(_Model):
    type: Literal["line", "bar"]
    series: list[ChartSeries]


class Source(_Model):
    name: str
    as_of: Optional[str] = None


class Card(_Model):
    # A-3: konflik memakai rule_id A-3; periode/keterbatasan di reason, sumber per dataset yang tersedia.
    # H-2: harga awal yang paling dekat dan harga terakhir di evidence, masing-masing bertanggal di sources.
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


# Nilai `bagian` ditentukan kode (JEV), bukan LLM bebas: FE memakainya untuk memilih label kecil.
BagianJawaban = Literal["angka_bukti", "alasan_aturan", "sumber_tanggal", "istilah", "di_luar_kartu"]


class TanyaResponse(_Model):
    answer: str
    refused: bool
    used_ai: bool = False  # True = jawaban lewat klasifikasi JEV; False = template kode
    # Bagian kartu yang dipakai menjawab: angka, aturan, sumber, istilah, saran (penolakan),
    # ringkasan (kode menjawab tanpa klasifikasi JEV), tidak_ada.
    answer_kind: Optional[Literal["angka", "aturan", "sumber", "istilah", "saran", "ringkasan",
                                  "tidak_ada"]] = None
    # Hanya diisi kalau jawaban diklasifikasi JEV; None saat fallback/penolakan.
    bagian: Optional[BagianJawaban] = None


# ---------- /api/ringkas ----------
class RingkasRequest(_Model):
    cek_id: str


class RingkasItem(_Model):
    kunci: str  # sama dengan TanyaRequest.card: claim_id, atau u0, u1, … untuk "Yang tidak diceritakan"
    teks: str


class RingkasResponse(_Model):
    # "Artinya apa?" per kartu: AI menulis ulang fakta kartu, kode memeriksa angka, arah, dan vonisnya.
    # Kartu yang tidak lolos tidak ikut; FE tetap menampilkan kalimat kode saja.
    items: list[RingkasItem]
    used_ai: bool = False


# ---------- /api/rules ----------
class GlosariumItem(_Model):
    key: str
    nama: str
    arti: str


class GlosariumPemetaan(_Model):
    checks: dict[str, str] = Field(default_factory=dict)
    untold: dict[str, str] = Field(default_factory=dict)


class Glosarium(_Model):
    versi: str
    pemetaan: GlosariumPemetaan
    istilah: list[GlosariumItem]




# Harus sama dengan frontend/src/lib/contract.ts → KunciGlosarium dan kunci di contract/glosarium.json.
GlosariumKey = Literal[
    "laba", "per", "pbv", "dividen", "yield", "payout", "orang_dalam", "asing", "suspensi",
    "free_float", "hari_serap", "korelasi", "kapitalisasi", "papan_pemantauan",
]


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


class KomoditasItem(_Model):
    ticker: str
    komoditas: str
    porsi_pendapatan: Optional[float] = None
    komoditas_terbesar: Optional[str] = None
    porsi_terbesar: Optional[float] = None
    tahun_buku: Optional[int] = None
    korelasi: float
    kategori: Literal["lemah", "sedang", "cukup kuat"]
    periode: str
    n_bulan: int
    total_return_saham: Optional[float] = None
    perubahan_komoditas: Optional[float] = None
    arah_tahunan: list[str]
    sources: list[Source]


class KomoditasList(_Model):
    as_of: str
    jenis: str
    items: list[KomoditasItem]


class KomoditasDetail(_Model):
    ticker: str
    as_of: str
    items: list[KomoditasItem]
