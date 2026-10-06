# cek dulu.

> Beginner investors in Indonesia often buy stocks because of claims in WhatsApp groups and forums ("profit up 200%", "foreigners are buying it all up", "it's going to the moon") that they never check against the data.

**cek dulu.** ("check first") splits a group message into claims, then checks each claim against market data from [Sectors](https://sectors.app) using **written rules**. The result is a verdict stamp, a reason, the numbers, and the sources, which can be sent back to the group.

**The rules decide, not AI.** AI only reads text/screenshots, splits claims, and rewrites the result in everyday language. Verdicts, numbers, and data selection are computed by code in `backend/app/checkers/`, and every rule has a test in `backend/tests/test_aturan.py`.

The app's UI is in Indonesian, because it is built for Indonesian retail investors and covers stocks listed on the Indonesia Stock Exchange (IDX).

Sectors Hackathon 2026 · Track 3 Market Intelligence · Not investment advice.

---

## Running it

Requires Python 3.11+ and Node 20+.

```bash
cp .env.example .env            # fill in SECTORS_API_KEY if you want live mode
git config core.hooksPath .githooks   # once per clone: strips AI attribution from commit messages

# backend
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python scripts/buat_fixture.py   # build data/fixtures from the data-lab cache (0 credits); see data/fixtures/README.md
pytest -q
uvicorn app.main:app --reload --port 8000

# frontend (another terminal)
cd frontend
cp .env.example .env.local       # VITE_API_MODE=mock (no backend) or api
npm install
npm run dev                      # http://localhost:5173
```

### Data modes

| | Frontend `VITE_API_MODE` | Backend `CEKDULU_DATA_MODE` |
|---|---|---|
| Start FE work without a backend | `mock` | – |
| BE returns the contract examples | `api` | `mock` |
| **Demo** (real rules, stored data, 0 credits) | `api` | `fixture` |
| Stocks outside the fixtures (uses credits, capped by `SECTORS_CREDIT_BUDGET`) | `api` | `live` |

## Structure

```
contract/            FE ↔ BE agreement: rules.json (all rules + thresholds) and example JSON
backend/
  app/
    main.py          FastAPI endpoints
    engine.py        runs checkers → verdict, form, "Yang tidak diceritakan" (no AI)
    checkers/        8 standard checkers + modules; pure rule functions `aturan_xx`
    untold/          extra "Yang tidak diceritakan" (what they didn't tell you) cards
    modul/           Free Float Radar, stock vs commodity
    data/            Sectors adapter (fixture/cache/live), parsers, CSV reader
    ai/              claim splitter (LLM + no-AI fallback), investment-advice refusal
  scripts/           buat_fixture.py
  tests/             rule, contract, and API tests
frontend/            Vite + React + TypeScript + Tailwind
data/
  bahan_produk/      data-lab CSVs (World Bank, BPS, FRED, IDX, Sectors) + KAMUS_DATA.md
  fixtures/          Sectors JSON per stock for the demo (not committed)
docs/
  FINAL_PLAN_cekdulu.md   product plan (source of truth for the product)
  DATA_NOTES.md           Sectors JSON shapes + data pitfalls
  lanes/A–D.md            detailed brief per task
LANES.md             team task split
AGENTS.md, CLAUDE.md rules for AI coding agents (and humans)
```

## Flow of one check

```
text / screenshot / ticker
  → POST /api/klaim   (AI or keyword fallback) → claims + relevant checkers
  → Confirm screen    (the user may edit/delete claims)
  → POST /api/cek     (NO AI)
       8 standard checkers, always in the same order  → inspection form
       per-claim checkers                             → verdict: sesuai · menyesatkan · tidak sesuai · tidak bisa dicek
       findings + extra cards                         → "Yang tidak diceritakan"
  → POST /api/tanya   (only from the numbers on the card; buy/sell advice questions are refused)
```

Verdicts in English: `sesuai` = matches the data · `menyesatkan` = misleading · `tidak_sesuai` = contradicts the data · `tidak_bisa_dicek` = can't be checked · `info` = context.

## Data sources

Core: **Sectors REST API v2** (financial statements, daily prices, foreign flows, insider filings, suspensions, corporate actions, revenue segments, analyst ratings, shareholder composition, free float).
Supplementary (labelled snapshots in `data/bahan_produk/`): World Bank Pink Sheet (CC BY), BPS `dataexim`, FRED `CCUSMA02IDM618N`, IDX Special Monitoring Board (Papan Pemantauan Khusus, manual download 30 Sep 2026).

## Open decisions

1. LLM provider + API key holder → task C0
2. Owners of Lanes B, C, D → `LANES.md`
3. How to show the HuluHilir (upstream–downstream) chain in the Commodity Module
4. Source for the sector average dividend yield (rule D-1) → B3
5. Whether Sectors quarterly data separates one-off items (rule L-2) → B3
6. Hosting & domain → C4
