// Kartu vonis. Versi kerangka — tampilan final dipindah dari prototipe (tugas A2).
import Stamp from '@/components/Stamp'
import type { Card } from '@/lib/contract'
import { fmt } from '@/lib/format'

export default function VerdictCard({ card, claimText }: { card: Card; claimText?: string }) {
  return (
    <article className="rounded-xl border border-line bg-surface p-4 shadow-soft">
      {claimText && <p className="mb-2 text-sm italic text-muted-foreground">“{claimText}”</p>}
      <Stamp verdict={card.verdict} className="text-xs" />
      <h3 className="mt-2 font-semibold">{card.headline}</h3>
      {card.reason && <p className="mt-1 text-sm text-ink-2">{card.reason}</p>}
      {card.evidence.length > 0 && (
        <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
          {card.evidence.map((e) => (
            <div key={e.label} className="rounded bg-surface-2 p-2">
              <dt className="text-xs text-muted-foreground">{e.label}</dt>
              <dd className="font-semibold">{fmt(e.value, e.fmt)}</dd>
            </div>
          ))}
        </dl>
      )}
      {card.rule_id && (
        <details className="mt-3 text-xs text-muted-foreground">
          <summary className="cursor-pointer">Lihat aturannya ({card.rule_id})</summary>
          <p className="mt-1">{card.rule_text}</p>
        </details>
      )}
      {card.sources.length > 0 && (
        <p className="mt-2 text-xs text-muted-foreground">
          Sumber: {card.sources.map((s) => `${s.name}${s.as_of ? ` (${s.as_of})` : ''}`).join(' · ')}
        </p>
      )}
    </article>
  )
}
