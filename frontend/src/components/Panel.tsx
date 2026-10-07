// Kotak isi di layar detail (detail pemeriksa, detail Radar Free Float).
import type { ReactNode } from 'react'

export default function Panel({ judul, children }: { judul?: string; children: ReactNode }) {
  return (
    <div className="mb-3.5 rounded-xl border border-line bg-surface p-[18px] shadow-soft">
      {judul && <h2 className="m-0 mb-2.5 text-sm font-bold text-muted-foreground">{judul}</h2>}
      {children}
    </div>
  )
}
