// Layar 10 — Modul Komoditas: saham tambang per komoditas, porsi pendapatannya, dan hubungan harganya (aturan K-1, K-2).
import { Link, useSearchParams } from 'react-router-dom'
import { bukanSumberUtama, sumberUnik, useDaftarKomoditas } from '@/components/alat/komoditas'
import Remah from '@/components/alat/Remah'
import TagHubungan from '@/components/alat/TagHubungan'
import TentangKomoditas from '@/components/alat/TentangKomoditas'
import Sumber from '@/components/hasil/Sumber'
import JudulLayar from '@/components/JudulLayar'
import { Button } from '@/components/ui/button'
import type { KomoditasItem } from '@/lib/contract'
import { fmt } from '@/lib/format'
import { KOMODITAS, labelCek, namaKomoditas } from '@/lib/labels'

const JUDUL = labelCek('m_komoditas')
const JEJAK = [{ label: 'Alat analisis', ke: '/alat' }, { label: JUDUL }]
const JENIS_AWAL = Object.keys(KOMODITAS)[0]

function PilihKomoditas({ pilih, onPilih }: { pilih: string; onPilih: (k: string) => void }) {
  return (
    <div role="group" aria-label="Komoditas" className="mb-3 flex flex-wrap gap-1.5">
      {Object.entries(KOMODITAS).map(([k, nama]) => (
        <Button key={k} size="sm" variant={pilih === k ? 'default' : 'outline'} aria-pressed={pilih === k} onClick={() => onPilih(k)}>
          {nama}
        </Button>
      ))}
    </div>
  )
}

function BarisKomoditas({ i }: { i: KomoditasItem }) {
  const nama = namaKomoditas(i.komoditas).toLowerCase()
  return (
    <li className="border-t border-line first:border-t-0">
      <Link to={`/alat/komoditas/${i.ticker}`} className="grid grid-cols-[1fr_auto] items-center gap-2.5 px-3.5 py-3 hover:bg-surface-2">
        <span className="min-w-0">
          <span className="font-mono font-semibold">{i.ticker}</span>
          <span className="block text-xs text-ink-2">
            {i.porsi_pendapatan == null
              ? 'Porsi pendapatan tidak tersedia'
              : `${fmt(i.porsi_pendapatan, 'pct')} pendapatan dari ${nama}`}
            {bukanSumberUtama(i) && <b className="text-menyesatkan"> · bukan sumber utama</b>}
          </span>
        </span>
        <span className="grid justify-items-end gap-1 text-right">
          <b className="font-mono text-sm">{fmt(i.korelasi, 'num')}</b>
          <TagHubungan kategori={i.kategori} />
        </span>
      </Link>
    </li>
  )
}

function Daftar({ jenis }: { jenis: string }) {
  const { data, pesan } = useDaftarKomoditas(jenis)
  if (!data) return <p className="m-0 text-sm text-ink-2">{pesan ?? 'Memuat data…'}</p>
  if (!data.items.length) return <p className="m-0 text-sm text-ink-2">Belum ada saham dengan data {namaKomoditas(jenis).toLowerCase()}.</p>
  const daftar = [...data.items].sort((a, b) => b.korelasi - a.korelasi)
  return (
    <>
      <ul className="m-0 list-none overflow-hidden rounded-xl border border-line bg-surface p-0 shadow-soft">
        {daftar.map((i) => (
          <BarisKomoditas key={i.ticker} i={i} />
        ))}
      </ul>
      <p className="mt-3 mb-0 text-[12.5px] text-muted-foreground">
        Angka di kanan adalah korelasi perubahan bulanan harga saham dengan harga {namaKomoditas(jenis).toLowerCase()} dunia,
        diurutkan dari yang paling searah. <b>Dihitung</b> dari data, bukan ramalan. Bukan saran investasi.
      </p>
      <Sumber sources={sumberUnik(data.items)} />
    </>
  )
}

export default function ModulKomoditas() {
  const [param, setParam] = useSearchParams()
  const jenis = param.get('jenis') ?? JENIS_AWAL
  return (
    <section className="pb-6">
      <Remah jejak={JEJAK} />
      <JudulLayar judul={JUDUL}>Saham ini benar-benar ikut harga komoditasnya, atau tidak?</JudulLayar>
      <TentangKomoditas />
      <PilihKomoditas pilih={jenis} onPilih={(k) => setParam({ jenis: k }, { replace: true })} />
      <Daftar jenis={jenis} />
    </section>
  )
}
