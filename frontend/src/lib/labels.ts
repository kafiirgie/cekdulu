import rules from '@contract/rules.json'
import type { Catalog, FormStatus, Verdict } from './contract'

const KATALOG = rules as unknown as Catalog

/** Semua pemeriksa + modul dari rules.json, urutannya sama dengan formulir inspeksi. */
export const CEK = KATALOG.checks
/** 8 pemeriksa yang selalu jalan untuk setiap saham. */
export const CEK_STANDAR = CEK.filter((c) => c.standar)
const ID_STANDAR = new Set(CEK_STANDAR.map((c) => c.id))
/** Selain 8 pemeriksa standar, sisanya modul khusus (mis. m_komoditas). */
export const isStandar = (check: string) => ID_STANDAR.has(check)
export const ATURAN = KATALOG.rules
/** Satu-satunya aturan tanpa pemeriksa yang menentukan vonis; aturan tanpa pemeriksa lainnya milik kartu "Yang tidak diceritakan". */
export const ATURAN_TIDAK_BISA_DICEK = 'T-1'
export const KUOTA_PER_HARI = KATALOG.quota.cek_per_hari

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

/** Arti tiap vonis (FINAL_PLAN §3.1), untuk Metodologi. */
export const VERDICT_ARTI: Record<Verdict, string> = {
  sesuai: 'Klaim cocok dengan data yang tercatat, sesuai aturan pemeriksanya.',
  menyesatkan: 'Angkanya ada, tapi konteks penting hilang atau periode yang dipakai tidak adil.',
  tidak_sesuai: 'Data menunjukkan hal yang berbeda dari klaim.',
  tidak_bisa_dicek: 'Prediksi, opini, atau rumor tanpa angka. Kami tidak menebak.',
  info: 'Konteks penting yang tidak disebut di klaim; muncul di "Yang tidak diceritakan".',
}

export const STATUS_LABEL: Record<FormStatus, string> = {
  temuan: 'Ada temuan',
  aman: 'Aman',
  modul_aktif: 'Modul aktif',
  tidak_relevan: 'Tidak relevan',
  data_kurang: 'Data tidak cukup',
  gagal: 'Gagal',
}

/** Arti status yang perlu dijelaskan ke pengguna (alasan spesifiknya ada di FormRow.why). */
export const ARTI_STATUS: Partial<Record<FormStatus, string>> = {
  data_kurang: 'Datanya belum lengkap, jadi kami tidak memberi penilaian. Ini bukan berarti aman.',
  gagal: 'Pemeriksaan ini error saat dijalankan; pemeriksaan lain tetap jalan. Coba cek ulang nanti.',
}

/** Kelompok tenggat Radar Free Float (Peraturan I-A BEI); target dan tanggalnya ikut data backend. */
export const KELOMPOK_FF: Record<string, string> = {
  kap_besar_ff_rendah: 'Besar, free float rendah',
  kap_besar_ff_menengah: 'Besar, hampir cukup',
  kap_kecil: 'Kecil dan menengah',
}

export const CONTOH_KLAIM = [
  'MGLV masih bakal terbang, dari 600 udah 14 ribuan, buruan!',
  'Kata grup, MDKA saham emas, emas lagi naik pasti ikut naik',
  'Semua analis rekomendasi buy ANTM',
  'BUMI diserbu ritel, asing juga masuk',
]
