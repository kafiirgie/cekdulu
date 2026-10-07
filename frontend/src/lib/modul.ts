// Rute layar tiap modul analisis. Modul komoditas belum punya layar (menunggu kontrak D4).
export const RUTE_MODUL: Record<string, string> = {
  m_free_float: '/alat/free-float',
}

/** Pemeriksa standar yang mengaktifkan modul (F-1: free float di bawah batas → Radar Free Float). */
export const MODUL_DARI_CEK: Record<string, string> = {
  free_float: 'm_free_float',
  m_free_float: 'm_free_float',
}
