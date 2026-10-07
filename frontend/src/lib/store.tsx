// State satu sesi cek (teks → klaim → hasil). Sengaja sederhana: React context, tanpa library.
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from './api'
import type { CekResponse, KlaimResponse } from './contract'

interface CekState {
  text: string
  setText: (t: string) => void
  klaim: KlaimResponse | null
  setKlaim: (k: KlaimResponse | null) => void
  /** Permintaan /api/cek yang sedang/sudah berjalan untuk `klaim`. Dibaca layar Hasil. */
  cek: Promise<CekResponse> | null
  /** Mulai satu cek. Dipanggil dari aksi pengguna (bukan efek), jadi kuota terpakai tepat sekali. */
  mulaiCek: (k: KlaimResponse) => void
  hasil: CekResponse | null
  setHasil: (h: CekResponse | null) => void
}

// Disimpan per tab supaya Hasil, Formulir, dan Detail tidak hilang saat halaman di-refresh.
// Permintaan yang sedang berjalan tidak ikut disimpan: refresh di tengah pemeriksaan kembali ke Input
// alih-alih memakai kuota lagi.
const KUNCI = 'cekdulu_sesi'

interface Sesi {
  text: string
  klaim: KlaimResponse | null
  hasil: CekResponse | null
}

function bacaSesi(): Sesi {
  try {
    const s = sessionStorage.getItem(KUNCI)
    if (s) return JSON.parse(s) as Sesi
  } catch {
    // Penyimpanan diblokir atau isinya rusak: mulai sesi baru.
  }
  return { text: '', klaim: null, hasil: null }
}

const Ctx = createContext<CekState | null>(null)

export function CekProvider({ children }: { children: ReactNode }) {
  const [awal] = useState(bacaSesi)
  const [text, setText] = useState(awal.text)
  const [klaim, setKlaim] = useState(awal.klaim)
  const [cek, setCek] = useState<Promise<CekResponse> | null>(null)
  const [hasil, setHasil] = useState(awal.hasil)

  useEffect(() => {
    try {
      sessionStorage.setItem(KUNCI, JSON.stringify({ text, klaim, hasil } satisfies Sesi))
    } catch {
      // Penyimpanan diblokir (mode privat): sesi tetap jalan, hanya tidak bertahan saat refresh.
    }
  }, [text, klaim, hasil])

  const mulaiCek = useCallback((k: KlaimResponse) => {
    if (!k.ticker) return
    setKlaim(k)
    setHasil(null)
    setCek(api.cek({ ticker: k.ticker, claims: k.claims }))
  }, [])

  return (
    <Ctx.Provider value={{ text, setText, klaim, setKlaim, cek, mulaiCek, hasil, setHasil }}>{children}</Ctx.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useCek() {
  const c = useContext(Ctx)
  if (!c) throw new Error('useCek di luar CekProvider')
  return c
}
