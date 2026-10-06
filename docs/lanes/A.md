# Lane A — Frontend

**Area:** `frontend/`.
**Read first:** `AGENTS.md`, `docs/FINAL_PLAN_cekdulu.md` §2 (12 screens), `frontend/README.md`, `frontend/src/lib/contract.ts`, `contract/examples/cek_res_mglv.json`.
**Design:** prototype iteration 3 https://claude.ai/artifact/HkmN5S4nTwWLZJ3NowLQUg. Take its look and interactions, but **follow FINAL_PLAN + the contract for content and rules** (the prototype still uses the BBXX/BRXX sample data and old rules). AI agents can't open that link: save the prototype HTML to `docs/prototipe/` (download it from the artifact) so it can be read as a reference.

Starting point: Vite + React + TS + Tailwind v4, router, session state (`lib/store.tsx`), API client with `mock`/`api` modes (`lib/api.ts`), and 8 skeleton pages that already run in mock mode. Comments `[A1]`, `[A2]`, … on each page mark the tasks.

**Lane A rules**
- Pages don't call `fetch`; everything goes through `lib/api.ts`.
- Numbers from the backend are always raw; format them with `lib/format.ts` (`fmt(value, e.fmt)`). Show source + date on every card.
- Design for 360–430 px wide phones first. Plain language; terms (free float, payout, PER, suspension, …) get an ⓘ with a one-sentence explanation.
- Required special states: quota exhausted, one check `gagal` (failed), `data_kurang` (insufficient data), network error, `/api/tanya` 404 (server restarted).

---

## A0 — Design foundations · P0

1. `npx shadcn@latest init` (the `@/` alias already exists in `tsconfig` & `vite.config.ts`). Add the components in use: `button card badge textarea sheet dialog tabs tooltip skeleton`.
2. Move the prototype's design tokens (colours, fonts, radius, shadows, verdict stamp style) into `src/index.css`. Verdict colours already exist as `--cd-*`; match their values to the prototype.
3. `components/Layout.tsx`: header, footer "Data dari Sectors · Bukan saran investasi" (Data from Sectors · Not investment advice), mock-mode banner.
4. Home: hero, claim conveyor → verdict stamp animation, 8 checks, 3 steps, bento, entry to Analysis tools. Example claims use the real scenarios (MGLV, MDKA), not BBXX.

**Done when:** Home at 390 px looks like the prototype; `npm run build` passes.

---

## A1 — Input + Confirm · P0

- **Input** (`pages/Input.tsx`): lined paper, ready-made examples (`lib/labels.ts`), screenshot upload → shrink in the browser (longest side ≤ 1280 px, JPEG) → `image_base64`. Ticker only (4 letters) → `{ticker}` → straight to Results (general check, `claims: []`).
- **Confirm** (`pages/Konfirmasi.tsx`): show the **original text** with claim parts highlighted using `claim.span` (character indexes into `store.text`). Claims can be deleted and their text edited. Claims without `checks` get the label "prediksi/opini — tidak bisa dicek" (prediction/opinion — can't be checked). Show checker names (labels from `api.rules()` → `checks[].label`), not raw ids.
- Note: for screenshots, the original text comes from the backend (`source_text`, task C2, waiting on a contract PR).

**Done when:** all four examples run from Input → Confirm in mock mode and api mode (backend in `fixture`).

---

## A2 — Running form + Results · P0

- **Loading** (`pages/Hasil.tsx`): the checker list from `steps[]` runs one by one + a seconds counter. Duration per step from `steps[].ms`, capped so the total is ±4–6 seconds (dramatic enough for the video, not boring for judges).
- **Results:** summary (`summary`), one card per claim (`components/VerdictCard.tsx`): stamp-style verdict, claim text, headline, reason, evidence, chart (`card.chart`: `line`/`bar`, using Recharts or simple SVG), "Lihat aturannya" (see the rule: `rule_id` + `rule_text`), source + date.
- The **"Yang tidak diceritakan"** (what they didn't tell you) section (`untold[]`) must stand out: it's the main selling point when many of a judge's claims can't be checked.
- Buttons: full form, "Bagikan ke grup" (share to group, A4), "Tanya" (Ask) per card (A5).

**Done when:** MGLV & MDKA results resemble the prototype in mock mode; nothing breaks when `claims` is empty (general check) or `untold` is empty.

---

## A3 — Inspection form + checker detail · P0

- `pages/Formulir.tsx`: the 8 standard checkers **in the order the backend sends** + module rows. Six statuses with distinct colours/icons (`lib/labels.ts → STATUS_LABEL`). Checker names from `api.rules()`.
- New route `/cek/formulir/:check` (screen 7): the rules that apply to that checker (filter `rules[].check`), related cards from `claims`/`untold` with the same `check`, source + date.

---

## A4 — Share card · P0

4:5 card (1080×1350) with the ticker, claims + verdict stamps (max 3), 1 line of "Yang tidak diceritakan", "Data dari Sectors · Bukan saran investasi", and the app name. Save as PNG (`html-to-image`); on phones use the Web Share API when available, otherwise download the file.

---

## A5 — Ask panel · P1

Bottom sheet per card. `api.tanya({cek_id, card, question})`; `card` = `claim_id` (e.g. `c1`) for claim cards, `u0`, `u1`, … (index) for "Yang tidak diceritakan" cards. 3 suggested questions per card (e.g. "Angka ini dari mana?" (where is this number from?), "Apa artinya untuk pemula?" (what does it mean for a beginner?), "Kenapa aturannya begitu?" (why is the rule like that?)). `refused: true` → a polite refusal view. A 404 error → "Hasil cek sudah kedaluwarsa, cek ulang ya." (This check has expired, please check again.)

---

## A6 — Analysis tools · P1

- Module index → Free Float Radar (`pages/RadarFreeFloat.tsx`): filter by deadline group, sort by days to absorb, **"Dihitung"** (calculated) label, days to absorb > 1,000 → "> 1.000 hari", monitoring-board flag, ⓘ explaining rule I-A. Company detail → **"Cek klaim saham ini"** (check a claim about this stock) button (fills `store.text` with the ticker → `/cek`).
- Commodity Module: **its response shape isn't in the contract yet** (task D4). Start once the D4 contract PR lands, using its example JSON in mock mode.
- From result cards whose `check` is `free_float` or `m_komoditas`, link to the module (modules shouldn't be reachable only from the menu).

---

## A7 — Methodology, quota, terms · P1

- `pages/Metodologi.tsx` (from `api.rules()`): 5 verdicts, checker + rule table (mark the `usulan` (proposed) ones), role of AI (table in FINAL_PLAN §5), what can't be checked, data sources including external data (World Bank CC BY, BPS, FRED, IDX), note that Sectors free float ≠ IDX.
- `pages/KuotaHabis.tsx`: show the time left until `quota.reset_at` (`KuotaHabisError.quota`, needs passing via state/route).
- List of ⓘ terms in `lib/istilah.ts` (one sentence each, everyday street-stall language).

---

## A8 — Phone testing & polish · P0 (phase 3)

Test on real phones (Android Chrome + iOS Safari if available): all §6 scenarios, failure states, quota, share card. Fix stiff copy. Check the colour contrast of the verdict stamps.
