// Rute layar tiap modul analisis.
export const RUTE_MODUL: Record<string, string> = {
  m_free_float: '/alat/free-float',
  m_komoditas: '/alat/komoditas',
}

/** Pemeriksa standar yang mengaktifkan modul (F-1: free float di bawah batas → Radar Free Float). */
export const MODUL_DARI_CEK: Record<string, string> = {
  free_float: 'm_free_float',
  m_free_float: 'm_free_float',
  m_komoditas: 'm_komoditas',
}
