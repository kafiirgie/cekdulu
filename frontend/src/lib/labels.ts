import type { FormStatus, Verdict } from './contract'

export const VERDICT_LABEL: Record<Verdict, string> = {
  sesuai: 'Sesuai data',
  menyesatkan: 'Menyesatkan',
  tidak_sesuai: 'Tidak sesuai',
  tidak_bisa_dicek: 'Tidak bisa dicek',
  info: 'Info',
}

export const VERDICT_COLOR: Record<Verdict, string> = {
  sesuai: 'var(--cd-sesuai)',
  menyesatkan: 'var(--cd-menyesatkan)',
  tidak_sesuai: 'var(--cd-tidak-sesuai)',
  tidak_bisa_dicek: 'var(--cd-tidak-bisa)',
  info: 'var(--cd-info)',
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
