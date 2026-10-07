// Layar 4 + 5 — formulir berjalan (animasi dari steps[]) lalu Hasil.
// Permintaan /api/cek dimulai oleh aksi pengguna (store.mulaiCek); layar ini hanya menunggu hasilnya.
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Navigate } from 'react-router-dom'
import FormulirBerjalan from '@/components/hasil/FormulirBerjalan'
import HasilCek from '@/components/hasil/HasilCek'
import { teksPerKlaim } from '@/components/hasil/kartu'
import JudulLayar from '@/components/JudulLayar'
import TautanKembali from '@/components/TautanKembali'
import { Button } from '@/components/ui/button'
import type { CekResponse } from '@/lib/contract'
import { useGalatApi } from '@/lib/galat'
import { useCek } from '@/lib/store'

export default function Hasil() {
  const { teksAsli, klaim, cek, mulaiCek, hasil, setHasil } = useCek()
  const galat = useGalatApi()
  const [diterima, setDiterima] = useState<CekResponse | null>(null)
  const [pesan, setPesan] = useState<string | null>(null)
  const teksKlaim = useMemo(() => teksPerKlaim(klaim), [klaim])
  const selesai = useCallback(() => {
    if (diterima) setHasil(diterima)
  }, [diterima, setHasil])

  useEffect(() => {
    if (!cek || hasil) return
    let batal = false
    cek.then(
      (res) => {
        if (!batal) setDiterima(res)
      },
      (e) => {
        if (batal) return
        const teks = galat(e)
        if (teks) setPesan(teks)
      },
    )
    return () => {
      batal = true
    }
  }, [cek, hasil, galat])

  if (!klaim?.ticker || !(cek || hasil)) return <Navigate to="/cek" replace />
  if (hasil) return <HasilCek hasil={hasil} teksAsli={teksAsli} teksKlaim={teksKlaim} />
  if (pesan) {
    const cobaLagi = () => {
      setPesan(null)
      mulaiCek(klaim)
    }
    return (
      <section className="pb-6">
        <JudulLayar judul="Pemeriksaan belum bisa jalan.">{pesan}</JudulLayar>
        <div className="flex items-center justify-between">
          <TautanKembali />
          <Button onClick={cobaLagi}>Coba lagi</Button>
        </div>
      </section>
    )
  }
  if (diterima) return <FormulirBerjalan hasil={diterima} teksKlaim={teksKlaim} onSelesai={selesai} />
  return <JudulLayar judul={`Memeriksa ${klaim.ticker}…`}>Mengambil data pasar dari Sectors.</JudulLayar>
}
