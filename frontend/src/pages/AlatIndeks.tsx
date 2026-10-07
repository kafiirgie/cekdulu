// Layar 10 — indeks Alat analisis: semua modul dengan kerangka yang sama (pertanyaan → daftar → detail → cek klaim).
import { DaftarModul } from '@/components/beranda/AlatAnalisis'
import { CatatanSumber } from '@/components/beranda/Bagian'
import JudulLayar from '@/components/JudulLayar'

export default function AlatIndeks() {
  return (
    <section className="pb-6">
      <JudulLayar judul="Alat analisis">
        Analisis yang dihitung dari data pasar, dengan mesin pemeriksa yang sama. Pilih modul, lalu pilih sahamnya.
      </JudulLayar>
      <DaftarModul />
      <CatatanSumber />
    </section>
  )
}
