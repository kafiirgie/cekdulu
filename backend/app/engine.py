"""Mesin cek: jalankan pemeriksa → vonis per klaim, formulir 8 pemeriksa, "Yang tidak diceritakan".
TIDAK ADA AI di sini. Semua vonis berasal dari fungsi aturan di checkers/.  [Lane B]"""
from __future__ import annotations

import logging
import time
import uuid
from collections import Counter
from datetime import date
from typing import Optional

from .catalog import check_label, rule, standard_checks
from .checkers.base import Outcome
from .checkers.registry import CHECKERS
from .data import normal
from .data.sectors import DataUnavailable
from .schemas import Card, CekRequest, CekResponse, Claim, FormRow, Step
from .untold.providers import PROVIDERS

log = logging.getLogger("cekdulu.engine")

VERDICT_TEKS = {"sesuai": "sesuai data", "menyesatkan": "menyesatkan", "tidak_sesuai": "tidak sesuai",
                "tidak_bisa_dicek": "tidak bisa dicek", "info": "informasi"}


def _run(check_id: str, ticker: str, claim: Optional[Claim], today: date) -> tuple[Outcome, int]:
    t0 = time.perf_counter()
    checker = CHECKERS.get(check_id)
    try:
        if checker is None:
            out = Outcome("data_kurang", f"Pemeriksa '{check_id}' belum dibuat.")
        else:
            out = checker.run(ticker, claim, today)
    except DataUnavailable as e:
        out = Outcome("data_kurang", "Data tidak cukup untuk pemeriksaan ini.")
        log.info("data_kurang %s %s: %s", ticker, check_id, e)
    except Exception:  # satu pemeriksa gagal tidak boleh menjatuhkan seluruh cek
        log.exception("gagal %s %s", ticker, check_id)
        out = Outcome("gagal", "Pemeriksaan ini gagal dijalankan. Hasil lain tetap berlaku.")
    return out, int((time.perf_counter() - t0) * 1000)


def _tidak_bisa_dicek(claim: Claim, alasan: str, rule_id: Optional[str] = "T-1") -> Card:
    return Card(claim_id=claim.id, verdict="tidak_bisa_dicek", check=None,
                headline=f"\"{claim.text}\" tidak bisa kami cek ke data.", reason=alasan,
                rule_id=rule_id, rule_text=rule(rule_id)["text"] if rule_id else None)


def ringkasan(claims: list[Card], n_untold: int) -> str:
    if not claims:
        teks = "Kami menjalankan 8 pemeriksaan standar untuk saham ini."
    else:
        c = Counter(k.verdict for k in claims)
        bagian = [f"{n} {VERDICT_TEKS[v]}" for v, n in c.items() if v in VERDICT_TEKS]
        teks = f"Dari {len(claims)} klaim, " + (", ".join(bagian[:-1]) + " dan " + bagian[-1] if len(bagian) > 1 else bagian[0]) + "."
    if n_untold:
        teks += f" Ada {n_untold} hal yang tidak diceritakan."
    return teks


def run_cek(req: CekRequest, today: Optional[date] = None) -> CekResponse:
    today = today or date.today()
    ticker = req.ticker.upper()
    steps: list[Step] = []
    form: list[FormRow] = []
    std_out: dict[str, Outcome] = {}

    # 1) 8 pemeriksa standar — selalu jalan, urutan tetap
    for c in standard_checks():
        out, ms = _run(c["id"], ticker, None, today)
        std_out[c["id"]] = out
        form.append(FormRow(check=c["id"], status=out.status, why=out.why))
        steps.append(Step(check=c["id"], label=c["step_label"], ms=max(ms, 300)))

    # 2) vonis per klaim
    cards: list[Card] = []
    for claim in req.claims:
        if not claim.checks:
            cards.append(_tidak_bisa_dicek(claim, "Ini prediksi, opini, atau rumor tanpa angka. Kami tidak menebak."))
            continue
        kartu = None
        for cid in claim.checks:
            out, ms = _run(cid, ticker, claim, today)
            if cid not in std_out and not any(s.check == cid for s in steps):
                steps.append(Step(check=cid, label=check_label(cid), ms=max(ms, 300)))
                form.append(FormRow(check=cid, status="modul_aktif" if out.status != "gagal" else "gagal", why=out.why))
            if out.card is not None:
                kartu = out.card
                break
        cards.append(kartu or _tidak_bisa_dicek(claim, "Data yang dibutuhkan untuk klaim ini tidak cukup.", None))

    # 3) Radar Free Float aktif jika free float temuan
    if std_out.get("free_float") and std_out["free_float"].status == "temuan":
        form.append(FormRow(check="m_free_float", status="modul_aktif", why="Free float di bawah 15%."))

    # 4) Temuan aturan lain tetap tampil (mis. D-2 saat klaim yield memakai D-1).
    untold = [o.card for cid, o in std_out.items() if o.status == "temuan" and o.card
              and not any(k.check == cid and k.rule_id == o.card.rule_id for k in cards)]
    for pid, provider in PROVIDERS.items():
        try:
            k = provider(ticker, req.claims)
            if k is not None:
                untold.append(k)
        except DataUnavailable:
            pass
        except Exception:
            log.exception("untold gagal %s %s", ticker, pid)

    try:
        company = normal.nama_emiten(ticker)
    except DataUnavailable:
        company = None

    return CekResponse(id=f"cek_{uuid.uuid4().hex[:12]}", ticker=ticker, company=company,
                       data_as_of=str(today), summary=ringkasan(cards, len(untold)),
                       steps=steps, claims=cards, untold=untold, form=form)
