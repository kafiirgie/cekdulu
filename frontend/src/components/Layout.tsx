import { Moon, Sun } from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { Logo, Wordmark } from '@/components/Logo'
import { InkFilter } from '@/components/Stamp'
import { Button } from '@/components/ui/button'
import { API_MODE } from '@/lib/api'
import { useTema } from '@/lib/tema'
import { cn } from '@/lib/utils'

// NavLink ikut aktif di halaman turunannya (mis. /cek/hasil, /alat/komoditas).
const MENU = [
  { ke: '/cek', label: 'Cek klaim' },
  { ke: '/alat', label: 'Alat analisis' },
  { ke: '/metodologi', label: 'Metodologi' },
  { ke: '/kamus', label: 'Kamus' },
]

function TombolTema() {
  const { tema, ganti } = useTema()
  const gelap = tema === 'dark'
  return (
    <Button variant="outline" size="icon" onClick={ganti} aria-label={gelap ? 'Ganti ke mode terang' : 'Ganti ke mode gelap'}>
      {gelap ? <Sun /> : <Moon />}
    </Button>
  )
}

/** Kolom baca untuk layar alat (selebar layar di HP, dibatasi di laptop); Beranda memakai lebar penuh seperti prototipe. */
export function KolomSempit() {
  return (
    <div className="mx-auto max-w-2xl">
      <Outlet />
    </div>
  )
}

export default function Layout() {
  return (
    <div className="mx-auto min-h-dvh max-w-[1120px] px-5 sm:px-6">
      <InkFilter />
      {/* Di layar sempit menu turun ke baris kedua supaya keempatnya tetap terlihat. */}
      <header className="flex flex-wrap items-center gap-x-3 gap-y-2 py-4">
        <Link to="/" aria-label="cek dulu, halaman awal" className="flex items-center gap-2.5">
          <Logo />
          <Wordmark />
        </Link>
        <nav
          aria-label="Menu utama"
          className="order-last -mx-1 flex w-full gap-1 overflow-x-auto text-[13px] font-semibold text-ink-2 sm:order-none sm:mx-0 sm:ml-auto sm:w-auto sm:text-[14.5px]"
        >
          {MENU.map(({ ke, label }) => (
            <NavLink
              key={ke}
              to={ke}
              className={({ isActive }) =>
                cn('shrink-0 rounded-full px-2.5 py-1.5 hover:text-ink sm:px-3', isActive && 'bg-hl-soft text-ink')
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto sm:ml-0">
          <TombolTema />
        </div>
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
        <span className="flex flex-wrap gap-x-3">
          {MENU.map(({ ke, label }) => (
            <Link key={ke} to={ke} className="hover:text-ink">
              {label}
            </Link>
          ))}
        </span>
      </footer>
    </div>
  )
}
