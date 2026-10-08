"""'Artinya apa?' per kartu klaim: AI hanya menulis ulang fakta kartu, kode memeriksa hasilnya.  [Lane C]

Vonis, angka, dan data tetap dari kode. Tulisan AI dibuang kalau memuat angka di luar judul kartu,
arah, kode saham, atau vonis yang tidak ada di kartu, atau berbau saran investasi. Gagal apa pun ->
kosong, dan FE cukup menampilkan kalimat kode.
"""
from __future__ import annotations

import json
import re

from ..catalog import catalog
from ..checkers.base import angka_id, persen_id, rp_kata
from ..schemas import Card, CekResponse, Evidence, RingkasItem, RingkasResponse
from . import guard
from .provider import get_llm

VONIS = {"sesuai": "Sesuai data", "menyesatkan": "Menyesatkan", "tidak_sesuai": "Tidak sesuai",
         "tidak_bisa_dicek": "Tidak bisa dicek", "info": "Info (konteks, bukan penilaian)"}
PANJANG_MIN, PANJANG_MAKS = 20, 300
# Kata yang hanya boleh dipakai AI kalau kartunya sendiri memakainya: arah (supaya "naik" tidak
# dibalik jadi "turun") dan kata berbau saran ("target" boleh kalau kartu menyebut target BEI).
_KATA_DARI_KARTU = ("naik", "turun", "masuk", "keluar", "untung", "rugi", "positif", "negatif", "berlawanan",
                    "searah", "sebaiknya", "saran", "target", "pasti", "dijamin", "cuan", "layak", "rekomendasi")
# Vonis lain yang tidak boleh muncul ("sesuai" sendiri tidak dicek: ia bagian dari "tidak sesuai").
_VONIS_LAIN = {"menyesatkan": "menyesatkan", "tidak_sesuai": "tidak sesuai", "tidak_bisa_dicek": "tidak bisa dicek"}
_ANGKA = re.compile(r"\d+(?:[.,]\d+)*")

PROMPT = """Kamu membantu investor pemula memahami hasil pemeriksaan klaim saham {ticker}.
Untuk setiap kartu di bawah, tulis "Artinya apa?": 1-2 kalimat bahasa Indonesia sehari-hari yang
menjelaskan maksud temuan itu, seperti menjelaskan ke teman yang baru belajar saham: bagian klaim
mana yang terbukti atau keliru, dan kenapa, dengan kata sederhana. Jangan sekadar mengulang judul kartu.

Aturan wajib:
- Pakai HANYA fakta di kartu itu. Jangan menambah fakta, sebab, istilah, atau konteks lain.
- Jangan menulis angka atau tanggal, kecuali yang tertulis di `judul` kartu itu (salin persis).
- Jangan mengubah vonis dan jangan menyebut vonis lain.
- Jangan memberi saran beli, jual, atau tahan, target harga, atau ramalan.
- Maksimal 220 karakter per kartu. Isi `kunci` sama persis dengan kunci kartunya.

Kartu:
{kartu}"""

SCHEMA = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": {
        "type": "object",
        "properties": {"kunci": {"type": "string"}, "teks": {"type": "string"}},
        "required": ["kunci", "teks"],
    }}},
    "required": ["items"],
}


def _nilai(e: Evidence) -> str:
    """Nilai bukti dalam format Indonesia, sama gaya dengan kalimat kartu."""
    v = e.value
    if v is None:
        return "tidak tersedia"
    if isinstance(v, str):
        return v
    if e.fmt == "pct":
        return persen_id(v)
    if e.fmt == "rp":
        return ("minus " if v < 0 else "") + rp_kata(v)
    if e.fmt == "int":
        return angka_id(v)
    return f"{v:g}".replace(".", ",")


def _label_cek(check: str | None) -> str:
    semua = catalog()["checks"] + catalog()["untold"]
    return next((c["label"] for c in semua if c["id"] == check), check or "")


