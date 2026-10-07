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
KUNCI_KLAIM = "klaim_saham"
KUNCI_TARGET = "target_harga"

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

# Pertanyaan `prediksi`. Rumusan lama ("...TANPA angka atau fakta terukur") ikut menangkap
# kalimat fakta yang kebetulan tak berangka, sehingga pemeriksanya dibuang (regresi PR #34:
# "MDKA saham emas" 0,82 -> pemeriksa nikel hilang). Rumusan ini menanyakan apakah kalimat
# MURNI ramalan, jadi fakta tanpa angka tetap tidak dianggap prediksi. Diukur 3x per kalimat:
# fakta tanpa angka 0,09-0,29 (dulu 0,55-0,82) vs ramalan 0,74-0,90 (dulu 0,37-0,90).
TEKS_PREDIKSI = (
    "Apakah kalimat ini MURNI ramalan atau spekulasi tentang masa depan, tanpa satu pun "
    "pernyataan tentang keadaan sekarang atau kejadian yang sudah lewat yang bisa dicek "
    "dengan data? Jawab tidak kalau kalimatnya menyebut sifat atau keadaan saham saat ini "
    "(misalnya soal bisnisnya, sektornya, atau kinerjanya), dan jawab tidak juga kalau ada angka."
)
KRITERIA_PREDIKSI = {
    "true": ("Murni ramalan tentang masa depan; tak ada keadaan sekarang atau kejadian lampau "
             "yang bisa dicek data."),
    "false": ("Ada pernyataan tentang keadaan sekarang, kejadian lampau, atau angka yang bisa "
              "dicek data."),
}

# Ambang `klaim_saham`: pisahkan kalimat yang LAYAK diperiksa dari sapaan/pertanyaan/ngobrol.
# Hasil ukur: non-klaim maksimum 0,28 ("mantap, lanjut pantau"), klaim minimum 0,55
# ("cuan gede nih"). 0,4 di tengah-tengahnya.
AMBANG_KLAIM = 0.4

# Ambang `target_harga`: target/prediksi harga (walau berangka) TIDAK boleh diberi vonis,
# ikut aturan T-1. Hasil ukur: "besok naik ke 20.000" 0,96 · "TP MGLV 20rb" 0,67 vs
# "dari 600 udah 14 ribuan" 0,07 · "laba naik 20%" 0,03 · "harga terakhir 14.650" 0,06.
AMBANG_TARGET = 0.4

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




    def saring(self, kalimat: str) -> dict[str, Any]:
        """Satu panggilan untuk tiga pertanyaan sekaligus: klaim? prediksi? target harga?

        JEV bisa menjawab beberapa pertanyaan dalam satu request. Dulu pemanggil
        mengirim tiga request terpisah (klaim_jev + prediksi_jev + target_jev per
        klaim); digabung supaya hemat ~3x. Hasil ukur sama keputusannya.
        """
        body = {
            "state": json.dumps({"kalimat": kalimat}, ensure_ascii=False),
            "model": self.model,
            "questions": {
                KUNCI_KLAIM: {
                    "type": "noul",
                    "instructions": ("Apakah kalimat ini berisi klaim, kabar, atau pendapat tentang "
                                     "saham yang bisa diperiksa? Jawab tidak kalau hanya sapaan, ucapan "
                                     "terima kasih, pertanyaan, rencana pribadi, atau ajakan ngobrol."),
                    "criteria": {
                        "true": "Klaim/kabar/pendapat tentang saham yang bisa diperiksa.",
                        "false": "Sapaan, terima kasih, pertanyaan, rencana pribadi, atau ngobrol.",
                    },
                },
                KUNCI_PREDIKSI: {
                    "type": "noul",
                    "instructions": TEKS_PREDIKSI,
                    "criteria": KRITERIA_PREDIKSI,
                },
                KUNCI_TARGET: {
                    "type": "noul",
                    "instructions": ("Apakah kalimat ini berisi target harga atau prediksi arah harga "
                                     "ke depan (mis. \"naik ke 20.000\", \"target 20rb\")? Jawab tidak "
                                     "kalau kalimatnya melaporkan data atau harga yang sudah terjadi."),
                    "criteria": {
                        "true": "Target harga atau prediksi arah harga ke depan.",
                        "false": "Melaporkan data atau harga yang sudah terjadi.",
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


def _skor(answers: dict[str, Any], kunci: str) -> Optional[float]:
    jawab = answers.get(kunci)
    nilai = jawab.get("noul") if isinstance(jawab, dict) else None
    return float(nilai) if isinstance(nilai, (int, float)) else None


def saring_jev(jev: Any, kalimat: str) -> dict[str, bool]:
    """Tiga keputusan untuk satu kalimat dari SATU panggilan JEV.

    Bentuk: {"klaim": bool, "prediksi": bool, "target": bool}. Default aman kalau JEV
    mati/gagal: klaim=TRUE (jangan buang klaim asli), prediksi/target=FALSE (jangan
    matikan vonis tanpa alasan).
    """
    aman = {"klaim": True, "prediksi": False, "target": False}
    try:
        a = jev.saring(kalimat)
    except Exception:
        return aman
    klaim = _skor(a, KUNCI_KLAIM)
    prediksi = _skor(a, KUNCI_PREDIKSI)
    target = _skor(a, KUNCI_TARGET)
    return {
        "klaim": True if klaim is None else klaim >= AMBANG_KLAIM,
        "prediksi": False if prediksi is None else prediksi >= AMBANG_PREDIKSI,
        "target": False if target is None else target >= AMBANG_TARGET,
    }


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
