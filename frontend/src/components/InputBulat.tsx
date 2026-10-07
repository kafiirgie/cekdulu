// Kolom isian berbentuk pil (panel Tanya, pencarian kode saham di Radar).
import type { ComponentProps } from 'react'
import { cn } from '@/lib/utils'

export default function InputBulat({ className, ...props }: ComponentProps<'input'>) {
  return (
    <input
      className={cn('min-w-0 flex-1 rounded-full border border-line-2 bg-surface px-4 py-2 text-[15px] outline-none focus:border-ink-2', className)}
      {...props}
    />
  )
}
