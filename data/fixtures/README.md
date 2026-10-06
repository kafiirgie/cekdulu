# data/fixtures

Raw Sectors API responses per stock (`<TICKER>/<key>.json`), used by the backend in `fixture` mode (0 credits).

**The contents of this folder are not committed**, because it isn't yet clear whether Sectors responses may be redistributed in a public repo.

How to get them:
- **Team members:** download `fixtures.zip` from the team's shared folder and extract it here.
- **If you have the data-lab cache** (`cekdulu-datacheck`): `cd backend && python scripts/buat_fixture.py` (0 credits).
- **If you have your own Sectors API key:** set `SECTORS_API_KEY` in `.env`, then `python scripts/buat_fixture.py --live MGLV MDKA` (uses credits).
