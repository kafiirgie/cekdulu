// Jembatan dari kartu/pemeriksa ke modul analisisnya, supaya modul tidak hanya bisa dibuka dari menu.
import { Link } from 'react-router-dom'
import { labelCek } from '@/lib/labels'
import { MODUL_DARI_CEK, RUTE_MODUL } from '@/lib/modul'
import { useCek } from '@/lib/store'

export default function TautanModul({ check }: { check?: string | null }) {
  const { hasil } = useCek()
  const modul = check ? MODUL_DARI_CEK[check] : undefined
  const rute = modul && RUTE_MODUL[modul]
  if (!modul || !rute || !hasil) return null
  return (
    <Link to={`${rute}/${hasil.ticker}`} className="mt-2 inline-block text-sm font-semibold text-ink underline decoration-hl decoration-2 underline-offset-4">
      Buka {labelCek(modul)} untuk {hasil.ticker} →
    </Link>
  )
}