// Kartu vonis di layar Hasil: cap, kalimat, sumber; "Lihat detail" membuka alasan, aturan, angka, dan grafik.
import { useState } from 'react'
import Grafik from '@/components/hasil/Grafik'
import type { ItemKartu } from '@/components/hasil/kartu'
import PanelTanya from '@/components/hasil/PanelTanya'
import Sumber from '@/components/hasil/Sumber'
import TautanModul from '@/components/hasil/TautanModul'
import Stamp from '@/components/Stamp'
import type { Card } from '@/lib/contract'
import { fmt } from '@/lib/format'
import { VERDICT_LABEL } from '@/lib/labels'


function Aturan({ card, className }: { card: Card; className: string }) {
  if (!card.rule_id) return null
  return (
    <span className={`block text-[12.5px] text-muted-foreground ${className}`}>
      Aturan {card.rule_id}
      {card.rule_text && `: ${card.rule_text}`}
    </span>
  )
}

function Detail({ card }: { card: Card }) {
  return (
    <div className="mt-1 text-[15px] text-ink-2">
      {card.reason ? (
        <div data-verdict={card.verdict} className="mt-2.5 mb-1 rounded-[10px] border border-l-[3px] border-line-2 border-l-[var(--c)] bg-surface-2 px-3 py-2.5 text-ink">
          <b className="font-stamp text-[15px] tracking-[0.06em] text-[var(--c)] uppercase">{VERDICT_LABEL[card.verdict]}</b> karena: {card.reason}
          <Aturan card={card} className="mt-1.5" />
        </div>
      ) : (
        <Aturan card={card} className="mt-2.5 mb-1" />
      )}
      {(card.evidence.length > 0 || card.chart) && (
        <div className="mt-2.5 rounded-md border border-line bg-surface-2 p-3.5">
          {card.evidence.length > 0 && (
            <table className="w-full border-collapse font-mono text-[12.5px] tabular-nums">
              <tbody>
                {card.evidence.map((e) => (
                  <tr key={e.label} className="border-b border-line last:border-0">
                    <td className="py-1.5">{e.label}</td>
                    <td className="py-1.5 text-right font-semibold text-ink">{fmt(e.value, e.fmt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {card.chart && <Grafik chart={card.chart} />}
        </div>
      )}
    </div>
  )
}

/** `item.judul`: baris kecil di atas ("Klaim 1" untuk klaim, nama kartu untuk "Yang tidak diceritakan"). */
export default function VerdictCard({ item }: { item: ItemKartu }) {
  const { card, judul, kutipan, kunciTanya } = item
  const [buka, setBuka] = useState(false)
  const adaDetail = Boolean(card.reason || card.rule_id || card.evidence.length || card.chart)
  return (
    <article className="dicap relative rounded-lg border border-line bg-surface px-[18px] pt-[18px] pb-3 shadow-soft">
      <div className="flex items-start justify-between gap-3.5">
        <p className="m-0 min-w-0 text-[13.5px] text-muted-foreground">
          <span className="mb-0.5 block text-[11.5px] font-semibold">{judul}</span>
          {kutipan && <q className="font-semibold text-ink-2">{kutipan}</q>}
        </p>
        <Stamp verdict={card.verdict} className="mt-1 flex-none" />
      </div>
      <h3 className="mt-2.5 mb-0 max-w-[34ch] text-[17.5px] leading-[1.32] font-bold tracking-[-0.02em]">{card.headline}</h3>
      <Sumber sources={card.sources} />
      <TautanModul check={card.check} />
      <div className="mt-2 flex items-center justify-between gap-2.5">
        {adaDetail && (
          <button
            onClick={() => setBuka(!buka)}
            aria-expanded={buka}
            className="inline-flex items-center gap-1.5 py-1.5 text-sm font-semibold text-ink-2 hover:text-ink"
          >
            {buka ? 'Tutup detail' : 'Lihat detail'}
            <span aria-hidden="true" className={buka ? 'rotate-180' : ''}>⌄</span>
          </button>
        )}
        {kunciTanya && <PanelTanya item={item} kunci={kunciTanya} />}
      </div>
      {buka && <Detail card={card} />}
    </article>
  )
}
