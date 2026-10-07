// Cap vonis bergaya stempel. Gaya + warna per vonis ada di index.css (.stamp[data-verdict]);
// filter tinta #ink dipasang sekali di Layout.
import type { CSSProperties, ReactNode } from 'react'
import type { Verdict } from '@/lib/contract'
import { VERDICT_LABEL } from '@/lib/labels'
import { cn } from '@/lib/utils'

interface Props {
  verdict: Verdict
  /** Kemiringan dalam derajat. */
  miring?: number
  className?: string
  /** Teks pengganti label vonis, mis. "Kuota harian". */
  children?: ReactNode
}

export default function Stamp({ verdict, miring = -6, className, children }: Props) {
  return (
    <span className={cn('stamp', className)} data-verdict={verdict} style={{ '--r': `${miring}deg` } as CSSProperties}>
      {children ?? VERDICT_LABEL[verdict]}
    </span>
  )
}

/** Definisi filter SVG untuk efek bintik tinta pada cap. Cukup dipasang sekali per halaman. */
export function InkFilter() {
  return (
    <svg width="0" height="0" className="absolute" aria-hidden="true">
      <filter id="ink" x="-10%" y="-20%" width="120%" height="140%">
        <feTurbulence type="fractalNoise" baseFrequency=".95" numOctaves="2" seed="4" result="n" />
        <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -5 4.4" result="holes" />
        <feComposite in="SourceGraphic" in2="holes" operator="in" result="speck" />
        <feTurbulence type="fractalNoise" baseFrequency=".05" numOctaves="2" seed="9" result="w" />
        <feDisplacementMap in="speck" in2="w" scale="1.4" xChannelSelector="R" yChannelSelector="G" />
      </filter>
    </svg>
  )
}
