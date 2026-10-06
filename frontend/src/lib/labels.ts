import rules from '@contract/rules.json'
import type { Catalog, FormStatus, Verdict } from './contract'

const KATALOG = rules as unknown as Catalog

/** Semua pemeriksa + modul dari rules.json, urutannya sama dengan formulir inspeksi. */
export const CEK = KATALOG.checks
export const ATURAN = KATALOG.rules

export const VERDICT_LABEL: Record<Verdict, string> = {
  sesuai: 'Sesuai data',
  menyesatkan: 'Menyesatkan',
  tidak_sesuai: 'Tidak sesuai',
  tidak_bisa_dicek: 'Tidak bisa dicek',
  info: 'Info',
}

export const STATUS_LABEL: Record<FormStatus, string> = {
  temuan: 'Ada temuan',
  aman: 'Aman',
  modul_aktif: 'Modul aktif',
  tidak_relevan: 'Tidak relevan',
  data_kurang: 'Data tidak cukup',
  gagal: 'Gagal',
}

export const CONTOH_KLAIM = [
  'MGLV masih bakal terbang, dari 600 udah 14 ribuan, buruan!',
  'Kata grup, MDKA saham emas, emas lagi naik pasti ikut naik',
  'Semua analis rekomendasi buy ANTM',
  'BUMI diserbu ritel, asing juga masuk',
]
