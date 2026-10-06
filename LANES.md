# LANES — task split for "cek dulu."

Four lanes run in parallel. The contract lives in `contract/`, so nobody has to wait for anyone else to start.
Product source: `docs/FINAL_PLAN_cekdulu.md`. This document only covers **who does what, and in what order**.
**Detailed brief per task** (goal, files, steps, limits, how to check it is done): `docs/lanes/A.md`, `B.md`, `C.md`, `D.md`.

### Working on a task with AI (Claude Code, Codex, Cursor, etc.)

This repo already contains `AGENTS.md` (read automatically by Codex, Cursor, Copilot, etc.) and `CLAUDE.md` (read automatically by Claude Code). Both contain the ground rules, a repo map, and how to run tests. How to use them:

1. `git switch main && git pull`, then create a task branch (see "Day-to-day workflow" below).
2. Open the AI in the repo root and give it a prompt like:
   > Do task **B1** from LANES.md. Follow the brief in docs/lanes/B.md and the rules in AGENTS.md. Don't change files outside Lane B's area. You're done when the "Done when" checks pass and `pytest -q` is green.
3. Read the diff before committing. If the AI wants to change `contract/` or another lane's files, stop and discuss it in the group first.
4. Whatever AI you use, **don't let it run Sectors live mode** without your approval (credits are limited).

| Lane | Owner | Area (folders you may change without asking) |
|---|---|---|
| **A — Frontend** | Kafi | `frontend/` |
| **B — Checking engine** | _tbd_ | `backend/app/data/sectors.py`, `normal.py`, `checkers/` (except `m_komoditas.py`), `engine.py`, `scripts/`, `data/fixtures/` |
| **C — AI, Tanya (Ask), deploy** | _tbd_ | `backend/app/ai/`, `backend/app/main.py`, `backend/app/quota.py`, deploy files |
| **D — Modules, extra cards, video** | Aufa? | `backend/app/modul/`, `backend/app/untold/`, `checkers/m_komoditas.py`, `data/bahan_produk/`, `docs/video/` |

**Shared (change via a PR labelled `kontrak`):** `contract/`, `backend/app/schemas.py`, `frontend/src/lib/contract.ts`.

**Priority** (proposed, re-assessed at every sync point): **P0** must be in the video · **P1** important for judges trying it themselves · **P2** can be cut.

---

## Phase 0 — Foundations (everyone starts at once)

Goal: everyone can run the repo, the FE runs on mocks, the BE has real fixtures.

