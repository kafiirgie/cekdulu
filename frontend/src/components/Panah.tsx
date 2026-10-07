// Panah aksi (lanjut, buka, kembali, bagikan) sebagai ikon garis, supaya bentuknya tidak ikut font.
// Panah di dalam data ("Rp600 → Rp14.650") tetap teks karena bagian dari kalimat.
import { ArrowLeft, ArrowRight, ArrowUpRight } from 'lucide-react'

const IKON = { kanan: ArrowRight, kiri: ArrowLeft, keluar: ArrowUpRight }

export default function Panah({ arah = 'kanan' }: { arah?: keyof typeof IKON }) {
  const Ikon = IKON[arah]
  return <Ikon aria-hidden="true" className="inline-block size-[1.05em] shrink-0 align-[-0.15em]" />
}
