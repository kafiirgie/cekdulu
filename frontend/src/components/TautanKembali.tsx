import { Link } from 'react-router-dom'

export default function TautanKembali({ ke = '/cek' }: { ke?: string }) {
  return (
    <Link to={ke} className="px-2 py-1.5 font-semibold text-ink-2 hover:text-ink">
      Kembali
    </Link>
  )
}
