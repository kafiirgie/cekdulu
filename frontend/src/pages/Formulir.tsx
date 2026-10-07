// Layar 6 — Formulir inspeksi: semua pemeriksaan untuk satu saham, urutan dari backend.
import { Link, Navigate } from 'react-router-dom'
import BarisMeta from '@/components/BarisMeta'
import JudulLayar from '@/components/JudulLayar'
import KotakDaftar from '@/components/KotakDaftar'
import { Pil } from '@/components/beranda/Bagian'
import StatusIkon, { TagStatus } from '@/components/StatusIkon'
import TautanKembali from '@/components/TautanKembali'
import type { FormRow, FormStatus } from '@/lib/contract'
import { dataPer } from '@/lib/format'
import { isStandar, labelCek, STATUS_LABEL } from '@/lib/labels'
import { useCek } from '@/lib/store'
import { cn } from '@/lib/utils'

function Legenda() {
  return (
    <ul className="m-0 mb-[18px] flex list-none flex-wrap gap-x-3.5 gap-y-2 p-0 text-[12.5px] text-ink-2">
      {(Object.keys(STATUS_LABEL) as FormStatus[]).map((s) => (
        <li key={s} className="inline-flex items-center gap-1.5">
          <StatusIkon status={s} className="size-[17px] text-[9px]" />
          {STATUS_LABEL[s]}
        </li>
      ))}
    </ul>
  )
}

function Baris({ f }: { f: FormRow }) {
  return (
    <li className="border-t border-line first:border-t-0">
      <Link to={`/cek/formulir/${f.check}`} className="grid grid-cols-[22px_1fr_auto] items-center gap-3 px-4 py-[13px] hover:bg-surface-2">
        <StatusIkon status={f.status} />
        <span>
          <span className={cn('text-[15px] font-bold tracking-[-0.01em]', f.status === 'tidak_relevan' && 'text-muted-foreground')}>
            {labelCek(f.check)}
          </span>
          <span className="mt-px block text-[13.5px] font-medium text-ink-2">{f.why}</span>
        </span>
        <span className="flex items-center gap-2">
          <TagStatus status={f.status} />
          <span aria-hidden="true" className="text-lg text-muted-foreground">›</span>
        </span>
      </Link>
    </li>
  )
}

export default function Formulir() {
  const { hasil } = useCek()
  if (!hasil) return <Navigate to="/cek" replace />
  const standar = hasil.form.filter((f) => isStandar(f.check))
  const modul = hasil.form.filter((f) => !isStandar(f.check))
  return (
    <section className="pb-6">
      <BarisMeta lencana={<Pil>Mode lengkap</Pil>}>
        {hasil.ticker}
        {dataPer(hasil.data_as_of)}
      </BarisMeta>
      <JudulLayar judul="Formulir inspeksi">
        Semua pemeriksaan yang dijalankan untuk {hasil.ticker}, termasuk yang aman dan yang tidak relevan. Ketuk satu
        baris untuk melihat aturan, angka, dan sumbernya.
      </JudulLayar>
      <Legenda />
      <KotakDaftar judul="Pemeriksaan standar" keterangan="selalu dijalankan · urutan tetap" className="mb-3.5">
        {standar.map((f) => (
          <Baris key={f.check} f={f} />
        ))}
      </KotakDaftar>
      {modul.length > 0 && (
        <KotakDaftar judul="Modul khusus" keterangan="aktif otomatis sesuai kondisi saham" className="mb-3.5">
          {modul.map((f) => (
            <Baris key={f.check} f={f} />
          ))}
        </KotakDaftar>
      )}
      <p className="text-[12.5px] text-muted-foreground">
        Urutan dan isi pemeriksaan standar selalu sama untuk setiap saham. Modul khusus hanya aktif kalau syaratnya
        terpenuhi.{' '}
        <Link to="/metodologi" className="underline underline-offset-2 hover:text-ink">
          Lihat semua aturan
        </Link>
      </p>
      <TautanKembali ke="/cek/hasil">Hasil</TautanKembali>
    </section>
  )
}
