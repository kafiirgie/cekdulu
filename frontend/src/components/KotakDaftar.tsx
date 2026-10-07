// Kotak berkepala untuk daftar baris (formulir berjalan, grup formulir inspeksi).
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface Props {
  judul: string
  keterangan: string
  className?: string
  children: ReactNode
}

export default function KotakDaftar({ judul, keterangan, className, children }: Props) {
  return (
    <div className={cn('overflow-hidden rounded-xl border border-line bg-surface shadow-soft', className)}>
      <div className="flex items-center justify-between gap-2.5 border-b border-line bg-surface-2 px-4 py-3 text-[13px] font-bold">
        {judul} <span className="font-medium text-muted-foreground">{keterangan}</span>
      </div>
      <ul className="m-0 list-none p-0">{children}</ul>
    </div>
  )
}
