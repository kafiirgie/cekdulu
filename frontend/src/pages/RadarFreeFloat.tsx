// Layar 10 — Alat analisis: Radar Free Float. [A4] daftar → detail → jembatan ke cek klaim.
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { FreeFloatList } from '@/lib/contract'
import { fmt, rupiah } from '@/lib/format'

export default function RadarFreeFloat() {
  const [data, setData] = useState<FreeFloatList | null>(null)
  useEffect(() => {
    api.freeFloat().then(setData)
  }, [])
  if (!data) return null
  return (
    <section>
      <h2 className="text-lg font-semibold">Radar Free Float</h2>
      <p className="text-sm text-muted-foreground">Saham yang wajib menambah porsi publik, dan seberapa berat tekanannya.</p>
      <ul className="mt-3 space-y-2 text-sm">
        {data.items.slice(0, 50).map((i) => (
          <li key={i.ticker} className="rounded-lg bg-surface p-3 shadow-soft">
            <b>{i.ticker}</b> · free float {fmt(i.free_float, 'pct')} → target {fmt(i.target, 'pct')} ({i.tenggat})
            <br />
            Harus dilepas {i.nilai_dilepas != null ? rupiah(i.nilai_dilepas) : '-'} · hari serap{' '}
            {i.hari_serap == null ? 'tidak bisa dihitung' : i.hari_serap > 1000 ? '> 1.000' : Math.round(i.hari_serap)}{' '}
            · {i.tekanan ?? '-'}
          </li>
        ))}
      </ul>
    </section>
  )
}
