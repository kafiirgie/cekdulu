@AGENTS.md

## Claude Code specifics

- When given a task ID (e.g. "do B1"), read `LANES.md` and then that task's section in `docs/lanes/`. Build a task list from the brief's steps, and finish by running its "Done when" checks.
- Run `pytest -q` (backend) and/or `npm run build` (frontend) before declaring a task done.
- Don't run `buat_fixture.py --live` or the server with `CEKDULU_DATA_MODE=live` without explicit permission in the chat.
