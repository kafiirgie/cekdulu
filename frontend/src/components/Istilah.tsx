// Istilah bergaris titik-titik dengan ikon info; diketuk → penjelasan satu kalimat (popover, jalan juga di layar sentuh).
import { Info } from 'lucide-react'
import type { ReactNode } from 'react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { istilah, type KunciIstilah } from '@/lib/istilah'

export default function Istilah({ k, children }: { k: KunciIstilah; children?: ReactNode }) {
  const { nama, arti } = istilah(k)
  return (
    <Popover>
      <PopoverTrigger className="inline cursor-help font-semibold underline decoration-dotted underline-offset-4">
        {children ?? nama}
        <Info aria-hidden="true" className="ml-0.5 inline-block size-[0.85em] align-[-0.08em] text-muted-foreground" />
        <span className="sr-only"> (lihat arti)</span>
      </PopoverTrigger>
      <PopoverContent className="w-72 border-0 bg-pop text-sm leading-relaxed text-on-pop">
        <b className="block text-hl">{nama}</b>
        {arti}
      </PopoverContent>
    </Popover>
  )
}
