// Layar 11 — Metodologi. Isi aturan diambil dari contract/rules.json (satu sumber kebenaran).
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { Catalog } from '@/lib/contract'

export default function Metodologi() {
  const [cat, setCat] = useState<Catalog | null>(null)
  useEffect(() => {
    api.rules().then(setCat)
  }, [])
  if (!cat) return null
  return (
    <section>
      <h2 className="text-lg font-semibold">Aturan yang memutuskan, bukan AI</h2>
      <ul className="mt-3 space-y-3 text-sm">
        {cat.rules.map((r) => (
          <li key={r.id} className="rounded-lg bg-white p-3 shadow-sm">
            <b>{r.id}</b> {r.status === 'usulan' && <em className="text-amber-700">(usulan)</em>}
            <p className="mt-1">{r.text}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
