// Kartu 4:5 untuk grup WhatsApp. Selalu bertema terang (data-theme) supaya gambar yang terkirim
// sama untuk semua orang, apa pun tema HP pengirimnya.
import type { Ref } from 'react'
import { Logo, Wordmark } from '@/components/Logo'
import Stamp from '@/components/Stamp'
import type { CekResponse } from '@/lib/contract'
import { dataPer } from '@/lib/format'
import { teksAtauJudul } from './kartu'

const MAKS_KLAIM = 3
const potong = (t: string, n: number) => (t.length > n ? `${t.slice(0, n - 1).trimEnd()}…` : t)

interface Props {
  hasil: CekResponse
  teksKlaim: Record<string, string>
  ref?: Ref<HTMLDivElement>
}

export default function KartuBagikan({ hasil, teksKlaim, ref }: Props) {
  const klaim = hasil.claims.slice(0, MAKS_KLAIM)
  const untold = hasil.untold[0]
  return (
    <div
      ref={ref}
      data-theme="light"
      className="kartu-bagikan relative flex aspect-[4/5] w-[360px] max-w-full flex-col overflow-hidden rounded-[20px] bg-page bg-[radial-gradient(var(--cd-dot)_1px,transparent_1.3px)] bg-[size:16px_16px] p-[22px] text-ink"
    >
      <Logo className="absolute -right-10 -bottom-10 size-[210px] rotate-[-14deg] opacity-[0.08]" />
      <div className="flex items-center gap-2">
        <Logo className="size-6" />
        <Wordmark className="text-base" />
        <span className="ml-auto font-mono text-xs font-semibold">{hasil.ticker}</span>
      </div>
      <h4 className="mt-4 mb-3 text-lg leading-[1.22] font-bold tracking-[-0.025em]">
        {klaim.length ? `Klaim soal ${hasil.ticker} yang beredar di grup, sudah dicek ke data:` : hasil.summary}
      </h4>
      <div className="grid content-start gap-2">
        {klaim.map((c, i) => (
          <div key={i} className="flex items-center justify-between gap-2.5 rounded-[10px] border border-line bg-surface px-2.5 py-2 shadow-soft">
            <span className="text-[13px] leading-tight font-semibold">“{potong(teksAtauJudul(c, teksKlaim), 60)}”</span>
            <Stamp verdict={c.verdict} miring={-4} className="flex-none text-[11px]" />
          </div>
        ))}
      </div>
      {untold && (
        <p className="mt-3 mb-0 text-xs leading-snug text-ink-2">
          <b className="text-ink">Yang tidak diceritakan:</b> {potong(untold.headline, 90)}
          {hasil.untold.length > 1 && ` (+${hasil.untold.length - 1} lainnya)`}
        </p>
      )}
      <div className="relative mt-auto flex justify-between gap-2 pt-3 text-[10.5px] text-muted-foreground">
        <span>Data dari Sectors{dataPer(hasil.data_as_of)}</span>
        <span>Bukan saran investasi</span>
      </div>
    </div>
  )
}
