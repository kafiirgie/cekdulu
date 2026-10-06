# Lane B — Checking engine

**Area:** `backend/app/data/sectors.py`, `backend/app/data/normal.py`, `backend/app/checkers/` (except `m_komoditas.py`), `backend/app/engine.py`, `backend/scripts/`, `data/fixtures/`, `backend/tests/test_aturan.py`, `backend/tests/test_skenario.py`.
**Read first:** `AGENTS.md`, `contract/rules.json`, `docs/DATA_NOTES.md` (JSON shapes + pitfalls), `backend/app/checkers/base.py`.

Starting point: every rule (`aturan_xx`) and checker class already exists and is tested with synthetic data. What's missing are the **parsers** in `normal.py`. While a parser is still TODO, its checker reports `data_kurang`. As soon as the parser is filled in, the checker works with real data.

---

## B0 — Complete the demo stock fixtures · P0

**Goal:** every demo stock has the fixtures its scenario needs.

**Steps**
1. `cd backend && python scripts/buat_fixture.py`. The table is already recorded in `docs/DATA_NOTES.md` § Fixture status.
2. Decide the **required** keys per scenario (FINAL_PLAN §6):
   - MGLV: `harga_harian`, `suspensi`, `filings`, `aksi_korporasi`, `report` (free float) — **all present**. Extra for the full form: `keuangan_kuartalan`, `aliran_asing`, `report` with the `valuation,dividend` sections.
   - MDKA: `segmen`, `harga_harian` present. For the form: `report` (all), `keuangan_kuartalan`, `aliran_asing`, `filings`, `suspensi`.
   - ANTM, BUMI: `report_future` (ANTM), `komposisi_pemegang` (BUMI) + form keys.
   - PSAB: `report` (dividend).
3. Count credits: `report` 1, `keuangan_kuartalan` 5, `aliran_asing` 1, `filings` 1, `suspensi` 1, `report_future` 1. The team has ±324 credits left; keep ±100 for judges.
4. **Ask a human for permission** with the list + total credits, then `python scripts/buat_fixture.py --live MGLV MDKA ...` (needs `SECTORS_API_KEY` in `.env`). The script only pulls empty keys.
5. Note: the cached MGLV `report` only contains `overview` + `ownership`; ANTM/BUMI contain `future` + `ownership` + `peers` (ANTM analyst ratings already present). For valuation/dividends, delete that file first so `--live` pulls `report` with `sections=all`, or add a new key `report_valuasi`.

**Done when:** the output table has no `-` for required keys; total credits used are recorded in the PR.
**Human decision:** fixtures (Sectors responses) are kept out of git for now (see `data/fixtures/README.md`); judges need them to run the demo, so confirm with the organisers whether they may be published.

---

## B1 — Parsers for the MGLV scenario · P0

**Goal:** in `fixture` mode, `/api/cek` for MGLV returns suspensions, insiders, price spikes, and free float with real numbers.

**File:** `backend/app/data/normal.py` (fill in the TODO functions).

| Function | Fixture source | Notes |
|---|---|---|
| `nama_emiten` | `report.company_name` | |
| `harga_harian` | `harga_harian[]` → `HargaHarian(date, close, nilai_transaksi_rp=close*volume)` | sort by date |
| `tanggal_aksi_korporasi` | `aksi_korporasi.corporate_actions`: `dividend[]`, `right_issue[]`, `stock_split[]`, `bonus[]` → collect `ex_date` | the date field name may differ per type; check the file. Empty/`null` → empty set (not an error) |
| `riwayat_suspensi` | `suspensi.results[]` → `Suspensi(suspension_date, reason)` | empty `results` → empty list (status **aman**) |
| `transaksi_orang_dalam` | `filings.results[]` → `nama=holder_name`, `jenis` = `beli`/`jual` (buy/sell) from `transaction_type`, `nilai_rp=transaction_value`, `sebelum/sesudah = share_percentage_before/after / 100` | `tanggal` from `timestamp[:10]` |
| `free_float` | `report.ownership.major_shareholders[]` with `name == "Public"` → `float(share_percentage)` | no Public entry → `DataUnavailable` |

Strip the `.JK` suffix where needed. For every function, if the fixture file is missing, `sectors.get` already raises `DataUnavailable`.

