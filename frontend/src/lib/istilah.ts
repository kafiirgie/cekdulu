// Istilah yang diberi ⓘ: satu kalimat, bahasa sehari-hari, untuk investor pemula.
export const ISTILAH = {
  laba: { nama: 'Laba bersih', arti: 'Keuntungan perusahaan setelah semua biaya dan pajak dibayar.' },
  per: { nama: 'PER', arti: 'Harga saham dibagi laba per saham setahun; PER 8 artinya harga saham setara 8 tahun laba.' },
  pbv: { nama: 'PBV', arti: 'Harga saham dibagi nilai buku per saham, yaitu aset perusahaan dikurangi utangnya.' },
  dividen: { nama: 'Dividen', arti: 'Bagian keuntungan perusahaan yang dibagikan ke pemegang saham, mirip bagi hasil.' },
  yield: { nama: 'Imbal dividen', arti: 'Dividen setahun dibanding harga saham; 6% artinya tiap Rp100 harga saham dapat dividen Rp6 setahun.' },
  payout: { nama: 'Payout ratio', arti: 'Bagian laba yang dibagikan sebagai dividen; di atas 100% berarti dividen lebih besar dari laba.' },
  orang_dalam: { nama: 'Orang dalam', arti: 'Direksi, komisaris, atau pemegang saham besar yang wajib melaporkan setiap jual-beli saham perusahaannya.' },
  asing: { nama: 'Investor asing', arti: 'Investor dari luar negeri, biasanya lembaga besar; gerakannya sering jadi patokan walau tidak selalu tepat.' },
  suspensi: { nama: 'Suspensi', arti: 'Penghentian sementara perdagangan saham oleh bursa, misalnya karena harganya naik terlalu cepat.' },
  free_float: { nama: 'Free float', arti: 'Porsi saham yang dipegang publik dan bebas diperjualbelikan, di luar pemilik besar.' },
  hari_serap: {
    nama: 'Hari serap',
    arti: 'Perkiraan berapa hari bursa yang dibutuhkan pasar untuk menyerap saham yang wajib dilepas, kalau seluruh transaksi normal sehari dipakai untuk itu.',
  },
  korelasi: {
    nama: 'Korelasi',
    arti: 'Ukuran seberapa sering dua harga bergerak bersama, dari -1 sampai 1; mendekati 0 berarti hampir tidak ada hubungan.',
  },
  kapitalisasi: { nama: 'Kapitalisasi pasar', arti: 'Harga saham dikali jumlah seluruh sahamnya; ukuran nilai pasar perusahaan.' },
  papan_pemantauan: { nama: 'Papan Pemantauan Khusus', arti: 'Papan perdagangan BEI untuk saham yang perlu diawasi, misalnya karena harganya bergerak tidak wajar.' },
} as const

export type KunciIstilah = keyof typeof ISTILAH

/** Istilah utama tiap pemeriksa, untuk ⓘ di daftar pemeriksa (Metodologi). */
export const ISTILAH_CEK: Partial<Record<string, KunciIstilah>> = {
  laba: 'laba',
  valuasi: 'per',
  dividen: 'dividen',
  orang_dalam: 'orang_dalam',
  asing: 'asing',
  suspensi: 'suspensi',
  free_float: 'free_float',
  m_free_float: 'hari_serap',
  m_komoditas: 'korelasi',
}
