# frontend — Lane A

Vite + React + TypeScript + Tailwind v4. Path alias `@/` → `src/`, `@contract/` → `../contract/`.

```bash
cp .env.example .env.local
npm install
npm run dev      # http://localhost:5173
npm run build    # type check + build
```

- `src/lib/api.ts` — the **only** place that calls the backend. `mock` mode reads `contract/examples`.
- `src/lib/contract.ts` — contract types (must match `backend/app/schemas.py`).
- `src/lib/format.ts` — number formatting. The backend sends raw numbers; the FE formats them.
- `src/pages/` — one file per screen in FINAL_PLAN §2. Comments `[A1]`, `[A2]`, … mark tasks in `LANES.md`.

shadcn isn't installed yet (task A0): `npx shadcn@latest init`; the aliases are already set up.
