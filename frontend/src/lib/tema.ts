// Tema terang/gelap. Tanpa pilihan tersimpan, ikut pengaturan perangkat.
// Atribut awal dipasang skrip di index.html (kunci harus sama) supaya tidak berkedip.
import { useEffect, useState } from 'react'

export type Tema = 'light' | 'dark'

const KUNCI = 'cekdulu_tema'

function tersimpan(): Tema | null {
  try {
    const t = localStorage.getItem(KUNCI)
    return t === 'light' || t === 'dark' ? t : null
  } catch {
    return null
  }
}

export function useTema() {
  const [tema, setTema] = useState<Tema>(() => (document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'))

  function terapkan(t: Tema) {
    document.documentElement.dataset.theme = t
    setTema(t)
  }

  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const ikutPerangkat = (e: MediaQueryListEvent) => {
      if (!tersimpan()) terapkan(e.matches ? 'dark' : 'light')
    }
    media.addEventListener('change', ikutPerangkat)
    return () => media.removeEventListener('change', ikutPerangkat)
  }, [])

  function ganti() {
    const t = tema === 'dark' ? 'light' : 'dark'
    terapkan(t)
    try {
      localStorage.setItem(KUNCI, t)
    } catch {
      // Penyimpanan diblokir (mode privat): tema tetap berganti untuk sesi ini.
    }
  }

  return { tema, ganti }
}
