"""Klasifikasi TypeSafe (JEV) untuk panel Tanya.  [Lane C]

Peran model di sini HANYA memilih label dari daftar tertutup (bagian kartu mana yang
menjawab pertanyaan, dan apakah pengguna minta saran investasi). Angka, kalimat, dan
pilihan data tetap disusun kode di tanya.py. Jadi vonis tetap ditentukan kode, bukan
AI (AGENTS.md aturan 1).

Respons JEV terstruktur; kunci pertanyaan selalu ada walau model gagal, dan kalau
jawabannya tidak ada di kartu (`yakin` < ambang) kode menjawab jujur "tidak ada".
"""
from __future__ import annotations

import json
from typing import Any, Optional

import httpx

from ..catalog import glosarium
from ..config import settings
from ..schemas import Card

BATAS_WAKTU = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=2.0)

# Kunci pertanyaan untuk /systemone.
KUNCI_BAGIAN = "bagian"
KUNCI_ISTILAH = "istilah_key"
KUNCI_TAHU = "tahu"
KUNCI_SARAN = "minta_saran"
KUNCI_PREDIKSI = "prediksi"

# Ambang "sanity" untuk `noul`. Hasil pengukuran ke model sungguhan: `noul` bukan
# skor ketersediaan yang andal (pertanyaan yang jawabannya ADA pun bisa bernilai 0,15,
# sedangkan yang jelas di luar kartu 0,10). Karena itu label `bagian` yang dipakai
# sebagai penentu utama (`di_luar_kartu` = tidak ada di kartu); `noul` hanya menjadi
# lantai pengaman untuk menolak keluaran yang benar-benar kosong/rusak.
AMBANG_SANITY = 0.05

# Ambang `minta_saran`. Hasil ukur ke model sungguhan (5x per frasa, stabil):
# "masih bagus buat dibeli?" 0,89–0,91 · "harga wajarnya berapa?" 0,53–0,55 ·
# "kira-kira masih naik gak?" 0,72–0,74 vs kontrol "apa itu PBV?" 0,03 ·
# "berapa porsi nikelnya?" 0,08–0,09. Yang di tengah (0,2–0,3) dianggap bukan saran.
AMBANG_SARAN = 0.5

# Ambang `prediksi`: prediksi/opini tanpa angka terukur tidak boleh memilih pemeriksa.
# Hasil ukur: "momen bagus buat masuk, gaskeun" 0,91 dan "saya yakin cuan besar" 0,93
# (dua-duanya lolos dari heuristik kata kunci) vs "laba naik 20%" 0,02 · "yield 6%" 0,03.
AMBANG_PREDIKSI = 0.5

# Label bagian yang dikenal kode. FE memakai nama yang sama (BagianJawaban).
BAGIAN = ("angka_bukti", "alasan_aturan", "sumber_tanggal", "istilah", "di_luar_kartu")


def ambang() -> float:
    return AMBANG_SANITY


def _pemetaan() -> dict[str, str]:
    """checker id / kartu untold → kunci istilah. Untuk daftar pilihan istilah."""
    return {**glosarium()["pemetaan"]["checks"], **glosarium()["pemetaan"]["untold"]}


def istilah_card(card: Card) -> Optional[str]:
    """Kunci istilah utama kartu (dipakai saat istilah tidak disebut jelas)."""
    return _pemetaan().get(card.check or "")


def kriteria_istilah(card: Card) -> dict[str, str]:
    """Pilihan istilah: yang utama untuk kartu ini, plus seluruh glosarium."""
    by_key = {i["key"]: i["nama"] for i in glosarium()["istilah"]}
    utama = istilah_card(card)
    urut = [utama] + [k for k in by_key if k != utama] if utama else list(by_key)
    return {k: by_key[k] for k in urut if k}


def aturan_bagian(card: Card) -> dict[str, str]:
    """Deskripsi tiap label, diberi tahu model supaya pilihannya masuk akal."""
    return {
        "angka_bukti": "Pertanyaan tentang angka/bukti di kartu.",
        "alasan_aturan": "Pertanyaan kenapa begitu, aturan mana yang dipakai.",
        "sumber_tanggal": "Pertanyaan dari mana datanya atau tanggalnya.",
        "istilah": "Pertanyaan arti istilah/istilah teknis di kartu.",
        "di_luar_kartu": "Tidak berkaitan dengan kartu ini.",
    }


def state(card: Card, question: str) -> str:
    """Isi kartu + glosarium + pertanyaan, sebagai satu string JSON untuk `state`."""
    glos = glosarium()
    by_key = {i["key"]: i for i in glos["istilah"]}
    utama = istilah_card(card)
    isi: dict[str, Any] = {
        "headline": card.headline,
        "verdict": card.verdict,
        "reason": card.reason,
        "rule_id": card.rule_id,
        "rule_text": card.rule_text,
        "evidence": [e.model_dump() for e in card.evidence],
        "sources": [s.model_dump() for s in card.sources],
        "istilah": [by_key[utama]] if utama in by_key else [],
        "pertanyaan": question,
    }
    return json.dumps(isi, ensure_ascii=False)


