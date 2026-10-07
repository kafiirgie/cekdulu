// Ikon status pemeriksa (formulir berjalan, ringkasan formulir, formulir inspeksi).
import type { FormStatus } from '@/lib/contract'
import { STATUS_LABEL } from '@/lib/labels'
import { cn } from '@/lib/utils'

export type StatusLangkah = FormStatus | 'jalan' | 'antre'

const GAYA: Record<StatusLangkah, { ikon: string; kelas: string }> = {
  temuan: { ikon: '!', kelas: 'border-menyesatkan bg-surface text-menyesatkan' },
  aman: { ikon: '✓', kelas: 'border-ink bg-ink text-page' },
  modul_aktif: { ikon: '', kelas: 'border-hl bg-hl shadow-[0_0_0_3px_var(--cd-hl-soft)]' },
  tidak_relevan: { ikon: '–', kelas: 'border-dashed text-muted-foreground' },
  data_kurang: { ikon: '?', kelas: 'rotate-45 rounded-[5px] text-ink-2 [&>i]:-rotate-45' },
  gagal: { ikon: '✕', kelas: 'border-tidak-sesuai text-tidak-sesuai' },
  jalan: { ikon: '', kelas: 'animate-spin border-ink border-r-transparent motion-reduce:animate-none' },
  antre: { ikon: '', kelas: 'text-line-2' },
}

export default function StatusIkon({ status, className }: { status: StatusLangkah; className?: string }) {
  const g = GAYA[status]
  return (
    <span
      aria-hidden="true"
      className={cn(
        'grid size-[22px] flex-none place-items-center rounded-full border-[1.6px] border-current text-[11.5px] leading-none font-bold',
        g.kelas,
        className,
      )}
    >
      <i className="not-italic">{g.ikon}</i>
    </span>
  )
}

const GAYA_TAG: Record<FormStatus, string> = {
  temuan: 'border-menyesatkan text-menyesatkan',
  aman: 'border-transparent bg-surface-3 text-ink-2',
  modul_aktif: 'border-hl bg-hl-soft text-ink',
  tidak_relevan: 'border-dashed border-line-2 text-muted-foreground',
  data_kurang: 'border-line-2 bg-surface-3 text-ink-2',
  gagal: 'border-tidak-sesuai text-tidak-sesuai',
}

/** Label status berbentuk pil, mis. "Ada temuan". */
export function TagStatus({ status }: { status: FormStatus }) {
  return (
    <span className={cn('inline-flex items-center rounded-full border px-2.5 py-[3px] text-[11px] font-bold whitespace-nowrap', GAYA_TAG[status])}>
      {STATUS_LABEL[status]}
    </span>
  )
}
