# AGENTS.md — guide for AI coding agents (Claude Code, Codex, Cursor, Copilot, etc.)

Read this file before changing anything. It applies equally to humans.

## Project

**cek dulu.** ("check first") is a mobile-first web app for Sectors Hackathon 2026 (Track 3, Market Intelligence). Users paste a stock claim from a WhatsApp group; the app splits it into claims and checks each one against Sectors data using **written rules**. The result is a verdict + reason + numbers + sources.
Submission deadline: **8 Oct 2026 23:59 WIB**. Team of 4, 4 lanes.

## Reading order

1. `AGENTS.md` (this file) — ground rules.
2. `LANES.md` — who does what. Find the task ID you were given (e.g. `B1`).
3. `docs/lanes/<A|B|C|D>.md` — **the detailed brief for that task**: goal, files, steps, limits, how to check it is done.
4. `contract/README.md` + `contract/rules.json` — the FE↔BE contract and every verdict rule.
5. For product context: `docs/FINAL_PLAN_cekdulu.md`. If you touch data: `docs/DATA_NOTES.md` and `data/bahan_produk/KAMUS_DATA.md`.

Do not read the whole repo. Read only the files named in your task brief.

## Rules that must not be broken

1. **Verdicts are decided by code, not AI.** Verdicts (`sesuai`, `menyesatkan`, `tidak_sesuai`, `tidak_bisa_dicek`, `info`), numbers, and data selection are computed in `backend/app/checkers/` and `backend/app/modul/` with pure rule functions. The LLM (`backend/app/ai/`) may only split claims, pick checkers, read screenshots, and rephrase sentences. **Never ask an LLM to decide a verdict or compute a number.**
2. **No buy/sell advice, price targets, or predictions.** Prediction claims → `tidak_bisa_dicek`. The Tanya (Ask) panel refuses investment-advice questions (regex in `rules.json`).
3. **Every number on screen has a source + date** (`sources[]` on the card). A card without sources is only allowed for the `tidak_bisa_dicek` verdict.
4. **Rule thresholds live only in `contract/rules.json`.** Code reads them via `catalog.param("H-1", "batas_perubahan")`. Never hard-code a threshold. New rule = new ID in `rules.json` + a test in `backend/tests/test_aturan.py`.
5. **Don't make up numbers.** Example numbers in `contract/examples/` come from FINAL_PLAN §6; demo numbers must come from fixtures or CSVs in `data/`. If data is missing, `raise DataUnavailable(...)` (status `data_kurang`); never fill in 0 or a guess.
6. **One failing checker must not bring down the whole check.** `engine._run` already catches errors; don't raise errors from outside a checker's `run` function.
7. **The contract is shared.** Changing `contract/`, `backend/app/schemas.py`, or `frontend/src/lib/contract.ts` = a separate PR labelled `kontrak`, and all three places change together.
8. **Stay inside your lane** (table in `LANES.md`). If you need to change another lane's files, stop and ask a human.
9. **The repo freezes at submission** (8 Oct 23:59 WIB at the latest): no commits/pushes/edits of any kind afterwards, including bug fixes, or the team is disqualified. Don't port code from older projects into this repo (judges inspect the commit history).
10. **Sectors credits are limited** (±324 left). Don't run `live` mode or `buat_fixture.py --live` without human approval. Tests must not call the real API.
11. **Don't commit `.env`, API keys, `data/cache/`, or the contents of `data/fixtures/`.**

## Repo map

```
contract/rules.json          all checkers, cards, rules + thresholds, quota, refusal regex
contract/examples/*.json     example requests/responses (used by FE & BE mocks, and tests)
backend/app/main.py          FastAPI endpoints                                    [Lane C]
backend/app/engine.py        check orchestration → verdict, form, untold (NO AI)   [Lane B]
backend/app/checkers/        one file = one checker; pure aturan_xx functions     [Lane B, m_komoditas: D]
backend/app/data/sectors.py  Sectors adapter: fixture → cache → live (credit-capped) [Lane B]
backend/app/data/normal.py   raw JSON parser → simple dataclasses                 [Lane B]
backend/app/data/bahan.py    reader for data/bahan_produk CSVs                    [Lane D]
backend/app/untold/          "Yang tidak diceritakan" (what they didn't tell you) cards [Lane D]
backend/app/modul/           Free Float Radar, stock vs commodity                 [Lane D]
backend/app/ai/              LLM + keyword fallback + advice refusal              [Lane C]
backend/scripts/buat_fixture.py  build data/fixtures from the data-lab cache (0 credits)
frontend/src/lib/api.ts      the only place the FE calls the backend (mock/api mode) [Lane A]
frontend/src/pages/          one file per screen                                  [Lane A]
data/fixtures/<TICKER>/      raw Sectors JSON per stock (fixture-mode data source; not in git)
data/bahan_produk/           processed data-lab CSVs + KAMUS_DATA.md
```

## Commands

```bash
# backend (from backend/)
pip install -r requirements.txt
pytest -q                                   # must pass before a PR
uvicorn app.main:app --reload --port 8000   # CEKDULU_DATA_MODE in root .env: mock | fixture | live

# frontend (from frontend/)
npm install
npm run dev                                 # VITE_API_MODE in .env.local: mock | api
npm run build                               # must pass before a PR (type check)
```

## Code patterns

- **New checker** (`backend/app/checkers/<name>.py`): a pure `aturan_xx(...)` function (numbers in, decision out) + a `Checker` class with `id` and `run(ticker, claim, today) -> Outcome`. Fetch data only through `app.data.normal` or `app.data.bahan`. Register it in `checkers/registry.py`. Write rule tests in `tests/test_aturan.py` (synthetic data, no fixtures).
- **Cards**: use `checkers.base.card(...)`; `rule_text` is filled in automatically from `rules.json`.
- **Parser** (`normal.py`): raw JSON → dataclass. See the JSON shapes in `docs/DATA_NOTES.md`. Empty field → `DataUnavailable`.
- **Frontend**: pages never call `fetch` directly, always go through `src/lib/api.ts`. Numbers from the backend are always raw; format them with `src/lib/format.ts`. UI text is plain Indonesian for beginner investors (hard terms get an ⓘ).
- Language: function names, code comments, and UI text are in Indonesian (follow the existing code). Docs (`*.md`) are in English.
- Small, focused changes. Don't refactor files outside your task, and don't add large dependencies without a reason.

## Git

- One branch per task: `<lane>/<id>-<short>`, e.g. `b/b1-parser-harga`.
- Commit messages in **English**, Conventional Commits with the task ID as scope: `feat(b1): parse daily prices`. Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `style`. Keep commits small; the body is optional and at most one short paragraph.
- **No AI attribution.** Don't add `Co-Authored-By: Claude ...`, `Claude-Session: ...`, or "Generated with ..." to commits or PRs. Commit with your own GitHub account. The `.githooks/commit-msg` hook strips those lines automatically after `git config core.hooksPath .githooks` (once per clone).
- PR into `main`, fill in the template. One other member reviews, then merges.
- Never force-push to `main`.

## When in doubt

Stop and ask a human, especially if: the task needs a contract change, needs a live Sectors call, the numbers in the data differ from FINAL_PLAN §6, or a rule in `rules.json` seems unreasonable for real data.
