// Penanganan galat panggilan API yang sama untuk semua layar.
import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { KuotaHabisError } from './contract'

/**
 * Kuota habis → pindah ke layar kuota sambil membawa data kuotanya (dibaca layar KuotaHabis, tugas A7).
 * Galat lain → kalimat ramah untuk ditampilkan. Fungsi stabil, aman dipakai di dependensi useEffect.
 */
export function useGalatApi() {
  const nav = useNavigate()
  return useCallback(
    (e: unknown): string | null => {
      if (e instanceof KuotaHabisError) {
        nav('/kuota-habis', { state: { quota: e.quota } })
        return null
      }
      return 'Tidak bisa terhubung ke server. Coba lagi sebentar lagi.'
    },
    [nav],
  )
}
