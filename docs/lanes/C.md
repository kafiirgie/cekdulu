# Lane C — AI, Ask, deploy

**Area:** `backend/app/ai/`, `backend/app/main.py`, `backend/app/quota.py`, deploy files (e.g. `render.yaml`, `Dockerfile`, `vercel.json`), the how-to-run & architecture parts of the README.
**Read first:** `AGENTS.md`, `docs/FINAL_PLAN_cekdulu.md` §5 (role of AI), `backend/app/ai/provider.py`, `backend/app/ai/fallback.py`, `contract/README.md`.

Starting point: `/api/klaim` already works with the **keyword fallback** (`NoLLM`, no AI). `/api/tanya` answers with a template from the numbers on the card. The `LLM` interface in `provider.py` is ready; only a provider needs adding.

**Limits on AI's role (must be enforced in code, not only in the prompt):** AI may split claims, determine the ticker, pick `checks` from the list in `rules.json`, read screenshots, and compose answer sentences. AI **may not** decide verdicts, compute numbers, or give advice.

---

## C0 — Choose the LLM provider · P0

**Criteria:** can read images (OCR of Indonesian WA screenshots), structured JSON output, latency < 3 seconds, enough free quota/credits for the demo + judges, and a clear owner of the API key.

**Steps**
1. Try 10 claims (the 4 examples in `frontend/src/lib/labels.ts` + 6 of your own, including ones mixing prediction and data, slang such as "ARA" (auto-reject upper limit) and "asing net buy", and two tickers in one message).
2. Compare with the output of `fallback.pecah_klaim`.
3. Write the decision + env variable names in `README.md` (Open decisions section) and tell the team.

**Done when:** the decision is written down; `LLM_PROVIDER`, `LLM_MODEL` are filled in `.env.example`.

---

## C1 — Claim extraction with an LLM · P0

**File:** `backend/app/ai/<provider>.py` (a class implementing the `LLM` protocol), registered in `get_llm()`.

**Spec for `extract_claims(text, image_base64, ticker) -> KlaimResponse`:**
- The prompt gives the list of valid `checks` (from `catalog()`: id + label of checkers and cards) and asks for JSON `{ticker, claims: [{text, checks}]}`.
- Each claim's `text` must be an **exact substring** of the original text. **Compute `span` in code** (`teks.find(klaim)`); don't trust spans from the LLM. Claims not found in the text → drop them.
- Prediction/opinion claims → `checks: []`.
- `sanitize()` already drops unknown `checks`; it is still called via `extract_with_fallback`.
- If the LLM errors/times out (> 8 seconds) → `extract_with_fallback` automatically uses `NoLLM`. Set `used_ai`.
- Ticker: 4 capital letters. If the LLM guesses a ticker that isn't in the text, use `fallback.cari_ticker`.

**Tests:** `backend/tests/test_ai.py` with a fake LLM (stub class), no network calls: spans recomputed, hallucinated claims dropped, stray `checks` dropped, error → fallback.

**Done when:** the 4 demo examples produce the same claims and `checks` as `contract/examples/klaim_res_*.json` (or better); `pytest -q` passes without an API key.

---

## C2 — Screenshots (OCR) · P1

`image_base64` → the vision LLM reads the text first, then the same process as C1 (spans computed against the **OCR text**, and that text is returned so the Confirm screen can highlight it). **This adds a contract field** (`source_text` in `KlaimResponse`) → a `kontrak` PR together with Lane A. Limit image size (the FE shrinks it before sending; the BE rejects > 4 MB with 413).

**Done when:** a WA chat screenshot containing the MGLV claim produces the same claims as the text version.

---

## C3 — Tanya (Ask) · P1 — deterministic answers + TypeSafe/JEV classification

**Replaces** the old plan of asking an LLM for free text. Free-text answers were the
brittle part: a model could invent a number or drift off the card. Now:

- **The model only classifies.** TypeSafe `/systemone` picks which part of the card
  answers the question (angka / aturan / sumber / istilah / tidak ada), from a closed
  set of labels. It never writes the answer text.
- **Code writes every answer.** `backend/app/ai/tanya.py` assembles the sentence from
  the card's own fields (`headline`, `reason`, `evidence`, `rule_text`, `sources`) and
  the contract glossary. So no number can be invented and no phrasing can leak advice.
- **Files:** `backend/app/ai/jev.py` (classifier client), `backend/app/ai/tanya.py`
  (answer assembler + `jawab_tanya`), `backend/app/ai/openai_compat.py` (an
  OpenAI-compatible provider, e.g. ollama-cloud, for claim splitting).
- **Guard order is unchanged:** `guard.minta_saran` runs first in `/api/tanya`.
- **Never 500:** if JEV is off (`TANYA_MODE=off`), unset, or errors, `jawab_tanya` falls
  back to a code-only `ringkasan` answer built from the same fields.
- Env: `TANYA_MODE` (`auto`/`off`), `JEV_BASE_URL`, `JEV_API_KEY`, `JEV_MODEL`.
  With `auto` and no `JEV_API_KEY`, no model call happens — code answers only.

**Done when:** `pytest -q` stays green with **no network** (fake `httpx.post`, same
pattern as `tests/test_ai.py`), and a real `/api/tanya` call through curl answers from
the card (numbers, rule, sources, glossary) without inventing anything.

---

## C4 — Deploy · P0

1. **Backend** (Render/Railway/Fly/VM, pick one): run from `backend/` with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. The `contract/` and `data/` folders must be deployed too (paths are computed from the repo root in `app/config.py`).
   Env: `CEKDULU_DATA_MODE=fixture` (or `live` with a small `SECTORS_CREDIT_BUDGET`), `SECTORS_API_KEY`, `LLM_*`, `CORS_ORIGINS=<frontend url>`.
   **A single instance only**: quota and check results are kept in process memory.
   Free tiers usually "sleep" → open `/api/health` before a demo/recording.
   Fixtures aren't in git (see `data/fixtures/README.md`), so the deploy needs them supplied separately.
2. **Frontend** (Vercel/Netlify): root `frontend/`, build `npm run build`, output `dist`, env `VITE_API_MODE=api`, `VITE_API_BASE=<backend url>`. Add an SPA rewrite (all paths → `index.html`) so `/cek/hasil` doesn't 404 on refresh.
3. Test from a phone: the MGLV and MDKA flows, quota exhausted (6 checks), Ask.

**Done when:** the public URL works from a phone and is recorded in the README.

---

## C5 — Final README · P0 (phase 3)

Complete `README.md`: app + video links, how to run, checker flow diagram (text/mermaid), table of all rules (may be generated from `rules.json`), role of AI and its limits, data sources + licences (World Bank CC BY), "Deliberately not done", and the team.
