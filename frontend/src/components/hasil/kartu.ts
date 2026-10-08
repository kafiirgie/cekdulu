// Kartu hasil beserta judul + kutipannya. Dipakai layar Hasil dan Detail pemeriksa,
// supaya nomor "Klaim N" selalu sama di kedua layar.
import type { Card, CekResponse, KlaimResponse } from '@/lib/contract'
import { labelCek } from '@/lib/labels'

export interface ItemKartu {
  card: Card
  judul: string
  kutipan?: string
  /** Alamat kartu untuk /api/tanya: claim_id untuk klaim, u0, u1, … untuk "Yang tidak diceritakan". */
  kunciTanya?: string
  /** "Artinya apa?" dari /api/ringkas (ditulis ulang AI, diperiksa kode); kosong = tidak ada. */
  artinya?: string
  /** true selama /api/ringkas belum menjawab untuk kartu ini. */
  memuatArtinya?: boolean
}

/** Teks klaim per id, dari hasil pemecahan klaim. */
export const teksPerKlaim = (klaim: KlaimResponse | null): Record<string, string> =>
  Object.fromEntries((klaim?.claims ?? []).map((c) => [c.id, c.text]))

/** Teks klaim aslinya kalau ada, kalau tidak judul kartu (mis. kartu cek umum tanpa klaim). */
export const teksAtauJudul = (card: Card, teks: Record<string, string>) => (card.claim_id && teks[card.claim_id]) || card.headline

export const itemKlaim = (hasil: CekResponse, teks: Record<string, string>): ItemKartu[] =>
  hasil.claims.map((card, i) => ({
    card,
    judul: `Klaim ${i + 1}`,
    kutipan: card.claim_id ? teks[card.claim_id] : undefined,
    kunciTanya: card.claim_id ?? undefined,
  }))

export const itemTakDiceritakan = (hasil: CekResponse): ItemKartu[] =>
  hasil.untold.map((card, i) => ({ card, judul: labelCek(card.check ?? ''), kunciTanya: `u${i}` }))
