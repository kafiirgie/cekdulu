// Kartu vonis di layar Hasil. Urutan baca: vonis → yang ditemukan → penjelasan → angka pendukung (+ sumber),
// lalu "Cara menilai" (aturan) di balik satu klik supaya kartu tidak terasa teknis di awal.
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
import { fmt, tanggalDalamTeks } from '@/lib/format'

// Daftar angka panjang (mis. transaksi orang dalam) dipotong dulu supaya kartu tetap ringkas.
const ANGKA_AWAL = 4

function AngkaPendukung({ card }: { card: Card }) {
  const [semua, setSemua] = useState(false)
  const angka = semua ? card.evidence : card.evidence.slice(0, ANGKA_AWAL)
  const sisa = card.evidence.length - ANGKA_AWAL
  return (
    <div className="mt-4">
      <h4 className="m-0 mb-2 text-[13px] font-bold">Angka pendukung</h4>
      <ul className={`m-0 grid list-none gap-2 p-0 ${card.evidence.length > 1 ? 'grid-cols-2' : ''}`}>
        {angka.map((e) => (
          <li key={e.label} className="rounded-[10px] border border-line bg-surface-2 px-3 py-2.5">
            <span className="block text-[12.5px] leading-snug text-ink-2">{tanggalDalamTeks(e.label)}</span>
            <b className="mt-0.5 block font-mono text-[16px] font-semibold text-ink tabular-nums">{fmt(e.value, e.fmt)}</b>
          </li>
        ))}
      </ul>
      {sisa > 0 && (
        <button onClick={() => setSemua(!semua)} className="mt-2 text-[13px] font-semibold text-ink-2 underline underline-offset-2 hover:text-ink">
          {semua ? 'Tampilkan lebih sedikit' : `Lihat ${sisa} angka lainnya`}
        </button>
      )}
    </div>
  )
}

function TombolCaraMenilai({ buka, onClick }: { buka: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} aria-expanded={buka} className="inline-flex items-center gap-1.5 py-1.5 text-sm font-semibold text-ink-2 hover:text-ink">
      <BookOpen aria-hidden="true" className="size-4" />
      Cara menilai
      <ChevronDown aria-hidden="true" className={`size-4 transition-transform duration-200 ${buka ? 'rotate-180' : ''}`} />
    </button>
  )
}

function KotakAturan({ card }: { card: Card }) {
  return (
    <div className="mt-1.5 mb-1 rounded-[10px] border border-dashed border-line-2 bg-surface-2 px-3.5 py-3 text-sm leading-relaxed">
      <span className="font-mono text-[11.5px] font-semibold text-muted-foreground">Aturan {card.rule_id}</span>
      {card.rule_text && <span className="mt-1 block text-ink">{card.rule_text}</span>}
      <Link to="/metodologi" className="mt-2 inline-block text-[13px] font-semibold text-ink-2 underline underline-offset-2 hover:text-ink">
        Lihat semua aturan
      </Link>
    </div>
  )
}

/** `item.judul`: baris kecil di atas ("Klaim 1" untuk klaim, nama kartu untuk "Yang tidak diceritakan"). */
export default function VerdictCard({ item }: { item: ItemKartu }) {
  const { card, judul, kutipan, kunciTanya } = item
  const [aturan, setAturan] = useState(false)
  return (
    <article data-verdict={card.verdict} className="dicap relative rounded-lg border border-line bg-surface px-[18px] pt-[18px] pb-3 shadow-soft">
      <div className="flex items-start justify-between gap-3.5">
        <p className="m-0 min-w-0 text-[13.5px] text-muted-foreground">
          <span className="mb-0.5 block text-[11.5px] font-semibold">{judul}</span>
          {kutipan && <q className="font-semibold text-ink-2">{kutipan}</q>}
        </p>
        <Stamp verdict={card.verdict} className="mt-1 flex-none" />
      </div>
      <div className={kutipan ? 'mt-3.5 border-t border-line pt-3.5' : 'mt-2'}>
        {kutipan && <p className="m-0 mb-1 text-[12.5px] font-bold text-[var(--c)]">Yang ditemukan</p>}
        <h3 className="m-0 max-w-[40ch] text-[17.5px] leading-[1.32] font-bold tracking-[-0.02em]">{card.headline}</h3>
        {card.reason && <p className="mt-2 mb-0 text-[15px] leading-relaxed text-ink-2">{tanggalDalamTeks(card.reason)}</p>}
      </div>
      {card.evidence.length > 0 && <AngkaPendukung card={card} />}
      {card.chart && <Grafik chart={card.chart} />}
      <Sumber sources={card.sources} />
      <TautanModul check={card.check} />
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2.5 border-t border-line pt-2">
        {card.rule_id ? <TombolCaraMenilai buka={aturan} onClick={() => setAturan(!aturan)} /> : <span />}
        {kunciTanya && <PanelTanya item={item} kunci={kunciTanya} />}
      </div>
      {aturan && <KotakAturan card={card} />}
    </article>
  )
}
