// Istilah bergaris titik-titik dengan ⓘ; diketuk → penjelasan satu kalimat (popover, jalan juga di layar sentuh).
import type { ReactNode } from 'react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { ISTILAH, type KunciIstilah } from '@/lib/istilah'

export default function Istilah({ k, children }: { k: KunciIstilah; children?: ReactNode }) {
  const istilah = ISTILAH[k]
  return (
    <Popover>
      <PopoverTrigger className="inline cursor-help font-semibold underline decoration-dotted underline-offset-4">
        {children ?? istilah.nama}
        <span aria-hidden="true" className="ml-0.5 text-[0.8em] text-muted-foreground">
          ⓘ
        </span>
        <span className="sr-only"> (lihat arti)</span>
      </PopoverTrigger>
      <PopoverContent className="w-72 border-0 bg-pop text-sm leading-relaxed text-on-pop">
        <b className="block text-hl">{istilah.nama}</b>
        {istilah.arti}
      </PopoverContent>
    </Popover>
  )
}
