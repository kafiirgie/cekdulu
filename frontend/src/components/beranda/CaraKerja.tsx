import { Activity, Coins, Globe, PauseCircle, PieChart, Scale, TrendingUp, UserRound, type LucideIcon } from 'lucide-react'
import { CEK_STANDAR } from '@/lib/labels'
import JudulBagian, { CatatanSumber } from './Bagian'
import { CONTOH_SABUK } from './contoh'
import Sabuk from './Sabuk'

const IKON: Record<string, LucideIcon> = {
  laba: TrendingUp,
  valuasi: Scale,
  dividen: Coins,
  orang_dalam: UserRound,
  asing: Globe,
  lonjakan_harga: Activity,
  suspensi: PauseCircle,
  free_float: PieChart,
}

const LANGKAH = [
  { judul: 'Tempel', isi: 'Teks dari grup, komentar, atau screenshot. Kode saham saja juga bisa.' },
  { judul: 'Kami cek ke data', isi: 'Laporan keuangan, aktivitas investor asing, riwayat dividen, porsi saham publik.' },
  { judul: 'Kamu lihat hasilnya', isi: 'Setiap klaim dapat cap vonis, lengkap dengan angka dan sumbernya.' },
]

export default function CaraKerja() {
  return (
    <section className="py-10">
      <div className="rounded-[28px] border border-line bg-surface-2 px-5 pt-9 pb-7 sm:px-9 sm:pt-12 sm:pb-9">
        <JudulBagian pilKuning pil="Cara kerja" judul={<>Klaim masuk berantakan,<br />keluar sudah diperiksa.</>} />
        <Sabuk contoh={CONTOH_SABUK} className="-mx-5 sm:-mx-9" />
        <CatatanSumber />
        <p className="mt-5 mb-3 text-center text-[14.5px] text-ink-2">
          Setiap cek menjalankan <b className="text-ink">{CEK_STANDAR.length} pemeriksaan yang sama</b>, apa pun sahamnya:
        </p>
        <ul className="flex flex-wrap justify-center gap-2">
          {CEK_STANDAR.map((c) => {
            const Ikon = IKON[c.id] ?? Activity
            return (
              <li key={c.id} className="inline-flex items-center gap-1.5 rounded-full border border-line-2 bg-surface px-3 py-1.5 text-[13px] font-semibold">
                <Ikon className="size-4 text-ink-2" aria-hidden="true" />
                {c.label}
              </li>
            )
          })}
        </ul>
        <p className="mt-3 text-center text-[12.5px] text-muted-foreground">
          Ditambah modul khusus yang aktif otomatis, misalnya saham vs komoditas dan free float.
        </p>
        <ol className="mt-6 grid border-t border-line md:grid-cols-3">
          {LANGKAH.map((l, i) => (
            <li key={l.judul} className="border-line px-5 pt-[18px] pb-1 max-md:[&+&]:border-t md:[&+&]:border-l">
              <div className="font-mono text-xs text-muted-foreground">{i + 1}</div>
              <h3 className="mt-1.5 mb-1 text-base font-bold tracking-[-0.015em]">{l.judul}</h3>
              <p className="m-0 text-sm text-ink-2">{l.isi}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}
