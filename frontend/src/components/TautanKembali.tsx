import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

export default function TautanKembali({ ke = '/cek', children = 'Kembali' }: { ke?: string; children?: ReactNode }) {
  return (
    <Link to={ke} className="px-2 py-1.5 font-semibold text-ink-2 hover:text-ink">
      {children}
    </Link>
  )
}
