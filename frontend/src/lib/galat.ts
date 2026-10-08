// Penanganan galat panggilan API yang sama untuk semua layar.
import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { GalatHttp } from './api'
import { KuotaHabisError } from './contract'

/**
 * Kuota habis → pindah ke layar kuota sambil membawa data kuotanya (dibaca layar KuotaHabis, tugas A7).
 * Galat 4xx dengan kalimat dari server (mis. saham di luar data demo) → kalimat itu.
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
      if (e instanceof GalatHttp && e.status < 500 && e.pesan) return e.pesan
      return 'Tidak bisa terhubung ke server. Coba lagi sebentar lagi.'
    },
    [nav],
  )
}
