// Tautan kembali dengan panah kiri; panahnya dari sini, pemanggil cukup memberi teks.
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import Panah from '@/components/Panah'

export default function TautanKembali({ ke = '/cek', children = 'Kembali' }: { ke?: string; children?: ReactNode }) {
  return (
    <Link to={ke} className="inline-flex items-center gap-1.5 px-2 py-1.5 font-semibold text-ink-2 hover:text-ink">
      <Panah arah="kiri" />
      {children}
    </Link>
  )
}