| ID | Lane | Task | Done when | P |
|---|---|---|---|---|
| **A0** | A | Install shadcn (`npx shadcn@latest init`), move the colour tokens, fonts, and layout skeleton from prototype iteration 3 into `src/index.css` + `components/` | Home and layout look like the prototype on a 390px phone | P0 |
| **B0** | B | Run `python scripts/buat_fixture.py` to build fixtures from the data-lab cache. Note which keys are still `-`, decide which need pulling (`--live`, uses credits) | Output table copied into the PR; P0 keys for MGLV & MDKA filled | P0 |
| **C0** | C | Decide the LLM provider + API key holder (open decision #1). Try 10 sample claims in a playground: can it split claims + pick `checks` from the list in `rules.json`? | Decision written in the group + in `README.md` | P0 |
| **D0** | D | Read `data/bahan_produk/KAMUS_DATA.md`. Match the demo scenario numbers in FINAL_PLAN §6 against the CSVs (MGLV, MDKA, ANTM, BUMI, PSAB) | "Numbers match / differ" list in the PR (`docs/cek_angka_demo.md`) | P0 |

---

## Phase 1 — Thin demo path: MGLV + MDKA end to end with real data

Goal: after this phase there is a product that can be recorded, even if only two scenarios.

| ID | Lane | Task | Done when | P |
|---|---|---|---|---|
| **A1** | A | Input + Confirm screens like the prototype: lined paper, ready-made examples, highlighter using `claim.span`, delete/edit claims | Input → Confirm flow works in mock mode | P0 |
| **A2** | A | "Running form" loading screen (from `steps[].ms`) + Results: verdict stamp, cards, "Yang tidak diceritakan", source + date on every number | Screenshots of MGLV & MDKA results resemble the prototype | P0 |
| **B1** | B | `normal.py` parsers for: `nama_emiten`, `harga_harian`, `tanggal_aksi_korporasi`, `riwayat_suspensi`, `transaksi_orang_dalam`, `free_float`. Raw JSON shape: see the fixture files | `CEKDULU_DATA_MODE=fixture`, `/api/cek` for MGLV returns suspensions, insiders, price spikes with real numbers | P0 |
| **C1** | C | `ai/<provider>.py`: `extract_claims` (text) + `answer`. The prompt may only pick `checks` from `rules.json`. `sanitize()` still runs. If the LLM fails → `NoLLM` | The 4 examples in `labels.ts` produce the right claims + `checks`; tests with the LLM disabled still pass | P0 |
| **D1** | D | `modul/komoditas.py`: `porsi_pendapatan` (segmen_pendapatan.csv) + `korelasi` (saham_vs_komoditas.csv). Map segment names → commodity (e.g. "proyek nikel" → nickel) | `/api/cek` MDKA "saham emas" (gold stock) → **Menyesatkan** (misleading), 82% nickel | P0 |
| **D2** | D | "Yang tidak diceritakan" providers: `papan_pemantauan`, `aksi_korporasi` (MGLV rights issue) | Cards appear in the MGLV result | P0 |

### 🔄 Sync point 1 — first integration
FE switches to `VITE_API_MODE=api`, BE runs in `fixture`. Together, run MGLV and MDKA from the Input screen to Results.
Discuss: what differs from the contract, what needs changing, **and re-assess the P1/P2 priorities below.**

---

## Phase 2 — Complete

| ID | Lane | Task | Done when | P |
|---|---|---|---|---|
| **A3** | A | Inspection form (8 checkers, fixed order, 6 statuses) + checker detail "Lihat aturannya" (see the rule) | All statuses render correctly, including `data_kurang` & `gagal` | P0 |
| **A4** | A | 4:5 share card for WhatsApp (save as image, e.g. `html-to-image`) with "Data dari Sectors · Bukan saran investasi" (Data from Sectors · Not investment advice) | Image saves from a phone | P0 |
| **A5** | A | Tanya (Ask) panel bound to a card + suggested questions + refusal view | The question "layak beli?" (worth buying?) is politely refused | P1 |
| **A6** | A | Analysis tools: Free Float Radar (list → detail → "check a claim about this stock" bridge), Commodity Module | Reachable from a result card, not only from the menu | P1 |
| **A7** | A | Methodology (from `/api/rules`), quota exhausted, ⓘ terms in plain language | All rules + the "usulan" (proposed) label shown | P1 |
| **B2** | B | Parsers for `laba_kuartalan`, `valuasi`, `dividen`, `aliran_asing` + rule A-2 (monthly foreign-share trend from `komposisi_pemegang`) | 8 checkers run for BBRI, BREN, PTBA, MGLV, MDKA, ANTM, BUMI, PSAB | P0 |
| **B3** | B | Answer open decision #4 (sector average yield for D-1) and #5 (one-off items for L-2). Change `rules.json` if needed | Decision written + rule tests updated | P1 |
| **B4** | B | Scenario tests: `tests/test_skenario.py` runs the 6 scenarios from FINAL_PLAN §6 in fixture mode and checks their verdicts | 6 scenarios green | P0 |
| **C2** | C | Screenshot OCR (`image_base64`) via the LLM | WA chat screenshot → the same claims as the text version | P1 |
| **C3** | C | `/api/tanya` with the LLM: answers only from numbers on the card (prompt + check that numbers in the answer appear on the card) | 10 test questions: no invented numbers | P1 |
| **C4** | C | Deploy: backend (e.g. Render/Railway/Fly) + frontend (Vercel/Netlify), `VITE_API_BASE`, CORS, `SECTORS_CREDIT_BUDGET` | Public link works from a phone | P0 |
| **D3** | D | Providers `analis`, `pemegang`, `segmen`, `likuiditas` + claim checkers for `analis` & `pemegang` (ANTM and BUMI scenarios) | ANTM: "Sesuai" + info on the −46% earnings projection; BUMI: two different verdicts | P0 |
| **D4** | D | Final `/api/modul/free-float` (monitoring-board flag) + `/api/modul/komoditas` | Endpoints return real CSV data | P1 |
| **D5** | D | Video script ≤3 minutes + 1-minute teaser (outline in FINAL_PLAN §11). The Remotion intro already exists in `D:\GitHub\cekdulu-video` | Final script + shot list | P0 |

### 🔄 Sync point 2 — feature freeze
After this, **no new features**. Anything unfinished moves to "Yang tidak dikerjakan" (not done) in the README.

---

## Phase 3 — Polish, verification, submission

| ID | Lane | Task | P |
|---|---|---|---|
| **A8** | A | Test on real phones, fix copy & terms, failure/insufficient-data/quota states | P0 |
| **B5** | B | Re-check every number in the video against the fixtures (FINAL_PLAN §6: "must be re-checked") | P0 |
| **C5** | C | Final README: how to run, architecture (checker flow diagram), rule list, data sources, role of AI | P0 |
| **D6** | D | Record video + teaser, social media post tagging Sectors, one-sentence problem statement | P0 |
| **Everyone** | – | Make the repo **public before submitting**, then submit before 8 Oct 23:59 WIB. **The repo is frozen from submission**: no commits at all, including bug fixes. The repo must stay public until ±15 Jan 2027 (90 days after the 17 Oct winner announcement) | P0 |

---

## Day-to-day workflow (git)

A short guide for those who rarely work in a team on GitHub:

0. **Once after cloning:** `git config core.hooksPath .githooks` (strips AI attribution lines from commit messages).
1. **One task = one branch.** Name: `<lane>/<id>-<short>`, e.g. `b/b1-parser-harga`.
   ```bash
   git switch main && git pull
   git switch -c b/b1-parser-harga
   ```
2. **Commit small and often.** Messages in English: `feat(b1): parse daily prices`. No AI `Co-Authored-By` (see the Git section in `AGENTS.md`).
3. **Push, then open a Pull Request (PR)** into `main`. PR = "please look at and merge my changes". Fill in the template.
4. **One other person reviews the PR** (a quick read + run the tests), then clicks *Merge*.
5. After a merge, everyone else runs `git switch main && git pull`, then `git rebase main` on their branch.
6. **Don't change files in another lane's area** without saying so in the group. It's the simplest way to avoid *merge conflicts* (two people changing the same lines).
7. **Don't commit `.env`** (it holds API keys). It's already in `.gitignore`.

Before opening a PR:
```bash
cd backend && pytest -q          # all tests pass
cd frontend && npm run build     # TypeScript types & build pass
```
