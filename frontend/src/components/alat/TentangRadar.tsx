// "Tentang modul ini": aturan F-1/R-1 dari rules.json + target dan tenggat tiap kelompok dari data.
import DaftarAturan from '@/components/DaftarAturan'
import Istilah from '@/components/Istilah'
import type { FreeFloatItem } from '@/lib/contract'
import { fmt, tanggal } from '@/lib/format'
import { KELOMPOK_FF } from '@/lib/labels'
import { ATURAN_RADAR } from './radar'
import TentangModul from './TentangModul'

function TenggatKelompok({ items }: { items: FreeFloatItem[] }) {
  const contoh = [...new Map(items.map((i) => [i.kelompok, i])).values()]
  return (
    <ul className="m-0 grid list-none gap-1.5 p-0">
      {contoh.map((i) => (
        <li key={i.kelompok} className="text-sm">
          <b>{KELOMPOK_FF[i.kelompok] ?? i.kelompok}</b>: target {fmt(i.target, 'pct')} paling lambat {tanggal(i.tenggat)}
        </li>
      ))}
    </ul>
  )
}

export default function TentangRadar({ items }: { items: FreeFloatItem[] }) {
  return (
    <TentangModul judul="Tentang modul ini (Peraturan I-A BEI)">
      <p className="m-0">
        BEI mewajibkan porsi saham di tangan publik (<Istilah k="free_float" />) mencapai batas minimal sebelum tenggat. Saham tambahan
        yang dilepas ke pasar bisa menekan harga kalau pasar tidak cukup kuat menyerapnya.
      </p>
      <TenggatKelompok items={items} />
      <DaftarAturan aturan={ATURAN_RADAR} />
    </TentangModul>
  )
}
