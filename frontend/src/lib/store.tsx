// State satu sesi cek (teks → klaim → hasil). Sengaja sederhana: React context, tanpa library.
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from './api'
import type { CekResponse, KlaimResponse } from './contract'

interface CekState {
  text: string
  setText: (t: string) => void
  klaim: KlaimResponse | null
  setKlaim: (k: KlaimResponse | null) => void
  /** Teks yang diperiksa: hasil baca screenshot kalau ada, selain itu teks yang ditempel. `span` klaim menunjuk ke sini. */
  teksAsli: string
  /** Permintaan /api/cek yang sedang/sudah berjalan untuk `klaim`. Dibaca layar Hasil. */
  cek: Promise<CekResponse> | null
  /** Mulai satu cek. Dipanggil dari aksi pengguna (bukan efek), jadi kuota terpakai tepat sekali. */
  mulaiCek: (k: KlaimResponse) => void
  hasil: CekResponse | null
  setHasil: (h: CekResponse | null) => void
}

/**
 * State yang disimpan per tab supaya Hasil, Formulir, dan Detail tidak hilang saat halaman di-refresh.
 * Satu kunci per nilai: mengetik di Input hanya menulis ulang teks, bukan seluruh hasil cek.
 */
function useTersimpan<T>(kunci: string, awal: T) {
  const [nilai, setNilai] = useState<T>(() => {
    try {
      const s = sessionStorage.getItem(kunci)
      if (s) return JSON.parse(s) as T
    } catch {
      // Penyimpanan diblokir atau isinya rusak: mulai dari awal.
    }
    return awal
  })
  useEffect(() => {
    try {
      sessionStorage.setItem(kunci, JSON.stringify(nilai))
    } catch {
      // Penyimpanan diblokir (mode privat): sesi tetap jalan, hanya tidak bertahan saat refresh.
    }
  }, [kunci, nilai])
  return [nilai, setNilai] as const
}

const Ctx = createContext<CekState | null>(null)

export function CekProvider({ children }: { children: ReactNode }) {
  const [text, setText] = useTersimpan('cekdulu_teks', '')
  const [klaim, setKlaim] = useTersimpan<KlaimResponse | null>('cekdulu_klaim', null)
  const [hasil, setHasil] = useTersimpan<CekResponse | null>('cekdulu_hasil', null)
  // Permintaan yang sedang berjalan tidak disimpan: refresh di tengah pemeriksaan kembali ke Input
  // alih-alih memakai kuota lagi.
  const [cek, setCek] = useState<Promise<CekResponse> | null>(null)

  const mulaiCek = useCallback((k: KlaimResponse) => {
    if (!k.ticker) return
    setKlaim(k)
    setHasil(null)
    setCek(api.cek({ ticker: k.ticker, claims: k.claims }))
  }, [setKlaim, setHasil])

  return (
    <Ctx.Provider value={{ text, setText, klaim, setKlaim, teksAsli: klaim?.source_text ?? text, cek, mulaiCek, hasil, setHasil }}>
      {children}
    </Ctx.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useCek() {
  const c = useContext(Ctx)
  if (!c) throw new Error('useCek di luar CekProvider')
  return c
}
