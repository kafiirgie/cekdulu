// Kotak lipat "Tentang modul ini" di layar alat analisis: ikon info, judul, dan panah yang berbalik saat dibuka.
import { ChevronDown, Info } from 'lucide-react'
import type { ReactNode } from 'react'

export default function TentangModul({ judul, children }: { judul: string; children: ReactNode }) {
  return (
    <details className="group mb-4 rounded-lg border border-line-2 bg-surface px-3.5 py-2.5 text-ink-2 shadow-soft">
      <summary className="flex cursor-pointer list-none items-center gap-2 text-sm font-semibold text-ink [&::-webkit-details-marker]:hidden">
        <Info className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
        <span className="flex-1">{judul}</span>
        <ChevronDown className="size-4 shrink-0 text-muted-foreground transition-transform duration-200 group-open:rotate-180" aria-hidden="true" />
      </summary>
      <div className="mt-2.5 grid gap-3 text-sm">{children}</div>
    </details>
  )
}
