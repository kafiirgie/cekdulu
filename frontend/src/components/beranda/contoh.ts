// Contoh di Beranda: klaim gaya grup WA + angka dari skenario demo FINAL_PLAN §6
// (snapshot Sectors 29–30 Sep 2026). Cek ulang bersama angka video (tugas B5).
import type { Verdict } from '@/lib/contract'

export const SUMBER_CONTOH = 'Contoh dari data Sectors per 30 Sep 2026'

export interface ContohSabuk {
  jenis: 'tempel' | 'chat' | 'potongan'
  dari?: string
  teks: string
  vonis: Verdict
  hasil: string
}

export const CONTOH_SABUK: ContohSabuk[] = [
  { jenis: 'tempel', teks: 'MGLV masih bakal terbang!', vonis: 'tidak_bisa_dicek', hasil: 'Tebakan harga, tidak ada datanya' },
  { jenis: 'chat', dari: 'Grup Saham Keluarga', teks: 'MGLV dari 600 udah 14 ribuan', vonis: 'sesuai', hasil: 'Rp600 → Rp14.650, sekitar 24×' },
  { jenis: 'potongan', dari: 'Screenshot grup', teks: 'MDKA itu saham emas', vonis: 'menyesatkan', hasil: '82% pendapatannya dari nikel' },
  { jenis: 'chat', dari: 'Kolom komentar', teks: 'Semua analis buy ANTM', vonis: 'sesuai', hasil: '68 dari 70 rekomendasi buy' },
  { jenis: 'tempel', teks: 'BUMI, asing juga masuk', vonis: 'tidak_sesuai', hasil: 'Porsi asing turun 81% → 69%' },
  { jenis: 'potongan', dari: 'Forum saham', teks: 'PSAB dividennya 25%', vonis: 'sesuai', hasil: 'Yield 25%, tapi payout 114%' },
]
