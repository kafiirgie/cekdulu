// Logo + wordmark dari prototipe iterasi 3 (aksen Kuning). public/favicon.svg memakai gambar yang sama.
import { cn } from '@/lib/utils'

export function Logo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={cn('size-[30px] -rotate-[8deg]', className)} aria-hidden="true">
      <circle cx="32" cy="32" r="29" fill="#ffb938" stroke="#18181b" strokeWidth="3.2" />
      <circle cx="32" cy="32" r="23.5" fill="none" stroke="#18181b" strokeWidth="1.6" strokeDasharray="2.4 3" opacity=".7" />
      <path d="M20.5 33.5l7.5 7.5 15.5-17" fill="none" stroke="#18181b" strokeWidth="5.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn('whitespace-nowrap text-[19px] font-extrabold tracking-[-0.035em]', className)}>
      cek dulu
      <b className="ml-[0.06em] inline-block size-[0.3em] rounded-full bg-ink shadow-[0_0_0_3px_var(--cd-hl)]" />
    </span>
  )
}
