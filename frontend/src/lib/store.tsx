// State satu sesi cek (teks → klaim → hasil). Sengaja sederhana: React context, tanpa library.
import { createContext, useContext, useState, type ReactNode } from 'react'
import type { CekResponse, KlaimResponse } from './contract'

interface CekState {
  text: string
  setText: (t: string) => void
  klaim: KlaimResponse | null
  setKlaim: (k: KlaimResponse | null) => void
  hasil: CekResponse | null
  setHasil: (h: CekResponse | null) => void
}

const Ctx = createContext<CekState | null>(null)

export function CekProvider({ children }: { children: ReactNode }) {
  const [text, setText] = useState('')
  const [klaim, setKlaim] = useState<KlaimResponse | null>(null)
  const [hasil, setHasil] = useState<CekResponse | null>(null)
  return <Ctx.Provider value={{ text, setText, klaim, setKlaim, hasil, setHasil }}>{children}</Ctx.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useCek() {
  const c = useContext(Ctx)
  if (!c) throw new Error('useCek di luar CekProvider')
  return c
}
