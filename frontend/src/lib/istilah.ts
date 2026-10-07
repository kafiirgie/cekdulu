// Glosarium untuk ikon info: satu kalimat, bahasa sehari-hari, untuk investor pemula.
// Sumber teks = contract/glosarium.json (bagian kontrak), diimpor langsung supaya tidak ada salinan yang bisa basi.
import glosarium from '@contract/glosarium.json'
import type { KunciGlosarium } from './contract'

export type KunciIstilah = KunciGlosarium

export const ISTILAH = glosarium.istilah as {
  key: KunciIstilah
  nama: string
  arti: string
}[]

const PER_KUNCI: Record<string, { nama: string; arti: string }> = Object.fromEntries(
  glosarium.istilah.map((i) => [i.key, { nama: i.nama, arti: i.arti }]),
)

/** Teks satu istilah; dipakai komponen Istilah dan tes sinkron kontrak. */
export const istilah = (k: KunciIstilah) => PER_KUNCI[k]

/** Istilah utama tiap pemeriksa / kartu "Yang tidak diceritakan", untuk ikon info di Metodologi. */
export const ISTILAH_CEK: Partial<Record<string, KunciIstilah>> = {
  ...glosarium.pemetaan.checks,
  ...glosarium.pemetaan.untold,
} as Partial<Record<string, KunciIstilah>>
