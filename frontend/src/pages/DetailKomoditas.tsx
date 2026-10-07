// Layar 10 — detail Modul Komoditas satu emiten: tiap komoditasnya, lalu jembatan ke cek klaim saham itu.
import { useParams } from 'react-router-dom'
import { BATAS_PORSI, bukanSumberUtama, tidakAdaData, useDetailKomoditas } from '@/components/alat/komoditas'
import Jembatan from '@/components/alat/Jembatan'
import Remah from '@/components/alat/Remah'
import TagHubungan from '@/components/alat/TagHubungan'
import TentangKomoditas from '@/components/alat/TentangKomoditas'
import Sumber from '@/components/hasil/Sumber'
import Istilah from '@/components/Istilah'
import JudulLayar from '@/components/JudulLayar'
import Panel from '@/components/Panel'
import { TagDasar } from '@/components/StatusIkon'
import TautanKembali from '@/components/TautanKembali'
import type { KomoditasItem } from '@/lib/contract'
import { fmt, periode, persenBertanda } from '@/lib/format'
import { labelCek, namaKomoditas } from '@/lib/labels'

const JUDUL = labelCek('m_komoditas')

function PorsiPendapatan({ i, nama }: { i: KomoditasItem; nama: string }) {
  if (i.porsi_pendapatan == null) return <p className="m-0 text-sm text-ink-2">Porsi pendapatan dari {nama} tidak tersedia.</p>
  const terbesar = i.komoditas_terbesar
  return (
    <div>
      <div className="flex h-2.5 overflow-hidden rounded-full bg-surface-3" role="img" aria-label={`${fmt(i.porsi_pendapatan, 'pct')} pendapatan dari ${nama}`}>
        <i className="bg-hl" style={{ width: `${i.porsi_pendapatan * 100}%` }} />
      </div>
      <p className="mt-1.5 mb-0 text-sm">
        <b>{fmt(i.porsi_pendapatan, 'pct')}</b> pendapatan dari {nama}
        {i.tahun_buku != null && <span className="text-muted-foreground"> · tahun buku {i.tahun_buku}</span>}
      </p>
      {terbesar && terbesar !== i.komoditas && (
        <p className="m-0 text-sm text-ink-2">
          Sumber terbesar: {namaKomoditas(terbesar).toLowerCase()} {fmt(i.porsi_terbesar, 'pct')}
        </p>
      )}
      {bukanSumberUtama(i) && BATAS_PORSI != null && (
        <p className="mt-1.5 mb-0 text-sm font-semibold text-menyesatkan">
          Di bawah {fmt(BATAS_PORSI, 'pct')}: {nama} bukan sumber utama pendapatan (aturan K-1).
        </p>
      )}
    </div>
  )
}

/** "2023: saham -45% vs +7% BERLAWANAN" → tahun, angka, arah. Bentuk lain ditampilkan apa adanya. */
function ArahTahunan({ baris, nama }: { baris: string[]; nama: string }) {
  return (
    <div>
      <h3 className="m-0 mb-1.5 text-[12.5px] font-semibold text-muted-foreground">Per tahun: saham vs harga {nama}</h3>
      <ul className="m-0 grid list-none gap-1.5 p-0 font-mono text-[13px] tabular-nums">
        {baris.map((b) => {
          const m = /^(.+?):\s*(.+?)\s+(searah|berlawanan)$/i.exec(b)
          if (!m) return <li key={b}>{b}</li>
          const berlawanan = m[3].toLowerCase() === 'berlawanan'
          return (
            <li key={b} className="flex items-center justify-between gap-2">
              <span>
                <b>{m[1]}</b> {m[2].replace(/^saham\s+/i, '')}
              </span>
              <TagDasar kelas={berlawanan ? 'border-menyesatkan text-menyesatkan' : 'border-line-2 text-ink-2'}>
                {berlawanan ? 'Berlawanan' : 'Searah'}
              </TagDasar>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function Perubahan({ i, nama }: { i: KomoditasItem; nama: string }) {
  const angka: [string, string][] = [
    [`Saham ${i.ticker}`, persenBertanda(i.total_return_saham)],
    [`Harga ${nama} dunia`, persenBertanda(i.perubahan_komoditas)],
  ]
  return (
    <table className="w-full border-collapse font-mono text-[13px] tabular-nums">
      <caption className="mb-1.5 text-left font-sans text-[12.5px] font-semibold text-muted-foreground">
        Perubahan {periode(i.periode)}
      </caption>
      <tbody>
        {angka.map(([k, v]) => (
          <tr key={k} className="border-b border-line last:border-0">
            <td className="py-2">{k}</td>
            <td className="py-2 text-right font-semibold">{v}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function PanelKomoditas({ i }: { i: KomoditasItem }) {
  const nama = namaKomoditas(i.komoditas).toLowerCase()
  return (
    <Panel>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="m-0 text-[17px] font-bold">{namaKomoditas(i.komoditas)}</h2>
          <div className="mt-1 text-[12.5px] text-muted-foreground">
            <Istilah k="korelasi" /> · Dihitung
          </div>
          <div className="font-mono text-[28px] leading-tight font-semibold">{fmt(i.korelasi, 'num')}</div>
          <div className="text-sm text-ink-2">
            dari {fmt(i.n_bulan, 'int')} bulan, {periode(i.periode)}
          </div>
        </div>
        <TagHubungan kategori={i.kategori} />
      </div>
      <div className="mt-4 grid gap-4">
        <PorsiPendapatan i={i} nama={nama} />
        <Perubahan i={i} nama={nama} />
        <ArahTahunan baris={i.arah_tahunan} nama={nama} />
      </div>
      <Sumber sources={i.sources} />
    </Panel>
  )
}

export default function DetailKomoditas() {
  const kode = (useParams().ticker ?? '').toUpperCase()
  const { data, pesan } = useDetailKomoditas(kode)
  const jejak = [{ label: 'Alat analisis', ke: '/alat' }, { label: JUDUL, ke: '/alat/komoditas' }, { label: kode }]
  const judul = `${JUDUL}: ${kode}`
  if (!data?.items.length) {
    const isi = pesan ?? (data ? tidakAdaData(kode) : 'Memuat data…')
    return <><Remah jejak={jejak} /><JudulLayar judul={judul}>{isi}</JudulLayar></>
  }

  return (
    <section className="pb-6">
      <Remah jejak={jejak} />
      <JudulLayar judul={judul}>Apakah {kode} benar-benar ikut harga komoditasnya?</JudulLayar>
      <TentangKomoditas />
      {data.items.map((i) => (
        <PanelKomoditas key={i.komoditas} i={i} />
      ))}
      <p className="mt-0 mb-3.5 text-[12.5px] text-muted-foreground">Hubungan masa lalu, bukan ramalan dan bukan saran investasi.</p>
      <Jembatan kode={kode} />
      <div className="mt-4">
        <TautanKembali ke="/alat/komoditas">Kembali ke daftar komoditas</TautanKembali>
      </div>
    </section>
  )
}
