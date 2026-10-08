// Daftar aturan tertulis dari rules.json (id, status usulan, teks), dipakai di layar detail dan modul.
import type { Rule } from '@/lib/contract'

export default function DaftarAturan({ aturan }: { aturan: Rule[] }) {
  if (!aturan.length) return <p className="m-0 text-sm text-ink-2">Belum ada aturan tertulis untuk pemeriksaan ini.</p>
  return (
    <ul className="m-0 grid list-none gap-2 p-0">
      {aturan.map((r) => (
        <li key={r.id} className="rounded-[10px] border border-dashed border-line-2 bg-surface-2 px-3.5 py-3 text-sm leading-relaxed">
          <span className="font-mono text-[11.5px] font-semibold text-muted-foreground">Aturan {r.id}</span>
          {r.status === 'usulan' && <span className="ml-2 text-[11px] font-semibold text-menyesatkan">usulan</span>}
          <span className="mt-1 block text-ink">{r.text}</span>
        </li>
      ))}
    </ul>
  )
}
