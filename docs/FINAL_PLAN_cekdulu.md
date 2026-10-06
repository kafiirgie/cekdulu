# cek dulu. — Final plan (Sectors Hackathon 2026)

> A copy of the plan document (version of 3 Oct 2026) so it lives in the repo and can be read by AI and team members. If it differs from the code in the repo, **the contract and rules in `contract/` win**; if it differs from the UI prototype, follow this document.
>
> UI prototype iteration 3 (sample data BBXX/BRXX): https://claude.ai/artifact/HkmN5S4nTwWLZJ3NowLQUg
> Data notes that affect the code: `docs/DATA_NOTES.md`. Data folder: `data/bahan_produk/` (+ `KAMUS_DATA.md`).
>
> The app UI is in Indonesian. Screen names and labels are quoted in Indonesian with an English gloss; example claims are kept in their original WhatsApp-group style.

---

## 1. One-page summary

| | |
|---|---|
| **Problem statement (1 sentence)** | Beginner investors in Indonesia often buy stocks because of claims in WhatsApp groups and forums ("profit up 200%", "foreigners are buying it all up", "it's going to the moon") that they never check against the data. |
| **Product** | Mobile-first web app: paste a claim (text / screenshot / ticker) → split into claims → each claim is checked against market data using **written rules** → the result is a verdict stamp + reason + numbers + source, which can be sent back to the group. |
| **Principle** | **The rules decide, not AI.** AI only reads text/screenshots, splits claims, picks checkers, and rewrites the result in everyday language. Verdicts, numbers, and data selection are computed by code. |
| **Track** | 3 — Market Intelligence (derived insight, not raw data). No buy/sell advice, no trade execution. |
| **Core data** | Sectors REST API (financial statements, daily prices, foreign flows, dividends, insider filings, suspensions, ownership, revenue segments, analyst ratings, shareholder composition, corporate actions). External data is only supplementary, stored as snapshots labelled with their source. |
| **Judging** | Usability 40% · Video 30% · Technical depth 30% |
| **Deadline** | Submit by **8 Oct 2026 23:59 WIB** (registration closes 7 Oct). The repo freezes at submission. |

---

## 2. User flow (as in the prototype)

