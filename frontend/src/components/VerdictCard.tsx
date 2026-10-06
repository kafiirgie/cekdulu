// Kartu vonis. Versi kerangka — tampilan final dipindah dari prototipe (tugas A2).
import type { Card } from '@/lib/contract'
import { fmt } from '@/lib/format'
import { VERDICT_COLOR, VERDICT_LABEL } from '@/lib/labels'

export default function VerdictCard({ card, claimText }: { card: Card; claimText?: string }) {
  return (
    <article className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
      {claimText && <p className="mb-2 text-sm italic text-neutral-500">“{claimText}”</p>}
      <span
        className="inline-block -rotate-2 rounded border-2 px-2 py-0.5 text-xs font-bold uppercase"
        style={{ color: VERDICT_COLOR[card.verdict], borderColor: VERDICT_COLOR[card.verdict] }}
      >
        {VERDICT_LABEL[card.verdict]}
      </span>
      <h3 className="mt-2 font-semibold">{card.headline}</h3>
      {card.reason && <p className="mt-1 text-sm text-neutral-700">{card.reason}</p>}
      {card.evidence.length > 0 && (
        <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
          {card.evidence.map((e) => (
            <div key={e.label} className="rounded bg-neutral-50 p-2">
              <dt className="text-xs text-neutral-500">{e.label}</dt>
              <dd className="font-semibold">{fmt(e.value, e.fmt)}</dd>
            </div>
          ))}
        </dl>
      )}
      {card.rule_id && (
        <details className="mt-3 text-xs text-neutral-600">
          <summary className="cursor-pointer">Lihat aturannya ({card.rule_id})</summary>
          <p className="mt-1">{card.rule_text}</p>
        </details>
      )}
      {card.sources.length > 0 && (
        <p className="mt-2 text-xs text-neutral-500">
          Sumber: {card.sources.map((s) => `${s.name}${s.as_of ? ` (${s.as_of})` : ''}`).join(' · ')}
        </p>
      )}
    </article>
  )
}
