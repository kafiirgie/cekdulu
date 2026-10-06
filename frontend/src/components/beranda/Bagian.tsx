// Potongan yang berulang di Beranda: pil, judul bagian, dan catatan sumber contoh.
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { SUMBER_CONTOH } from './contoh'

/** Pil kuning dipakai di dalam bingkai berlatar krem (sesuai prototipe aksen Kuning). */
export function Pil({ children, kuning = false }: { children: ReactNode; kuning?: boolean }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-3 py-1 text-[12.5px] font-semibold shadow-soft',
        kuning ? 'border-hl-edge bg-hl text-on-hl' : 'border-line-2 bg-surface text-ink-2',
      )}
    >
      {children}
    </span>
  )
}

export function CatatanSumber() {
  return <p className="mt-3 text-center font-mono text-[11px] text-muted-foreground">{SUMBER_CONTOH}</p>
}

interface Props {
  pil: string
  judul: ReactNode
  sub?: string
  pilKuning?: boolean
}

export default function JudulBagian({ pil, judul, sub, pilKuning = false }: Props) {
  return (
    <div className="mb-[26px] text-center">
      <Pil kuning={pilKuning}>{pil}</Pil>
      <h2 className="mt-3.5 text-[clamp(26px,3.6vw,38px)] leading-[1.12] font-bold tracking-[-0.035em] text-balance">{judul}</h2>
      {sub && <p className="mx-auto mt-2 max-w-[34rem] text-muted-foreground">{sub}</p>}
    </div>
  )
}
