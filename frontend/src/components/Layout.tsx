import { Link, Outlet } from 'react-router-dom'
import { API_MODE } from '@/lib/api'

export default function Layout() {
  return (
    <div className="mx-auto min-h-dvh max-w-md px-4 pb-16">
      <header className="flex items-center justify-between py-4">
        <Link to="/" className="text-xl font-bold tracking-tight">cek dulu.</Link>
        <nav className="flex gap-3 text-sm">
          <Link to="/alat/free-float">Alat</Link>
          <Link to="/metodologi">Metodologi</Link>
        </nav>
      </header>
      {API_MODE === 'mock' && (
        <p className="mb-3 rounded bg-amber-100 px-2 py-1 text-xs text-amber-900">
          Mode mock: data contoh dari contract/examples
        </p>
      )}
      <Outlet />
      <footer className="mt-12 text-center text-xs text-neutral-500">Data dari Sectors · Bukan saran investasi</footer>
    </div>
  )
}
