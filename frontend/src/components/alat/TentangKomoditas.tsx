// "Tentang modul ini": pesan inti modul komoditas + aturan K-1/K-2 dari rules.json.
import DaftarAturan from '@/components/DaftarAturan'
import Istilah from '@/components/Istilah'
import { ATURAN_KOMODITAS } from './komoditas'
import TentangModul from './TentangModul'

export default function TentangKomoditas() {
  return (
    <TentangModul judul="Tentang modul ini">
      <p className="m-0">
        Harga komoditas naik tidak otomatis membuat sahamnya ikut naik. Modul ini menunjukkan dua hal: berapa bagian
        pendapatan perusahaan yang datang dari komoditas itu, dan seberapa sering harga sahamnya bergerak bersama harga
        komoditas dunia (<Istilah k="korelasi" />). Kami tidak membuat ramalan harga.
      </p>
      <DaftarAturan aturan={ATURAN_KOMODITAS} />
    </TentangModul>
  )
}