**Tests:** add `backend/tests/test_normal.py` that reads the MGLV fixtures (skip if they're missing) and checks: 7 suspensions; a Nextier sale with `sesudah ≈ 0.6271`; first price 600, last 14650; free float ≈ 0.33.

**Done when:** `CEKDULU_DATA_MODE=fixture uvicorn app.main:app` then `POST /api/cek` with the body of `contract/examples/klaim_res_mglv.json` produces:
- the claim "dari 600 udah 14 ribuan" (from 600 it's already 14k) → `sesuai` (rule H-2);
- form: `suspensi` finding, `orang_dalam` finding, `lonjakan_harga` finding, `free_float` clear;
- `untold` contains suspension and insider cards with source + date.

**Watch out:**
- Insider card: FINAL_PLAN mentions 78.74% → 62.71% (several filings combined). Make sure the sales are ordered by date correctly in `checkers/orang_dalam.py`.
- `checkers/suspensi.py` uses `Source(as_of=today)`. Using the latest suspension date would be more honest; feel free to fix it.

---

## B2 — Remaining parsers: profit, valuation, dividend, foreign + rule A-2 · P0

| Function | Source | Notes |
|---|---|---|
| `laba_kuartalan` | `keuangan_kuartalan[]` → `Kuartal(periode=date, laba_bersih=earnings)` | the file lists **newest first**; the checker sorts by `periode` (ISO date string, safe to sort) |
| `valuasi` | `report.valuation.historical_valuation[]` latest year → `pe`, `pb`; `forward_pe` | a `null` `forward_pe` stays `None` |
| `dividen` | `report.dividend.yield_ttm`, `payout_ratio`; `yield_rata_sektor` = `None` for now (B3) | `yield_ttm` `null`/0 → the checker returns `tidak_relevan` |
| `aliran_asing` | `aliran_asing.data[]` → `AliranAsing(date, net_foreign_inflow)` | |

**Rule A-2 (foreign/retail share trend):** add a `komposisi_bulanan(ticker)` function in `normal.py` (from `komposisi_pemegang.data[]`: foreign share = `total_f / (total_l + total_f)`, local retail share = `individual_l / (total_l + total_f)`, `numbers_of_shareholders`). Add `aturan_a2(...)` in `checkers/asing.py`. The claim "foreigners coming in/going out" is judged by A-1 **and** A-2. If they point in different directions, the verdict is `menyesatkan` with the explanation "tergantung jendela waktu" (depends on the time window). This is a **rule change → get team approval** and write its text in `rules.json`.

**Done when:** the 8-checker form is filled (not `data_kurang`) for BBRI, BREN, PTBA, and the demo stocks with complete fixtures. `pytest -q` passes.

---

## B3 — Open rule decisions · P1

1. **D-1 sector average yield.** `dividend_yield_avg` in the report is the company's own average, not the sector's. Options: (a) `GET /v2/subsector/report/{subsector}/` (1 credit per subsector, check whether it has a yield); (b) compute the median `yield_ttm` per subsector from `data/bahan_produk/dividen_payout_yield.csv` (0 credits, but the CSV only covers some companies); (c) change D-1 to "yield ≥ X% and payout ≤ 100%". Propose to the team, change `rules.json`, update the tests.
2. **L-2 one-off items.** Quarterly data has **no** separate one-off items (see `docs/DATA_NOTES.md`). Make sure the L-2 text in `rules.json` only describes the period rule (it already does). Write the note in Methodology (ask Lane A).
3. Rules with status `usulan` (proposed: L-1, H-2, K-1): agree on the numbers with the team, then change the status to `final`.

---

## B4 — Demo scenario tests · P0

Create `backend/tests/test_skenario.py`: for each FINAL_PLAN §6 scenario, run `pecah_klaim(text)` → `run_cek(...)` in fixture mode (skip if fixtures are missing) and check the verdict per claim + the important untold cards.

| Scenario | Required |
|---|---|
| MGLV | "bakal terbang" `tidak_bisa_dicek`; "dari 600…" `sesuai`; untold contains suspension, insiders, monitoring board (D2), rights issue (D2) |
| MDKA | "saham emas" `menyesatkan` (D1); "pasti ikut naik" `tidak_bisa_dicek` |
| ANTM | "semua analis buy" `sesuai` + earnings projection info (D3) |
| BUMI | "diserbu ritel" `sesuai`, "asing juga masuk" `tidak_sesuai` (D3 + B2) |
| PSAB | "dividen 25%" `sesuai` + payout > 100% info |

Tests waiting on another lane may use `pytest.mark.xfail(reason="menunggu D1")` for now. **Done when:** all scenarios are green at sync point 2.

---

## B5 — Re-check the video numbers · P0 (phase 3)

Compare every number that will appear in the video with the `/api/cek` output from fixtures. Write a table "number in the script ↔ number in the app ↔ source" in `docs/video/cek_angka.md`. Numbers that don't match → change the script, not the data.
