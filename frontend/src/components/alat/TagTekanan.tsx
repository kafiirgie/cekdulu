import { TagDasar } from '@/components/StatusIkon'
import type { FreeFloatItem } from '@/lib/contract'

const GAYA: Record<NonNullable<FreeFloatItem['tekanan']>, string> = {
  ringan: 'border-transparent bg-surface-3 text-ink-2',
  sedang: 'border-menyesatkan text-menyesatkan',
  berat: 'border-tidak-sesuai text-tidak-sesuai',
}

/** Berat tekanan suplai menurut aturan R-1 (ringan / sedang / berat). */
export default function TagTekanan({ tekanan }: { tekanan: FreeFloatItem['tekanan'] }) {
  if (!tekanan) return null
  return <TagDasar kelas={GAYA[tekanan]}>Tekanan {tekanan}</TagDasar>
}