class Jev:
    """Pemanggil /systemone. Sekali panggil, tiga jawaban terstruktur."""

    def __init__(self, base_url: str, api_key: str, model: str):
        if not base_url:
            raise ValueError("JEV_BASE_URL belum diisi")
        if not api_key:
            raise ValueError("JEV_API_KEY belum diisi")
        if not model:
            raise ValueError("JEV_MODEL belum diisi")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def klasifikasi(self, card: Card, question: str) -> dict[str, Any]:
        body = {
            "state": state(card, question),
            "model": self.model,
            "questions": {
                KUNCI_BAGIAN: {
                    "type": "choice",
                    "instructions": "Bagian kartu mana yang menjawab pertanyaan pengguna?",
                    "criteria": aturan_bagian(card),
                },
                KUNCI_ISTILAH: {
                    "type": "choice",
                    "instructions": "Istilah mana yang ditanyakan pengguna?",
                    "criteria": kriteria_istilah(card),
                },
                KUNCI_TAHU: {
                    "type": "noul",
                    "instructions": "Apakah jawabannya tersedia penuh di field kartu di atas?",
                },
            },
        }
        response = httpx.post(
            f"{self.base_url}/systemone",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=BATAS_WAKTU,
        )
        response.raise_for_status()
        return response.json().get("answers", {})

    def saran(self, pertanyaan: str) -> dict[str, Any]:
        """Noul: apakah pertanyaan minta saran investasi? Tanpa kartu (nilai pertanyaannya)."""
        body = {
            "state": json.dumps({"pertanyaan": pertanyaan}, ensure_ascii=False),
            "model": self.model,
            "questions": {
                KUNCI_SARAN: {
                    "type": "noul",
                    "instructions": ("Apakah pengguna meminta saran investasi: beli, jual, atau tahan, "
                                     "atau menanyakan target harga?"),
                    "criteria": {
                        "true": "Meminta saran investasi atau target harga.",
                        "false": "Hanya menanyakan data, angka, atau arti istilah.",
                    },
                },
            },
        }
        response = httpx.post(
            f"{self.base_url}/systemone",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=BATAS_WAKTU,
        )
        response.raise_for_status()
        return response.json().get("answers", {})

    def prediksi(self, kalimat: str) -> dict[str, Any]:
        """Noul: apakah kalimat ini prediksi/opini tanpa angka terukur? Tanpa kartu."""
        body = {
            "state": json.dumps({"kalimat": kalimat}, ensure_ascii=False),
            "model": self.model,
            "questions": {
                KUNCI_PREDIKSI: {
                    "type": "noul",
                    "instructions": ("Apakah kalimat ini berisi prediksi, opini, atau rumor tentang "
                                     "harga/nasib saham di masa depan TANPA angka atau fakta terukur "
                                     "yang bisa diperiksa?"),
                    "criteria": {
                        "true": "Prediksi/opini/rumor tanpa angka atau fakta terukur.",
                        "false": "Berisi angka atau fakta yang bisa diperiksa.",
                    },
                },
            },
        }
        response = httpx.post(
            f"{self.base_url}/systemone",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=BATAS_WAKTU,
        )
        response.raise_for_status()
        return response.json().get("answers", {})


def minta_saran_jev(jev: Any, pertanyaan: str) -> bool:
    """JEV sebagai pengaman kedua penolakan saran. True = minta saran.

    Menerima klien apa pun yang punya `.saran(pertanyaan)` (klien JEV sungguhan atau
    palsu saat tes). Kalau JEV mati/gagal -> False: HANYA menolak, tidak pernah
    mengizinkan, dan regex guard tetap jalan lebih dulu.
    """
    try:
        jawab = jev.saran(pertanyaan).get(KUNCI_SARAN)
    except Exception:
        return False
    nilai = jawab.get("noul") if isinstance(jawab, dict) else None
    return isinstance(nilai, (int, float)) and nilai >= AMBANG_SARAN


def get_jev() -> Optional[Jev]:
    """None kalau Tanya memakai mode kode saja atau kuncinya belum diisi."""
    if settings.tanya_mode.lower() == "off" or not settings.jev_api_key:
        return None
    return Jev(settings.jev_base_url, settings.jev_api_key, settings.jev_model)


def prediksi_jev(jev: Any, kalimat: str) -> bool:
    """True = kalimat itu prediksi/opini tanpa angka. JEV mati/gagal -> False (pakai heuristik)."""
    try:
        jawab = jev.prediksi(kalimat).get(KUNCI_PREDIKSI)
    except Exception:
        return False
    nilai = jawab.get("noul") if isinstance(jawab, dict) else None
    return isinstance(nilai, (int, float)) and nilai >= AMBANG_PREDIKSI


def pilih_bagian(answers: dict[str, Any]) -> Optional[str]:
    jawab = answers.get(KUNCI_BAGIAN)
    pilihan = jawab.get("choice") if isinstance(jawab, dict) else None
    return pilihan if pilihan in BAGIAN else None


def pilih_istilah(answers: dict[str, Any]) -> Optional[str]:
    jawab = answers.get(KUNCI_ISTILAH)
    pilihan = jawab.get("choice") if isinstance(jawab, dict) else None
    return pilihan if pilihan in {i["key"] for i in glosarium()["istilah"]} else None


def yakin(answers: dict[str, Any]) -> float:
    jawab = answers.get(KUNCI_TAHU)
    nilai = jawab.get("noul") if isinstance(jawab, dict) else None
    return float(nilai) if isinstance(nilai, (int, float)) else 0.0
