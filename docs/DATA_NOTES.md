# Data notes that affect the code

Summary of the data-lab findings (29–30 Sep 2026, folder `D:\GitHub\cekdulu-datacheck\`) that **must be kept in mind when writing code**. Full details are in the Project documents `DATA_FINDINGS_sectors.md` and `EKSPLORASI_sectors.md`.

## Sectors API

- Base `https://api.sectors.app`, header `Authorization: <key>` **without** "Bearer". A 429 doesn't cost credits; a 404 costs 1.
- Credits: ±676 of 1,000 used as of 30 Sep. **Don't call live without a reason.** Use `data/fixtures/` (`fixture` mode).
- Tickers in responses end in `.JK` (`"symbol": "MGLV.JK"`). Strip `.JK` when comparing.
- Percentages in responses are inconsistent:
  - `report.ownership.major_shareholders[].share_percentage` = **decimal string** (`"0.3292"` = 32.92%).
  - `filings[].share_percentage_before/after` = **percentage number** (`63.07` = 63.07%). Divide by 100.
  - `dividend.yield_ttm`, `payout_ratio` = decimals.

## Fixture JSON shapes (verified)

| Fixture key | Shape | Important fields |
|---|---|---|
| `report` | `{symbol, company_name, valuation, dividend, ownership, ...}` (sections depend on the cache source) | `valuation.historical_valuation[]` → `{year, pe, pb, pe_peer_avg, pb_peer_avg}`; `valuation.forward_pe` (may be `null`); `dividend.yield_ttm`, `payout_ratio`, `dividend_yield_avg {period, avg_yield}` (the **company's own** average, not the sector's); `ownership.major_shareholders[]` → `{name, share_percentage}` (look for `name == "Public"`) |
| `keuangan_kuartalan` | list of 5 quarters, **newest first** | `date`, `earnings` (net profit), `revenue`, `earnings_before_tax`. No separate one-off items → rule L-2 uses the period version |
| `harga_harian` | list, sorted by date | `date`, `close`, `volume`, `market_cap`. **No transaction value** → value ≈ `close × volume` |
| `aliran_asing` | `{symbol, start, end, data: [...]}` | `date`, `net_foreign_inflow` (Rp), `foreign_buy_idr`, `foreign_sell_idr` |
| `filings` | `{results: [...], pagination}` | `timestamp`, `holder_name`, `holder_type`, `transaction_type` (`buy`/`sell`), `transaction_value` (**Rp**), `amount_transaction` (**shares**), `share_percentage_before/after` (percent) |
| `suspensi` | `{results: [...], pagination}` | `suspension_date`, `reason`, `pdf_url` |
| `aksi_korporasi` | `{symbol, corporate_actions: {agm, bonus, warrant, dividend, right_issue, stock_split, upcoming_dividend}}` | `right_issue[]` → `{price, ex_date, old_ratio, new_ratio}` |
| `segmen` | `{symbol, financial_year, revenue_breakdown: [{source, target, value}]}` | revenue tree (source → target) |
| `komposisi_pemegang` | `{symbol, data: [...]}` monthly | `*_l` (local) & `*_f` (foreign) in **shares**; `individual_l` = local retail; `total_l`, `total_f`; `numbers_of_shareholders` (only filled from Sep 2025) |
| `report_future` | `{future: {...}}` | `analyst_rating_breakdown {buy, hold, sell, n_analyst, updated_on}`, `company_growth_forecasts[] {eps_growth, revenue_growth, estimate_year}` |

## Pitfalls

1. **Prices are not adjusted for corporate actions.** ADRO −25% (28–29 Nov 2024) because of an ex-dividend date. Rule H-1 ignores returns on corporate-action dates (`tanggal_aksi_korporasi`).
2. **`forward_pe` can be `null`** (BREN). Show "tidak tersedia" (not available), never 0.
3. **Ownership data in the report can lag behind filings.** MGLV: report 67.08%, latest filing 62.71%. For "the controlling shareholder is selling", use filings.
4. **Shareholder composition: coverage differs per company** (PTBA ±34% of shares, ADRO & MGLV ±100%). Only compare trends within one company, show them as shares of the total, and label them.
5. **"Number of recommendations", not "number of analysts"** (`n_analyst` ANTM 70).
6. **Sectors' "Coal" price = HBA** (the government reference price; lagging, stopped 15 Feb 2026). For stock–commodity relationships use the World Bank (`saham_vs_komoditas.csv`).
7. **BPS gold exports look wrong**: don't show them.
8. **Mining data units are inconsistent** (copper "Mt", ferronickel "kton"). Avoid them, or show them very carefully.
9. **Sectors free float ≠ exactly the IDX definition** (IDX: 327 companies not yet compliant; Sectors: 242 < 15%). Mention it in Methodology.
10. **Special Monitoring Board (Papan Pemantauan Khusus)**: manual snapshot from 30 Sep 2026, one row per company (latest episode). Criteria 1, 6, 7, 10 were removed from 28 Sep 2026; show the old criteria's description.

## Fixture status (6 Oct, from `python backend/scripts/buat_fixture.py`)

| Ticker | report | quarterly | prices | foreign | filings | suspensions | corp. actions | segments | composition | future |
|---|---|---|---|---|---|---|---|---|---|---|
| MGLV | yes¹ | – | yes (241 days) | – | yes | yes | yes | – | yes | – |
| MDKA | – | – | yes | – | – | – | yes | yes | yes | yes |
| ANTM | yes² | – | yes | – | – | – | yes | yes | yes | – |
| BUMI | yes² | – | yes | – | – | – | yes | yes | yes | – |
| PSAB | – | – | yes | – | – | – | yes | – | – | – |
| BBRI, BREN | yes | yes | yes (61 days) | yes | yes | yes | yes | – | yes | – |
| PTBA | yes | yes | yes | yes | yes | yes | yes | – | yes | yes |

¹ MGLV report from the exploration cache: only the `overview` + `ownership` sections (no valuation/dividend).
² ANTM/BUMI report: `future` + `ownership` + `peers` sections (ANTM's analyst ratings are here, in `report.future`; no valuation/dividend).
Analyst rating data for ANTM is also in `data/bahan_produk/rating_analis.csv`.
