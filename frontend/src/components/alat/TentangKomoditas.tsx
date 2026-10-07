// "ⓘ Tentang modul ini": pesan inti modul komoditas + aturan K-1/K-2 dari rules.json.
import DaftarAturan from '@/components/DaftarAturan'
import Istilah from '@/components/Istilah'
import { ATURAN_KOMODITAS } from './komoditas'

export default function TentangKomoditas() {
  return (
    <details className="mb-4 rounded-lg border border-line-2 bg-surface px-3.5 py-2.5 text-ink-2 shadow-soft">
      <summary className="cursor-pointer text-sm font-semibold text-ink">ⓘ Tentang modul ini</summary>
      <div className="mt-2.5 grid gap-3 text-sm">
        <p className="m-0">
          Harga komoditas naik tidak otomatis membuat sahamnya ikut naik. Modul ini menunjukkan dua hal: berapa bagian
          pendapatan perusahaan yang datang dari komoditas itu, dan seberapa sering harga sahamnya bergerak bersama harga
          komoditas dunia (<Istilah k="korelasi" />). Kami tidak membuat ramalan harga.
        </p>
        <DaftarAturan aturan={ATURAN_KOMODITAS} />
      </div>
    </details>
  )
}
