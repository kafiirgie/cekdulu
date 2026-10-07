# data/fixtures

Raw Sectors API responses per stock (`<TICKER>/<key>.json`), used by the backend in `fixture` mode (0 credits).

`report_keuangan.json` is an optional supplement containing only `valuation` and `dividend`. The parser uses it when those sections are missing from `report.json`; it preserves the team's original company and ownership snapshot. Full reports do not need this supplement. Build it explicitly with `--kunci report_keuangan`.

On 7 October 2026, the approved B0 fetch added 23 responses for MGLV, MDKA, ANTM, BUMI, and PSAB. The adapter recorded 52 credits (MGLV 8, MDKA 12, ANTM 10, BUMI 10, PSAB 12). All 48 pre-existing fixture files were preserved byte for byte. Live responses were also saved in `data/cache/`; the local audit is `data/cache/b0_fetch_summary.json`.

These additions are current responses, alongside the team's September price/ownership snapshots. Read each card's source date; do not assume all datasets share one snapshot date. All eight standard-check datasets are now present for the eight demo tickers, but the profit check still reports `data_kurang` for MGLV (all five earnings values are null) and PSAB (earnings for 2025-09-30 are null). Null earnings are not replaced or silently skipped.

**The contents of this folder are not committed**, because it isn't yet clear whether Sectors responses may be redistributed in a public repo.

How to get them:
- **Team members:** download `fixtures.zip` from the team's shared folder and extract it here.
- **If you have the data-lab cache** (`cekdulu-datacheck`): `cd backend && python scripts/buat_fixture.py` (0 credits).
- **If you have your own Sectors API key:** set `SECTORS_API_KEY` in `.env`, then `python scripts/buat_fixture.py --live MGLV MDKA` (uses credits).
