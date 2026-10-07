import type { CSSProperties } from 'react'
import VerdictCard from '@/components/VerdictCard'
import type { ItemKartu } from './kartu'

/**
 * Daftar kartu vonis yang dicap satu per satu. `mulai` = urutan cap kartu pertama, supaya cap di
 * beberapa daftar dalam satu layar tetap berurutan.
 */
export default function DaftarKartu({ item, mulai = 0 }: { item: ItemKartu[]; mulai?: number }) {
  return (
    <ul className="m-0 grid list-none gap-3 p-0">
      {item.map((k, i) => (
        <li key={i} style={{ '--tunda': `${350 + (mulai + i) * 260}ms` } as CSSProperties}>
          <VerdictCard {...k} />
        </li>
      ))}
    </ul>
  )
}
