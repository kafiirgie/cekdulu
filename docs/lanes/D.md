# Lane D — Modules, extra cards, video

**Area:** `backend/app/modul/`, `backend/app/untold/`, `backend/app/checkers/m_komoditas.py` (+ new checkers `analis.py`, `pemegang.py`), `backend/app/data/bahan.py`, `data/bahan_produk/`, `docs/video/`.
**Read first:** `AGENTS.md`, `docs/FINAL_PLAN_cekdulu.md` §3.4, §4, §6, §11, `data/bahan_produk/KAMUS_DATA.md`, `docs/DATA_NOTES.md`.

Starting point: the Free Float Radar (`modul/free_float.py`) **already works** and its output matches the data-lab CSV (it has tests). The commodity module and every "Yang tidak diceritakan" (what they didn't tell you) provider are still TODO and raise `DataUnavailable` (silently skipped).

Provider pattern (`untold/providers.py`): `(ticker, claims) -> Card | None`. Return `None` when not relevant, raise `DataUnavailable` when data is missing. Always `verdict="info"` + `sources` (name + snapshot date).

---

## D0 — Match the demo numbers · P0

For every number in FINAL_PLAN §6, find it in `data/bahan_produk/*.csv` or `data/fixtures/` and write `docs/cek_angka_demo.md`: number in the plan · number in the data · file/column · match? Examples: MDKA 82% nickel → `segmen_pendapatan.csv`; BUMI 226k → 590k → `komposisi_pemegang_saham.csv` (`jumlah_pemegang`); ANTM 68/70 buy, EPS −46% → `rating_analis.csv`; MGLV rights issue → `kalender_aksi_korporasi.csv`; MGLV monitoring board → `papan_pemantauan_khusus.csv`.

**Done when:** every §6 number has a row; mismatches are flagged and reported to the team.

---

## D1 — Commodity module for "stock X = commodity Y stock" claims · P0

**Files:** `backend/app/modul/komoditas.py`, `backend/app/checkers/m_komoditas.py`.

1. **Segment → commodity mapping.** Segment names in `segmen_pendapatan.csv` aren't uniform (e.g. "Coal sales", "Proyek nikel"). Create a small file `data/bahan_produk/segmen_ke_komoditas.csv` (`symbol, segmen, komoditas`), filled in by hand for the mining companies in the CSV. Mixed segments (MDKA "Tujuh Bukit" = gold/copper) get the commodity `campuran:emas+tembaga` (mixed: gold+copper) and are **not** counted as pure gold share. Write the rule in a comment.
2. `porsi_pendapatan(ticker, jenis)` → share from that commodity. Also add `komoditas_terbesar(ticker) -> (jenis, porsi)`.
3. `korelasi(ticker, jenis)` from `saham_vs_komoditas.csv` (columns `symbol, komoditas, korelasi_bulanan, kategori, total_return_saham, perubahan_komoditas, arah_tahunan`). Map `jenis` → the World Bank name (check the contents of the `komoditas` column; coal = "Coal, Australian" = Newcastle). There are several rows per company → pick the one matching `jenis`.
4. Update `MKomoditas.run`: the headline must read like FINAL_PLAN, e.g. **"82% pendapatan MDKA dari proyek nikel, bukan emas."** (82% of MDKA's revenue is from nickel projects, not gold.) Evidence: largest share, correlation + category (from `aturan_k2`, not the CSV column), stock total return vs commodity change over the same period. Sources: Sectors get-segments (financial year) + World Bank Pink Sheet (2 Sep 2026).
5. Tests: `aturan_k2(korelasi_csv) == kategori_csv` for every row (ensures the `rules.json` thresholds match the data lab); MDKA "saham emas" → `menyesatkan`.

**Done when:** `POST /api/cek` for MDKA with `contract/examples/klaim_res_mdka.json` (fixture mode) → claim c1 is `menyesatkan` with real numbers.

---

## D2 — MGLV cards: monitoring board, corporate actions · P0

- `papan_pemantauan`: `papan_pemantauan_khusus.csv` (`symbol, tanggal_masuk, tanggal_keluar, aktif, kriteria`) + `papan_pemantauan_kriteria.csv` for the criteria text. Shown if the company is active on **or has ever been** on the board. Mention that criterion 10 was removed from 28 Sep 2026. Source: "BEI · Papan Pemantauan Khusus (unduh manual)" (IDX · Special Monitoring Board, manual download), as_of 2026-09-30.
- `aksi_korporasi`: `kalender_aksi_korporasi.csv` (`symbol, jenis, tanggal, detail_json`), within 90 days of `today`. Rights issue: show the exercise price vs the last price (`normal.harga_harian` from Lane B; if it isn't ready yet, skip the comparison).

**Done when:** the MGLV check result includes both cards.

---

## D3 — Analyst & shareholder claims (ANTM, BUMI) · P0

The claim fallback already maps "analis/rekomendasi buy" (analysts/buy recommendation) → `analis` and "ritel/diserbu" (retail/swarmed) → `pemegang`, but **there are no checkers for them yet** (they come out `data_kurang`).

1. **New rules in `rules.json`** (`kontrak` PR, status `usulan`): e.g. `N-1` "A claim that 'all/most analysts say buy' matches if the share of buy (+ strong buy) recommendations is ≥ 90% of all recommendations" and `P-1` "A claim that 'retail/foreigners are coming in' matches if that group's share rose over the last 3–6 months (compared with the first month of the window)". Add `analis` and `pemegang` to `checks` (standard: false). Rule texts in `rules.json` are shown to users, so write them in Indonesian.
2. `checkers/analis.py`: data from `rating_analis.csv` (or the `report_future` fixture). Claim card + EPS & revenue projection evidence (ANTM: 68/70 buy but 2026 EPS −46%). Label "jumlah rekomendasi" (number of recommendations).
3. `checkers/pemegang.py`: data from `komposisi_pemegang_saham.csv` (`porsi_ritel_lokal`, `porsi_asing`, `jumlah_pemegang`, `cakupan`). The "diserbu ritel" claim is judged from local retail share + number of shareholders. The coverage label is required.
4. Register them in `checkers/registry.py` (coordinate with Lane B, one line).
5. Untold providers `analis`, `pemegang`, `segmen`, `likuiditas` (liquidity: 60-day average of `close × volume`; propose a "small" threshold in `rules.json`).
6. The claim "asing juga masuk" (foreigners coming in too, BUMI) is judged by Lane B's `asing` checker (rule A-2). Make sure it comes out `tidak_sesuai` together with Lane B.

**Done when:** the ANTM & BUMI scenarios in `tests/test_skenario.py` (Lane B) are green.

---

## D4 — Module endpoints · P1

- `/api/modul/free-float`: add the `papan_pemantauan` flag (from the board CSV, `aktif == "ya"`; check the exact value in the CSV).
- `/api/modul/komoditas?jenis=` and `/api/modul/komoditas/{ticker}`: **the response shape isn't in the contract yet.** Propose it first via a `kontrak` PR (`schemas.py` + `contract.ts` + `contract/examples/modul_komoditas_*.json`) so Lane A can start with mocks. Contents: per company → commodity, revenue share, correlation + category, direction per year (`arah_tahunan`), stock vs commodity total return.
- Open decision #3 (HuluHilir chain view): decide with the team; if kept, every chain position must have a source.

---

## D5 — Video script & teaser · P0

`docs/video/naskah.md`: FINAL_PLAN §11 outline → script per second + shot list (which screen, what input, what numbers). The Remotion intro already exists in `D:\GitHub\cekdulu-video`. 1-minute teaser = hook + core demo + closing. Name the **derived insights** explicitly (Track 3): Free Float Radar (days to absorb vs deadline), stock vs commodity category, "Yang tidak diceritakan".

## D6 — Record & submit · P0 (phase 3)

Record from the deployed app with fixture data, after B5 (number check) is done. Social media post tagging Sectors, one-sentence problem statement (FINAL_PLAN §1).