def fakta(kunci: str, card: Card) -> dict:
    """Satu-satunya bahan yang dikirim ke AI untuk kartu ini."""
    return {"kunci": kunci, "pemeriksa": _label_cek(card.check), "vonis": VONIS[card.verdict],
            "judul": card.headline, "penjelasan": card.reason,
            "angka": [f"{e.label}: {_nilai(e)}" for e in card.evidence]}


def _angka(teks: str) -> set[float]:
    """Semua angka dalam teks sebagai nilai: '14.650' = 14650, '22,4' = 22.4, '2025-09-26' = 2025, 9, 26."""
    hasil = set()
    for t in _ANGKA.findall(teks):
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
            n = float(t.replace(".", ""))
        elif "," in t:
            n = float(t.replace(".", "").replace(",", "."))
        else:
            n = float(t)
        hasil.add(round(n, 6))
    return hasil


def rapikan(teks: str, judul: str) -> str:
    """Model kadang menyalin label "Artinya apa?" dan judul kartu di depan; keduanya sudah tampil di kartu."""
    teks = re.sub(r"^\s*artinya apa\s*\??\s*[:\-–]?\s*", "", teks.strip(), flags=re.IGNORECASE)
    return teks[len(judul):].strip() if teks.startswith(judul) else teks


def periksa(teks: str, bahan: dict, verdict: str, ticker: str) -> bool:
    """True kalau tulisan AI aman dipakai untuk kartu dengan fakta `bahan` dan vonis `verdict`."""
    sumber = json.dumps(bahan, ensure_ascii=False) + " " + ticker
    kecil, sumber_kecil = teks.lower(), sumber.lower()
    # Angka hanya boleh dari judul: angka asli dari bagian lain kartu bisa dirangkai AI jadi fakta salah
    # (mis. tanggal akhir periode tertukar dengan tanggal kuartal lain).
    return (PANJANG_MIN <= len(teks) <= PANJANG_MAKS
            and _angka(teks) <= _angka(bahan["judul"])
            and all(kata in sumber_kecil for kata in _KATA_DARI_KARTU if kata in kecil)
            and not any(frasa in kecil for v, frasa in _VONIS_LAIN.items() if v != verdict)
            and set(re.findall(r"\b[A-Z]{4}\b", teks)) <= set(re.findall(r"\b[A-Z]{4}\b", sumber))
            and not guard.minta_saran(teks))


def _kartu(cek: CekResponse) -> dict[str, Card]:
    """Hanya kartu klaim (kunci = claim_id, sama dengan /api/tanya): di sanalah pembaca butuh "artinya".
    Kartu "Yang tidak diceritakan" sudah berupa catatan singkat, dan tiap kartu tambahan memperlambat
    jawaban AI. Prediksi (tidak bisa dicek) tidak perlu ditulis ulang."""
    return {c.claim_id: c for c in cek.claims if c.claim_id and c.verdict != "tidak_bisa_dicek"}


def ringkas(cek: CekResponse, llm=None) -> RingkasResponse:
    kartu = _kartu(cek)
    if not kartu:
        return RingkasResponse(items=[])
    bahan = {k: fakta(k, c) for k, c in kartu.items()}
    prompt = PROMPT.format(ticker=cek.ticker, kartu=json.dumps(list(bahan.values()), ensure_ascii=False, indent=1))
    try:
        mentah = (llm or get_llm()).minta_json(prompt, SCHEMA)
    except Exception:
        # Tanpa kunci, penyedia tanpa minta_json, galat jaringan, atau JSON rusak: tanpa ringkasan.
        return RingkasResponse(items=[])
    items: dict[str, RingkasItem] = {}
    for item in mentah.get("items", []) if isinstance(mentah, dict) else []:
        kunci, teks = (item.get("kunci"), item.get("teks")) if isinstance(item, dict) else (None, None)
        if kunci not in bahan or kunci in items or not isinstance(teks, str):
            continue
        teks = rapikan(teks, bahan[kunci]["judul"])
        if periksa(teks, bahan[kunci], kartu[kunci].verdict, cek.ticker):
            items[kunci] = RingkasItem(kunci=kunci, teks=teks)
    return RingkasResponse(items=list(items.values()), used_ai=True)
