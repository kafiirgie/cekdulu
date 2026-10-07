import rules from '@contract/rules.json'
import type { Catalog, FormStatus, Verdict } from './contract'

const KATALOG = rules as unknown as Catalog

/** Semua pemeriksa + modul dari rules.json, urutannya sama dengan formulir inspeksi. */
export const CEK = KATALOG.checks
/** 8 pemeriksa yang selalu jalan untuk setiap saham. */
export const CEK_STANDAR = CEK.filter((c) => c.standar)
export const ATURAN = KATALOG.rules

// Pemecah klaim bisa memilih pemeriksa maupun kartu "Yang tidak diceritakan" (mis. analis, pemegang).
const LABEL_CEK = new Map([...KATALOG.checks, ...KATALOG.untold].map((c) => [c.id, c.label]))
export const labelCek = (id: string) => LABEL_CEK.get(id) ?? id

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
