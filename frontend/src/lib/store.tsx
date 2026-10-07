// State satu sesi cek (teks → klaim → hasil). Sengaja sederhana: React context, tanpa library.
import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
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

const Ctx = createContext<CekState | null>(null)

export function CekProvider({ children }: { children: ReactNode }) {
  const [text, setText] = useState('')
  const [klaim, setKlaim] = useState<KlaimResponse | null>(null)
  const [cek, setCek] = useState<Promise<CekResponse> | null>(null)
  const [hasil, setHasil] = useState<CekResponse | null>(null)

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
