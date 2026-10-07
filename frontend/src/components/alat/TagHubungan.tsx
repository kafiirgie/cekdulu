import { TagDasar } from '@/components/StatusIkon'
import type { KomoditasItem } from '@/lib/contract'

// Kekuatan hubungan bukan baik/buruk, jadi tidak memakai warna vonis.
const GAYA: Record<KomoditasItem['kategori'], string> = {
  lemah: 'border-transparent bg-surface-3 text-ink-2',
  sedang: 'border-line-2 text-ink',
  'cukup kuat': 'border-ink text-ink',
}

/** Kategori hubungan saham–komoditas menurut aturan K-2 (lemah / sedang / cukup kuat). */
export default function TagHubungan({ kategori }: { kategori: KomoditasItem['kategori'] }) {
  return <TagDasar kelas={GAYA[kategori]}>Hubungan {kategori}</TagDasar>
}