| # | Screen | Contents | Notes for the real version |
|---|---|---|---|
| 1 | **Beranda** (Home) | Hero "Dengar klaim soal saham? Cek dulu sebelum percaya." (Heard a stock claim? Check before you believe it.), claim conveyor → verdict stamp animation, 8 checks, 3 steps, feature bento, entry to Analysis tools | Replace the BBXX examples with real demo examples (see §6) |
| 2 | **Input** | Lined text box, screenshot upload, ready-made examples | A ticker alone is also accepted → becomes a "general check" claim |
| 3 | **Konfirmasi klaim** (Confirm claims) | "Kami menemukan N klaim" (We found N claims); highlighted parts can be edited/deleted | AI extraction result; the user may correct it before checking |
| 4 | **Loading = running form** | Seconds counter + list of checkers running one by one | May be simulated in the FE from `steps[].ms` (see the contract) |
| 5 | **Hasil** (Results) | Summary ("Dari 4 klaim, 1 sesuai…" — of 4 claims, 1 matches…), one card per claim (stamp + sentence + reason + rule + evidence/chart + source), **"Yang tidak diceritakan"** (what they didn't tell you), full form button, "Bagikan ke grup" (share to group) | The core of the demo |
| 6 | **Formulir inspeksi** (Inspection form) | 8 standard checkers + modules, statuses: Ada temuan (finding) / Aman (clear) / Modul aktif (module active) / Tidak relevan (not relevant) / Data tidak cukup (insufficient data) / Gagal (failed) | Always the same order for every stock |
| 7 | **Checker detail** ("Lihat aturannya" — see the rule) | Rule, numbers, chart, source + date | |
| 8 | **Panel Tanya** (Ask panel) | Follow-up questions bound to a card, suggested questions; investment-advice questions are refused | The refusal regex is in `contract/rules.json` |
| 9 | **Share card** | 4:5 card for WhatsApp: claim summary + stamp + "Data dari Sectors · Bukan saran investasi" (Data from Sectors · Not investment advice) | Saved as an image |
| 10 | **Alat analisis** (Analysis tools) | Module index → company list → company detail → bridge to claim check | §4 |
| 11 | **Metodologi** (Methodology) | 5 verdicts, checker + rule table, role of AI, how modules calculate, what can't be checked, data sources | Add the external data list (§7) |
| 12 | **Kuota habis** (Quota exhausted) | 5 checks per day per device, no login | |

**Special states already in the prototype:** quota exhausted, one check failed, insufficient data. Keep them.

---

## 3. Verdicts and checkers

### 3.1 Five verdicts (per claim)

| Verdict | Meaning |
|---|---|
| **Sesuai data** (matches the data) | The claim matches the recorded data, according to its checker's rule. |
| **Menyesatkan** (misleading) | The number exists, but important context is missing or the period used is unfair. |
| **Tidak sesuai** (contradicts the data) | The data shows something different from the claim. |
| **Tidak bisa dicek** (can't be checked) | Predictions ("pasti terbang" — sure to fly), opinions, rumours without numbers. Not guessed. |
| **Info** | Important context the claim doesn't mention (used in "Yang tidak diceritakan"). |

### 3.2 Checker statuses (inspection form)
`temuan` · `aman` · `modul_aktif` · `tidak_relevan` · `data_kurang` · `gagal`. "No insider transactions in 12 months" = **aman** (clear), not insufficient data.

### 3.3 Eight standard checkers (always run)

The "Change" column = difference from the prototype's rule, based on the data check.

| # | Checker | Sectors data | Verdict rule | Change / data notes |
|---|---|---|---|---|
| 1 | **Laba** (Profit) | Quarterly reports (5 quarters up to 30 Jun 2026; 1 credit/quarter) | Claim "profit up X%": recompute. **Sesuai** if the difference ≤ tolerance; **Menyesatkan** if the claim uses 1 cherry-picked quarter/period while the 4-quarter trend points the other way, or >50% of the increase comes from one-off items | ⚠️ First check whether Sectors quarterly data separates one-off items. If not, the "one-off items" rule (L-2 in the prototype) is replaced with a period rule |
| 2 | **Valuasi** (Valuation) | Report section `valuation` + daily prices | PER & PBV; **Sesuai** if within 15% of our calculation | `forward_pe` may be empty (e.g. BREN) → show "tidak tersedia" (not available), never 0 |
| 3 | **Dividen** (Dividend) | Report section `dividend`, corporate actions, screener `yield_ttm`, `payout_ratio` | "Big dividend" is **Sesuai** if the 12-month yield ≥ 1.5× the sector average; **Menyesatkan** if another period is used (difference > 2 points) | **Add:** payout > 100% → finding "paid out more than earnings, may not recur" (31 companies, e.g. PSAB, BSSR, TLKM). ⚠️ Source for the sector average yield not checked yet |
| 4 | **Orang dalam** (Insiders) | Filings (holder_type, transaction_type, before/after %) | Finding if a transaction > Rp1B | **12-month window** (prototype: 90 days). Filings per stock are rare (BBRI 3, PTBA 0 in a year) |
| 5 | **Investor asing** (Foreign investors) | Daily foreign flow (max 90 days/call) + brokers + monthly shareholder composition | "Asing borong" (foreigners buying up) is **Sesuai** if net flow over 20 trading days > 0 and ≥ 60% of days are net inflows | **Add a monthly trend** of foreign/retail share (3–6 months) from shareholder composition |
| 6 | **Lonjakan harga** (Price spike) | Daily closing prices | Finding if the price changes > 25% within 21 trading days | **Must check corporate actions first**: Sectors prices aren't adjusted for splits/dividends (ADRO −25% on 28–29 Nov 2024 because of an ex-dividend date) |
| 7 | **Suspensi** (Suspension) | Suspensions + written reason + IDX PDF | Finding if there was a suspension within 36 months | Show the reason (e.g. "peningkatan harga kumulatif yang signifikan" — significant cumulative price increase) |
| 8 | **Free float** | "Public" entry in major_shareholders | Finding if < 15% → activate the Free Float Radar module | Sectors' definition ≠ exactly IDX's → mention it in Methodology |

### 3.4 Extra cards for "Yang tidak diceritakan" (new, from data exploration)

Shown with the **Info** verdict when relevant. All their data has been confirmed available.

| Card | Shown when | Source | Real example |
|---|---|---|---|
| **Papan Pemantauan Khusus** (Special Monitoring Board) | The company is or was on the board | IDX snapshot (manual download 30 Sep 2026) | MGLV on the board 6–15 Apr 2026 (criterion 10) |
| **Revenue sources** | The claim mentions a commodity/business | `get-segments` | MDKA: 82% of revenue from nickel projects, not gold |
| **Analysts vs earnings projection** | The claim mentions analysts/recommendations | Report `future` | ANTM 68 of 70 recommendations are buy, but projected 2026 EPS −46% |
| **Who holds it** | Claim about retail/foreigners/"crowded" | `shareholders-composition` | BUMI: shareholders 226k → 590k (Sep 2025 → May 2026), local retail 13% → 24%, foreign 81% → 69% |
| **Upcoming corporate actions** | A dividend/rights issue/split within 90 days | `corporate-actions` | MGLV rights issue ex 2 Nov 2026 at Rp8,880 (price Rp14,650) |
| **Liquidity** | Small daily traded value | Daily prices | MGLV average Rp12.9B/day (last 60 days) |

Fixed labels: "Komposisi pemegang saham: cakupan berbeda per emiten, bandingkan tren dalam satu emiten saja" (Shareholder composition: coverage differs per company, only compare trends within one company). "Jumlah rekomendasi" (number of recommendations), not "jumlah analis" (number of analysts).

---

## 4. Analysis tools (modules)

Same frame for every module: question → company list → detail → bridge to claim check.

### 4.1 Free Float Radar — data ready

- **Question:** does this stock have to release shares to the public, and how heavy is the pressure?
- **Data:** screener `free_float < 0.15 and market_cap > 0` → 242 companies (1–2 credits). File: `data/bahan_produk/radar_free_float.csv`.
- **Deadlines (Regulation I-A, SE-00004/BEI/03-2026)** — *replaces the prototype's "large/medium/small" logic:*

| Group | Target | Deadline | Companies |
|---|---|---|---|
| Cap > Rp5T & FF < 12.5% | 12.5% then 15% | 31 Mar 2027 then 31 Mar 2028 | 52 |
| Cap > Rp5T & FF 12.5–15% | 15% | 31 Mar 2027 | 20 |
| Cap ≤ Rp5T | 15% | 31 Mar 2029 | 170 |

- **Formula:** value to release = (target − free float) × market cap; days to absorb = value to release ÷ 60-day average daily traded value. Pressure: light < 20 days, moderate 20–60, heavy > 60. Labelled **"Dihitung"** (calculated).
- Calculated for 60 of the 72 companies with a 2027 deadline. Extreme range (BREN ±80 days, DUTI > 100,000 days) → **show at most "> 1.000 hari"** (> 1,000 days).
- Add a flag if the company is also on the Special Monitoring Board (13 companies, e.g. TRIO, INAF, BATA).

### 4.2 Commodity Module (formerly "Coal Chain") — *changed from the prototype*

- **Question:** does this stock really follow its commodity's price, or not?
- **Scope:** coal, nickel, gold, copper, tin (not only coal).
- **What changed:**
  - The stock–commodity relationship uses **World Bank market prices** (Newcastle for coal), **not HBA**. Sectors' HBA lags and pushes the correlation to ≈ 0; that's why the early conclusion was "no connection".
  - Show it as a **category per company** (weak < 0.3 · moderate 0.3–0.6 · fairly strong ≥ 0.6), not beta + scenarios. **The price slider/scenarios are removed** (too close to prediction).
  - Add the **share of revenue from that commodity** (segments) and the **direction per year** (same/opposite).
- **Example results (correlation of monthly changes, Jan 2023–Aug 2026):** INCO–nickel 0.63 · ADRO–Newcastle 0.57 · ARCI–gold 0.56 · ANTM–gold 0.49 · MDKA–copper 0.46 · BYAN 0.11 · BUMI 0.09 · AMMN ≈ 0 (weak). File: `data/bahan_produk/saham_vs_komoditas.csv`.
- **Core message:** "commodity price up ≠ stock automatically up" still holds, with nuance per company. Examples: in 2024 Newcastle −8% but ADRO +72%; in 2025 BUMI +114% while Newcastle −17%.
- **Supporting context:** Sectors commodity prices (official HBA, nickel/gold/copper), BPS monthly exports (coal, nickel, copper, tin; **don't show gold**, its numbers look wrong), FRED exchange rate.
- **Chain view (HuluHilir, upstream–downstream):** ⚠️ needs a decision. Sectors data on a company's role in the supply chain is thin (sales destinations only for 8/10 coal companies). Keep it only if the chain position can be filled from a clear source (e.g. the HuluHilir repo), and label the source.

---

## 5. Role of AI

| AI is used for | AI is not used for |
|---|---|
| Reading text & screenshots (OCR) | Deciding verdicts |
| Splitting text into claims + tickers | Computing numbers |
| Picking relevant checkers | Choosing data |
| Rewriting results in everyday language | Buy/sell advice |
| Answering follow-up questions **only from the numbers on the card** | Guessing prices |

Fallback when AI fails/quota runs out: ticker-only input → run the 8 standard checkers without claim extraction.

⚠️ **Open decision:** LLM provider and who holds the API key.

---

## 6. Demo scenarios (real data, snapshot 29–30 Sep 2026)

The numbers below come from the exploration; they **must be re-checked against the fixtures** before recording the video.

| # | Claim (WA group style) | Expected result | Why it's good for the demo |
|---|---|---|---|
| 1 | "**MGLV** masih bakal terbang, dari 600 udah 14 ribuan, buruan!" (MGLV is still going to fly, from 600 it's already 14k, hurry!) | "Bakal terbang" → **Tidak bisa dicek**. "From 600 to 14k" → **Sesuai data** (Rp600 → Rp14,650, ±24×). What they didn't tell you: 7 suspensions (6 because of price increases), Monitoring Board Apr 2026, controlling shareholder sold 78.74% → 62.71%, only ±1,389 shareholders, rights issue ex 2 Nov at Rp8,880 | Strongest video hook; shows "Yang tidak diceritakan" |
| 2 | "**MDKA** saham emas, emas lagi naik pasti ikut" (MDKA is a gold stock, gold is rising so it's sure to follow) | **Menyesatkan**: 82% of revenue from nickel projects. Moderate relationship with gold (0.40), copper 0.46. MDKA −36% (Jan 2023–Aug 2026) while gold +132% | Commodity module + segments |
| 3 | "Semua analis rekomendasi buy **ANTM**" (All analysts recommend buying ANTM) | **Sesuai data**: 68 of 70 recommendations are buy. Info: projected 2026 EPS −46%, revenue −30% | "Matches" but still with context |
| 4 | "**BUMI** diserbu ritel, asing juga masuk" (BUMI is swarmed by retail, foreigners are coming in too) | "Swarmed by retail" → **Sesuai data** (shareholders 226k → 590k; local retail 13% → 24%). "Foreigners coming in" → **Tidak sesuai** (foreign share 81% → 69%) | One message, two different verdicts |
| 5 (backup) | "**PSAB** dividennya 25%, gede banget" (PSAB's dividend is 25%, huge) | 25% yield **Sesuai data**; Info: payout 114%, paid out more than earnings | Dividend checker |
| 6 (backup) | Ticker only, with free float < 15% (pick from the radar, 2027 deadline) | Free float finding → Free Float Radar active, days to absorb | Free float module demo |

---

## 7. Data

### 7.1 Sources
| Data | Source | How the app uses it |
|---|---|---|
| All standard checkers, segments, analysts, composition, corporate actions, radar | **Sectors API** (core) | Live + cache, or fixtures for the demo |
| Monthly world commodity prices | World Bank Pink Sheet (CC BY), updated 2 Sep 2026 | Labelled CSV snapshot |
| Monthly exports per HS code | BPS WebAPI `dataexim` (up to Jul 2026) | Labelled CSV snapshot; Sectors exports = BPS (validated) |
| Rupiah per USD exchange rate | FRED `CCUSMA02IDM618N` | Labelled CSV snapshot |
| Special Monitoring Board | IDX (manual download 30 Sep 2026) | Snapshot + download date; criteria 1, 6, 7, 10 removed from 28 Sep 2026 |
| **Don't use** | ICI (Argus/Coalindo, paid), Google Trends, UMA (no source yet) | – |

Hackathon rule: Sectors must be the core source, not a single decorative call. The product must lose its core function if Sectors is removed. External data is allowed as a supplement. **Every number on screen shows its source + date.**

### 7.2 Ready-to-use files (`data/bahan_produk/`)
`segmen_pendapatan` · `rating_analis` · `komposisi_pemegang_saham` · `dividen_payout_yield` · `kalender_aksi_korporasi` · `radar_free_float` · `emiten_tambang_per_komoditas` · `saham_vs_komoditas` · `harga_komoditas_dunia_bulanan` · `ekspor_bulanan_bps` · `kurs_idr_per_usd_bulanan` · `papan_pemantauan_khusus` (+ `_kriteria`). Column meanings: `KAMUS_DATA.md`. Percentages are stored as decimals (0.25 = 25%).

### 7.3 Sectors credits
±676 of 1,000 used → **±324 left**. Fixtures for 8 checkers cost ±15–20 credits per stock → 6 demo stocks ≈ 120 credits. Keep ±100 for the live demo/judges. Header `Authorization: <key>` (no Bearer); a 429 doesn't cost credits, a 404 costs 1.

---

## 8. FE–BE JSON contract

**The contract in force is in `contract/` (README, `rules.json`, `examples/`), `backend/app/schemas.py`, and `frontend/src/lib/contract.ts`.** This section is only the early draft.

```jsonc
// POST /api/klaim  → split input into claims (AI)
{ "text": "Kata grup, MDKA saham emas...", "image_base64": null, "ticker": null }
// → { "ticker": "MDKA", "company": "...", "claims": [ { "id": "c1", "text": "...", "span": [10, 25], "checks": ["m_komoditas"] } ] }

// POST /api/cek  → run the rules (no AI for verdicts)
{ "ticker": "MDKA", "claims": [ { "id": "c1", "text": "MDKA saham emas", "checks": ["m_komoditas"] } ] }
// → { id, ticker, company, data_as_of, summary, steps[], claims[], untold[], form[], quota }

// GET  /api/modul/free-float  ·  /api/modul/free-float/{ticker}
// GET  /api/modul/komoditas?jenis=batubara  ·  /api/modul/komoditas/{ticker}
// POST /api/tanya { "cek_id": "...", "card": "c1", "question": "..." } → { "answer": "...", "refused": false }
```

Contract rules: raw numbers as decimals/full Rupiah, the FE does the formatting. Every card must have `sources[]`. Rule IDs (L-1, A-1, D-1, K-1, …) are the same as those shown in Methodology.

---

## 9. Task split

See `LANES.md` (split per lane and phase) and `docs/lanes/` (detailed brief per task).

---

## 10. Original schedule (remaining days)

| Date | Target |
|---|---|
| **Sat 3 Oct** | This document agreed. JSON contract final. Product repo created. Fixture-pulling script for the 6 demo stocks |
| **Sun 4 Oct** | FE on top of a mock server. BE: adapter + 8 checkers. AI: claim extraction |
| **Mon 5 Oct** | Extra cards + 2 modules. Ask panel. First FE–BE integration |
| **Tue 6 Oct** | Test all §6 scenarios + failure/insufficient-data/quota states. Fix copy & ⓘ terms |
| **Wed 7 Oct** | Deploy. Record the ≤3-minute video + 1-minute teaser. |
| **Thu 8 Oct** | Buffer + submit before 23:59 WIB |

This schedule has already slipped: the repo was only created on 6 Oct. The working order in force is in `LANES.md`; priorities are re-assessed at every sync point.

---

## 11. Video (30% of the score) — ≤3-minute outline

1. **0:00–0:20 Hook:** a WA-group-style message about MGLV "still going to fly".
2. **0:20–1:30 Core demo:** paste → confirm claims → running form → verdict stamp → "Yang tidak diceritakan" (suspensions, monitoring board, controlling shareholder selling).
3. **1:30–2:10 Second scenario:** "MDKA saham emas" → Menyesatkan + commodity module.
4. **2:10–2:40 Technical depth:** "the rules decide, not AI", the same 8-checker form for every stock, source + date on every number, Sectors as the core data.
5. **2:40–3:00 Closing:** the card is sent back to the group. "Keputusan tetap di tanganmu. Bukan saran investasi." (The decision stays in your hands. Not investment advice.)

1-minute teaser: cuts 1 + 2 + 5.

---

## 12. Submission package
- [ ] Repo public at submission, and **stays public for at least 90 days after winners are announced (17 Oct 2026 → until ±15 Jan 2027)**; making it private before then = losing the right to the prize. Source: hackathon.sectors.app/rules (checked 6 Oct)
- [ ] **Repo + app frozen at submission or on 8 Oct (whichever comes first): no commits/pushes/edits of any kind, including bug fixes.** The only exception: removing a leaked API key, after notifying the organisers
- [ ] Repo created after 19 Aug 2026, with no code migrated from older projects (judges may inspect the commit history)
- [ ] Video ≤3 minutes + 1-minute teaser
- [ ] One-sentence problem statement (§1)
- [ ] Social media post tagging Sectors
- [ ] App deployed, demo examples can be tried by judges

---

## 13. Open decisions (the team must answer)
1. LLM provider + API key holder (claim extraction, screenshot OCR, Ask).
2. Names for the BE, AI, and modules/video roles.
3. HuluHilir chain view in the Commodity Module: keep it (with what source) or replace it with a list of companies per commodity.
4. Source for the sector average dividend yield (rule D-1).
5. Whether Sectors quarterly data separates one-off items (rule L-2).
6. Hosting & domain.

## 14. Deliberately not done
Price predictions, price scenario slider, buy/sell advice, login/accounts, UMA data, ICI prices, BPS gold data.
