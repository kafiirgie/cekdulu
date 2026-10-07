// Data Radar Free Float untuk layar daftar dan detail.
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { FreeFloatItem, FreeFloatList } from '@/lib/contract'
import { fmt } from '@/lib/format'
import { ATURAN } from '@/lib/labels'

const R1 = ATURAN.find((r) => r.id === 'R-1')
/** Batas tampil hari serap ("> 1.000 hari") dari rules.json, bukan angka tetap di kode. */
const BATAS_TAMPIL = R1?.params.batas_tampil_hari ?? Infinity

export const ATURAN_RADAR = ATURAN.filter((r) => r.id === 'F-1' || r.id === 'R-1')

export const SUMBER_RADAR = 'Sumber: Sectors · data kepemilikan dan transaksi harian'

export const tidakDiRadar = (kode: string) =>
  `${kode} tidak ada di radar. Free float-nya mungkin sudah memenuhi, atau datanya belum ada.`

export function teksHariSerap(i: FreeFloatItem): string {
  if (i.hari_serap == null) return 'belum dihitung'
  if (i.hari_serap > BATAS_TAMPIL) return `> ${fmt(BATAS_TAMPIL, 'int')} hari`
  return `${fmt(Math.round(i.hari_serap), 'int')} hari`
}

// Satu muatan untuk layar daftar dan detail (backend membaca ulang CSV di setiap permintaan).
// Dikosongkan kalau gagal supaya kunjungan berikutnya mencoba lagi.
let muatan: Promise<FreeFloatList> | null = null

/** Daftar radar. `pesan` terisi kalau gagal (mis. data radar belum tersedia di server). */
export function useRadar() {
  const [data, setData] = useState<FreeFloatList | null>(null)
  const [pesan, setPesan] = useState<string | null>(null)
  useEffect(() => {
    muatan ??= api.freeFloat().catch((e) => {
      muatan = null
      throw e
    })
    muatan.then(setData, () => setPesan('Data Radar Free Float belum bisa dimuat. Coba lagi sebentar lagi.'))
  }, [])
  return { data, pesan }
}
