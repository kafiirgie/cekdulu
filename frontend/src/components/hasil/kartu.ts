// Kartu hasil beserta judul + kutipannya. Dipakai layar Hasil dan Detail pemeriksa,
// supaya nomor "Klaim N" selalu sama di kedua layar.
import type { Card, CekResponse, KlaimResponse } from '@/lib/contract'
import { labelCek } from '@/lib/labels'

export interface ItemKartu {
  card: Card
  judul: string
  kutipan?: string
}

/** Teks klaim per id, dari hasil pemecahan klaim. */
export const teksPerKlaim = (klaim: KlaimResponse | null): Record<string, string> =>
  Object.fromEntries((klaim?.claims ?? []).map((c) => [c.id, c.text]))

export const itemKlaim = (hasil: CekResponse, teks: Record<string, string>): ItemKartu[] =>
  hasil.claims.map((card, i) => ({ card, judul: `Klaim ${i + 1}`, kutipan: card.claim_id ? teks[card.claim_id] : undefined }))

export const itemTakDiceritakan = (hasil: CekResponse): ItemKartu[] =>
  hasil.untold.map((card) => ({ card, judul: labelCek(card.check ?? '') }))
