// Pintu ke Alat analisis. Angka contoh dari FINAL_PLAN §4.1 dan §6 (data 30 Sep 2026).
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { labelCek } from '@/lib/labels'
import JudulBagian, { CatatanSumber } from './Bagian'

function IlustrasiFreeFloat() {
  return (
    <div className="relative">
      <div className="w-44 -rotate-2 rounded-xl border border-line bg-surface p-3 text-left shadow-lift">
        <div className="text-[10.5px] font-semibold text-muted-foreground">Porsi saham publik</div>
        <div className="relative mt-2 h-2.5 rounded-full bg-surface-3">
          <i className="absolute inset-y-0 left-0 w-[45%] rounded-full bg-hl" />
          <b className="absolute -inset-y-1 left-[75%] w-0.5 bg-ink" />
        </div>
        <div className="mt-1.5 flex justify-between text-[10.5px] font-semibold text-muted-foreground">
          <span>sekarang</span>
          <span>target 15%</span>
        </div>
      </div>
      <p className="kertas-tempel tulisan-tangan absolute -right-12 -bottom-16 m-0 w-28 rotate-[5deg] px-2.5 py-2 text-sm">Berapa hari pasar menyerap?</p>
    </div>
  )
}

function IlustrasiKomoditas() {
  return (
    <div className="w-48 rotate-2 rounded-xl border border-line bg-surface p-3 text-left shadow-lift">
      <div className="text-[10.5px] font-semibold text-muted-foreground">Sumber pendapatan MDKA</div>
      <div className="mt-2 flex h-3 overflow-hidden rounded-full bg-surface-3">
        <i className="w-[82%] bg-hl" />
      </div>
      <div className="mt-1.5 flex justify-between text-[10.5px] font-semibold">
        <span>Nikel 82%</span>
        <span className="text-muted-foreground">lainnya</span>
      </div>
    </div>
  )
}

interface Modul {
  nama: string
  tanya: string
  angka: string
  arti: string
  ilustrasi: ReactNode
  /** Kosong = modul belum punya halaman (menunggu kontrak D4). */
  ke?: string
}

const MODUL: Modul[] = [
  {
    nama: labelCek('m_free_float'),
    tanya: 'Apakah saham ini wajib melepas saham ke publik, dan seberapa berat tekanannya?',
    angka: '242',
    arti: 'emiten dengan free float di bawah 15%',
    ilustrasi: <IlustrasiFreeFloat />,
    ke: '/alat/free-float',
  },
  {
    nama: labelCek('m_komoditas'),
    tanya: 'Saham ini benar-benar ikut harga komoditasnya, atau tidak?',
    angka: '82%',
    arti: 'pendapatan MDKA dari nikel, bukan emas',
    ilustrasi: <IlustrasiKomoditas />,
  },
]

function KartuModul({ m }: { m: Modul }) {
  const isi = (
    <>
      <div className="grid h-[170px] place-items-center border-b border-line bg-surface-2 bg-[radial-gradient(var(--cd-dot)_1px,transparent_1.3px)] bg-[size:16px_16px]" aria-hidden="true">
        {m.ilustrasi}
      </div>
      <div className="flex flex-1 flex-col gap-1.5 p-[18px] pb-4">
        <span className="text-xs font-bold text-muted-foreground">{m.nama}</span>
        <h3 className="m-0 text-[17.5px] leading-[1.3] font-bold tracking-[-0.02em] text-balance">{m.tanya}</h3>
        <div className="mt-auto flex items-baseline gap-2 border-t border-line pt-3">
          <span className="font-mono text-lg font-semibold">{m.angka}</span>
          <span className="flex-1 text-[13px] text-ink-2">{m.arti}</span>
          <span className="text-sm font-semibold whitespace-nowrap">{m.ke ? 'Buka →' : 'Segera'}</span>
        </div>
      </div>
    </>
  )
  const gaya = 'flex flex-col overflow-hidden rounded-xl border border-line bg-surface text-left shadow-soft'
  if (!m.ke) return <div className={gaya} aria-disabled="true">{isi}</div>
  return (
    <Link to={m.ke} className={`${gaya} transition hover:-translate-y-0.5 hover:shadow-lift`}>
      {isi}
    </Link>
  )
}

export default function AlatAnalisis() {
  return (
    <section id="alat" className="scroll-mt-4 py-10">
      <JudulBagian
        pil="Alat analisis"
        judul="Untuk yang ingin menggali lebih dalam."
        sub="Analisis yang dihitung dari data pasar, dengan mesin pemeriksa yang sama. Pilih modul, lalu pilih sahamnya."
      />
      <div className="grid gap-3.5 md:grid-cols-2">
        {MODUL.map((m) => (
          <KartuModul key={m.nama} m={m} />
        ))}
      </div>
      <CatatanSumber />
    </section>
  )
}
