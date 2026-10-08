// Kartu vonis di layar Hasil: cap, kalimat, sumber; "Lihat detail" membuka alasan, angka, grafik, dan aturan.
import { BookOpen, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import Grafik from '@/components/hasil/Grafik'
import type { ItemKartu } from '@/components/hasil/kartu'
import PanelTanya from '@/components/hasil/PanelTanya'
import Sumber from '@/components/hasil/Sumber'
import TautanModul from '@/components/hasil/TautanModul'
import Stamp from '@/components/Stamp'
import type { Card } from '@/lib/contract'
import { fmt } from '@/lib/format'
import { VERDICT_LABEL } from '@/lib/labels'

// Rujukan aturan disimpan di balik satu klik supaya kartu tidak terasa teknis di awal.
function Aturan({ card }: { card: Card }) {
  const [buka, setBuka] = useState(false)
  if (!card.rule_id) return null
  return (
    <div className="mt-2.5">
      <button
        onClick={() => setBuka(!buka)}
        aria-expanded={buka}
        className="inline-flex items-center gap-1.5 py-1 text-[13px] font-semibold text-muted-foreground hover:text-ink"
      >
        <BookOpen aria-hidden="true" className="size-3.5" />
        Aturan yang dipakai
        <ChevronDown aria-hidden="true" className={`size-3.5 transition-transform duration-200 ${buka ? 'rotate-180' : ''}`} />
      </button>
      {buka && (
        <div className="mt-1.5 rounded-[10px] border border-dashed border-line-2 bg-surface-2 px-3.5 py-3 text-sm leading-relaxed">
          <span className="font-mono text-[11.5px] font-semibold text-muted-foreground">Aturan {card.rule_id}</span>
          {card.rule_text && <span className="mt-1 block text-ink">{card.rule_text}</span>}
          <Link to="/metodologi" className="mt-2 inline-block text-[13px] font-semibold text-ink-2 underline underline-offset-2 hover:text-ink">
            Lihat semua aturan
          </Link>
        </div>
      )}
    </div>
  )
}

function Detail({ card }: { card: Card }) {
  return (
    <div className="mt-1 text-[15px] text-ink-2">
      {card.reason && (
        <div data-verdict={card.verdict} className="mt-2.5 mb-1 rounded-[10px] border border-l-[3px] border-line-2 border-l-[var(--c)] bg-surface-2 px-3 py-2.5 text-ink">
          <b className="font-stamp text-[15px] tracking-[0.06em] text-[var(--c)] uppercase">{VERDICT_LABEL[card.verdict]}</b> karena: {card.reason}
        </div>
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
      <Aturan card={card} />
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
            <ChevronDown aria-hidden="true" className={`size-4 transition-transform duration-200 ${buka ? 'rotate-180' : ''}`} />
          </button>
        )}
        {kunciTanya && <PanelTanya item={item} kunci={kunciTanya} />}
      </div>
      {buka && <Detail card={card} />}
    </article>
  )
}
