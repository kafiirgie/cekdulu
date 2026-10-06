import { Moon, Sun } from 'lucide-react'
import { Link, Outlet } from 'react-router-dom'
import { Logo, Wordmark } from '@/components/Logo'
import { InkFilter } from '@/components/Stamp'
import { Button } from '@/components/ui/button'
import { API_MODE } from '@/lib/api'
import { useTema } from '@/lib/tema'

function TombolTema() {
  const { tema, ganti } = useTema()
  const gelap = tema === 'dark'
  return (
    <Button variant="outline" size="icon" onClick={ganti} aria-label={gelap ? 'Ganti ke mode terang' : 'Ganti ke mode gelap'}>
      {gelap ? <Sun /> : <Moon />}
    </Button>
  )
}

/** Kolom sempit (mobile-first) untuk layar alat; Beranda memakai lebar penuh seperti prototipe. */
export function KolomSempit() {
  return (
    <div className="mx-auto max-w-md">
      <Outlet />
    </div>
  )
}

export default function Layout() {
  return (
    <div className="mx-auto min-h-dvh max-w-[1120px] px-4 sm:px-5">
      <InkFilter />
      <header className="flex items-center justify-between gap-3 py-4">
        <Link to="/" aria-label="cek dulu, halaman awal" className="flex items-center gap-2.5">
          <Logo />
          <Wordmark />
        </Link>
        <nav className="flex items-center gap-1.5 text-[14.5px] font-semibold text-ink-2">
          <Link to="/alat/free-float" className="px-2 py-1.5 hover:text-ink">Alat analisis</Link>
          <Link to="/metodologi" className="hidden px-2 py-1.5 hover:text-ink sm:block">Metodologi</Link>
          <TombolTema />
        </nav>
      </header>
      {API_MODE === 'mock' && (
        <p className="mb-3 inline-block rounded-md border border-dashed border-line-2 px-2 py-1 font-mono text-[10px] uppercase tracking-[0.08em] text-muted-foreground">
          Mode mock · data contoh dari contract/examples
        </p>
      )}
      <main>
        <Outlet />
      </main>
      <footer className="mt-12 flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-t border-line pt-6 pb-9 text-[13px] text-muted-foreground">
        <span>
          Data dari <b className="text-ink-2">Sectors</b> · Bukan saran investasi
        </span>
        <span>
          <Link to="/alat/free-float" className="hover:text-ink">Alat analisis</Link> ·{' '}
          <Link to="/metodologi" className="hover:text-ink">Metodologi</Link>
        </span>
      </footer>
    </div>
  )
}
