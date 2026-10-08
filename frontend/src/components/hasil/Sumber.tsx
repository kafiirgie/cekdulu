import type { Source } from '@/lib/contract'
import { tanggal, tanggalDalamTeks } from '@/lib/format'

/** Selalu tampil: setiap angka di layar wajib punya sumber + tanggal. */
export default function Sumber({ sources }: { sources: Source[] }) {
  if (!sources.length) return null
  return (
    <p className="mt-2 mb-0 font-mono text-[11.5px] text-muted-foreground">
      Sumber: {sources.map((s) => (s.as_of ? `${tanggalDalamTeks(s.name)} (${tanggal(s.as_of)})` : tanggalDalamTeks(s.name))).join(' · ')}
    </p>
  )
}
