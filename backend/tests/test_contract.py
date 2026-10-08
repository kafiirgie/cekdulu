"""Kontrak tetap sinkron: contoh JSON valid, ID aturan ada di katalog, span cocok."""
import json

import pytest

from app.catalog import catalog, glosarium, known_ids
from app.config import settings
from app.schemas import (CekResponse, FreeFloatList, Glosarium, GlosariumKey, KlaimRequest, KlaimResponse, KomoditasDetail,
                         KomoditasList, RingkasRequest, RingkasResponse, TanyaRequest, TanyaResponse)

EX = settings.contract_dir / "examples"
RULE_IDS = {r["id"] for r in catalog()["rules"]}


def load(name):
    d = json.loads((EX / name).read_text(encoding="utf-8"))
    d.pop("_catatan", None)
    return d


@pytest.mark.parametrize("t", ["mglv", "mdka"])
def test_contoh_valid(t):
    req = KlaimRequest.model_validate(load(f"klaim_req_{t}.json"))
    res = KlaimResponse.model_validate(load(f"klaim_res_{t}.json"))
    for c in res.claims:  # span menunjuk teks asli (untuk stabilo di layar Konfirmasi)
        assert req.text[c.span[0]:c.span[1]] == c.text
        assert set(c.checks) <= known_ids()
    cek = CekResponse.model_validate(load(f"cek_res_{t}.json"))
    for card in cek.claims + cek.untold:
        assert card.rule_id is None or card.rule_id in RULE_IDS, card.rule_id
        assert card.check is None or card.check in known_ids()
    std = [c["id"] for c in catalog()["checks"] if c["standar"]]
    assert [f.check for f in cek.form][:8] == std, "formulir: 8 pemeriksa standar, urutan tetap"


def test_contoh_lain_valid():
    t = load("tanya.json")
    TanyaRequest.model_validate(t["req"])
    TanyaResponse.model_validate(t["res_tolak"])
    TanyaResponse.model_validate(t["res_jawab"])
    FreeFloatList.model_validate(load("modul_free_float_list.json"))
    KomoditasList.model_validate(load("modul_komoditas_list_emas.json"))
    KomoditasDetail.model_validate(load("modul_komoditas_detail_mdka.json"))


def test_contoh_ringkas_menunjuk_kartu_yang_ada():
    r = load("ringkas.json")
    RingkasRequest.model_validate(r["req"])
    res = RingkasResponse.model_validate(r["res"])
    kartu = CekResponse.model_validate(load("cek_res_mdka.json"))
    kunci = {c.claim_id for c in kartu.claims} | {f"u{i}" for i in range(len(kartu.untold))}
    assert {i.kunci for i in res.items} <= kunci


def test_katalog_konsisten():
    checks = {c["id"] for c in catalog()["checks"]}
    for r in catalog()["rules"]:
        assert r["check"] is None or r["check"] in checks, r["id"]
        assert r["status"] in ("final", "usulan")
    assert len([c for c in catalog()["checks"] if c["standar"]]) == 8


def test_glosarium_valid_dan_sinkron():
    """Glosarium = kontrak: kunci di JSON harus sama dengan Literal di schemas.py."""
    g = Glosarium.model_validate(glosarium())
    keys = [i.key for i in g.istilah]
    assert len(keys) == len(set(keys)), "kunci glosarium kembar"
    literal = set(getattr(GlosariumKey, "__args__", ()))
    assert set(keys) == literal, f"schemas.py tidak sinkron: {set(keys) ^ literal}"
    # Pemetaan hanya boleh menunjuk kunci glosarium dan id yang benar-benar ada.
    for k in list(g.pemetaan.checks.values()) + list(g.pemetaan.untold.values()):
        assert k in literal, k
    for cid in list(g.pemetaan.checks) + list(g.pemetaan.untold):
        assert cid in known_ids(), cid
    assert catalog().get("glosarium"), "rules.json harus menunjuk glosarium"
