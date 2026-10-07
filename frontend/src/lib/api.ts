// Satu pintu FE ke backend. Halaman TIDAK boleh memanggil fetch langsung.
// VITE_API_MODE=mock → contoh dari contract/examples (FE bisa jalan tanpa backend).
import cekMdka from '@contract/examples/cek_res_mdka.json'
import cekMglv from '@contract/examples/cek_res_mglv.json'
import klaimReqMdka from '@contract/examples/klaim_req_mdka.json'
import klaimReqMglv from '@contract/examples/klaim_req_mglv.json'
import klaimMdka from '@contract/examples/klaim_res_mdka.json'
import klaimMglv from '@contract/examples/klaim_res_mglv.json'
import ffList from '@contract/examples/modul_free_float_list.json'
import rules from '@contract/rules.json'
import tanyaContoh from '@contract/examples/tanya.json'
import type {
  Catalog, CekRequest, CekResponse, FreeFloatList, KlaimRequest, KlaimResponse, TanyaRequest, TanyaResponse,
} from './contract'
import { KuotaHabisError } from './contract'
import { deviceId } from './device'

export const API_MODE = (import.meta.env.VITE_API_MODE ?? 'mock') as 'mock' | 'api'
const BASE = import.meta.env.VITE_API_BASE ?? ''

const tunggu = (ms: number) => new Promise((r) => setTimeout(r, ms))
const pilih = <T,>(ticker: string | null | undefined, mglv: unknown, mdka: unknown) =>
  ((ticker ?? '').toUpperCase() === 'MGLV' ? mglv : mdka) as T

// Mock hanya punya pecahan klaim untuk teks contoh MGLV & MDKA. Teks lain dijawab jujur seperti backend
// tanpa klaim: kode saham saja (cek umum), atau tanpa kode kalau teksnya tidak menyebut saham.
const CONTOH_KLAIM_MOCK: [string, unknown][] = [
  [klaimReqMglv.text, klaimMglv],
  [klaimReqMdka.text, klaimMdka],
]

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Device-Id': deviceId() },
    body: JSON.stringify(body),
  })
  if (r.status === 429) {
    const d = await r.json()
    throw new KuotaHabisError(d.detail.quota)
  }
  if (!r.ok) throw new Error(`${path} → HTTP ${r.status}`)
  return r.json()
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(BASE + path)
  if (!r.ok) throw new Error(`${path} → HTTP ${r.status}`)
  return r.json()
}

export const api = {
  async klaim(req: KlaimRequest): Promise<KlaimResponse> {
    if (API_MODE === 'mock') {
      await tunggu(600)
      const contoh = CONTOH_KLAIM_MOCK.find(([teks]) => teks === req.text)?.[1]
      if (contoh) return contoh as KlaimResponse
      return { ticker: req.ticker ?? req.text?.match(/\b[A-Z]{4}\b/)?.[0] ?? null, claims: [] }
    }
    return post('/api/klaim', req)
  },
  async cek(req: CekRequest): Promise<CekResponse> {
    if (API_MODE === 'mock') return pilih(req.ticker, cekMglv, cekMdka)
    return post('/api/cek', req)
  },
  async tanya(req: TanyaRequest): Promise<TanyaResponse> {
    if (API_MODE === 'mock') {
      await tunggu(500)
      const tolak = new RegExp(rules.tanya_tolak_regex, 'i').test(req.question)
      return tolak ? tanyaContoh.res_tolak : tanyaContoh.res_jawab
    }
    return post('/api/tanya', req)
  },
  async freeFloat(): Promise<FreeFloatList> {
    if (API_MODE === 'mock') return ffList as unknown as FreeFloatList
    return get('/api/modul/free-float')
  },
  async rules(): Promise<Catalog> {
    if (API_MODE === 'mock') return rules as unknown as Catalog
    return get('/api/rules')
  },
}
