// Data dan aturan modul komoditas untuk layar daftar dan detail.
import { useEffect, useState } from 'react'
import { api, GalatHttp } from '@/lib/api'
import type { KomoditasItem, Source } from '@/lib/contract'
import { ATURAN } from '@/lib/labels'

export const ATURAN_KOMODITAS = ATURAN.filter((r) => r.check === 'm_komoditas')

/** Batas porsi pendapatan aturan K-1 (mis. 0,5). */
export const BATAS_PORSI = ATURAN.find((r) => r.id === 'K-1')?.params.batas_porsi_pendapatan

/** K-1: komoditas ini bukan sumber utama pendapatan perusahaan. */
export const bukanSumberUtama = (i: KomoditasItem) =>
  i.porsi_pendapatan != null && BATAS_PORSI != null && i.porsi_pendapatan < BATAS_PORSI

/** Sumber unik dari beberapa baris, untuk satu catatan sumber di bawah daftar. */
export const sumberUnik = (items: KomoditasItem[]): Source[] => [
  ...new Map(items.flatMap((i) => i.sources).map((s) => [s.name, s])).values(),
]

export const tidakAdaData = (kode: string) =>
  `${kode} belum ada di modul komoditas. Sahamnya mungkin bukan saham tambang, atau datanya belum tersedia.`

const pesanDaftar = () => 'Data modul komoditas belum bisa dimuat. Coba lagi sebentar lagi.'
const pesanDetail = (e: unknown, kode: string) =>
  e instanceof GalatHttp && e.status === 404 ? tidakAdaData(kode) : pesanDaftar()

/** Muat ulang setiap `kunci` berubah; jawaban lama yang datang terlambat diabaikan. */
function useMuat<T>(kunci: string, muat: (k: string) => Promise<T>, pesanGagal: (e: unknown, k: string) => string) {
  const [hasil, setHasil] = useState<{ kunci: string; data: T | null; pesan: string | null } | null>(null)
  useEffect(() => {
    let aktif = true
    muat(kunci).then(
      (data) => aktif && setHasil({ kunci, data, pesan: null }),
      (e) => aktif && setHasil({ kunci, data: null, pesan: pesanGagal(e, kunci) }),
    )
    return () => {
      aktif = false
    }
  }, [kunci, muat, pesanGagal])
  const kini = hasil?.kunci === kunci ? hasil : null
  return { data: kini?.data ?? null, pesan: kini?.pesan ?? null }
}

export const useDaftarKomoditas = (jenis: string) => useMuat(jenis, api.komoditas, pesanDaftar)
export const useDetailKomoditas = (kode: string) => useMuat(kode, api.komoditasDetail, pesanDetail)
