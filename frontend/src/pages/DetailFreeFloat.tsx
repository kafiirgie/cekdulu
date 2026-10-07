// Layar 10 — detail Radar Free Float satu emiten, lalu jembatan ke cek klaim saham itu.
import { useNavigate, useParams } from 'react-router-dom'
import Remah from '@/components/alat/Remah'
import TagTekanan from '@/components/alat/TagTekanan'
import { ATURAN_RADAR, SUMBER_RADAR, teksHariSerap, tidakDiRadar, useRadar } from '@/components/alat/radar'
import DaftarAturan from '@/components/DaftarAturan'
import Istilah from '@/components/Istilah'
import JudulLayar from '@/components/JudulLayar'
import Panel from '@/components/Panel'
import TautanKembali from '@/components/TautanKembali'
import { Button } from '@/components/ui/button'
import type { FreeFloatItem } from '@/lib/contract'
import { dataPer, fmt, rupiah, tanggal } from '@/lib/format'
import { KELOMPOK_FF } from '@/lib/labels'
import { useCek } from '@/lib/store'

const hariLagi = (iso: string) => Math.max(0, Math.ceil((new Date(`${iso}T00:00:00`).getTime() - Date.now()) / 86_400_000))

function AngkaUtama({ i }: { i: FreeFloatItem }) {
  // Meter: 0 sampai sedikit di atas target, supaya jarak free float ke target terlihat.
  const skala = i.target * 1.25
  return (
    <Panel>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-[12.5px] text-muted-foreground">
            <Istilah k="hari_serap" /> · Dihitung
          </div>
          <div className="font-mono text-[28px] leading-tight font-semibold whitespace-nowrap">{teksHariSerap(i)}</div>
          <div className="text-sm text-ink-2">
            {i.hari_serap == null ? 'Belum dihitung untuk kelompok tenggat ini.' : 'transaksi normal untuk menyerap saham yang harus dilepas'}
          </div>
        </div>
        <TagTekanan tekanan={i.tekanan} />
      </div>
      <div className="relative mt-4 h-2.5 rounded-full bg-surface-3" role="img" aria-label={`Free float ${fmt(i.free_float, 'pct')}, target ${fmt(i.target, 'pct')}`}>
        <i className="absolute inset-y-0 left-0 rounded-full bg-hl" style={{ width: `${Math.min(i.free_float / skala, 1) * 100}%` }} />
        <b className="absolute -inset-y-1 w-0.5 bg-ink" style={{ left: `${(i.target / skala) * 100}%` }} />
      </div>
      <div className="mt-1.5 flex justify-between text-xs font-semibold">
        <span>Sekarang {fmt(i.free_float, 'pct')}</span>
        <span className="text-menyesatkan">Target {fmt(i.target, 'pct')}</span>
      </div>
    </Panel>
  )
}

function Angka({ i }: { i: FreeFloatItem }) {
  const baris: [string, string][] = [
    ['Free float', fmt(i.free_float, 'pct')],
    ['Target', fmt(i.target, 'pct')],
    ['Tenggat', `${tanggal(i.tenggat)} · ${fmt(hariLagi(i.tenggat), 'int')} hari lagi`],
    ['Harus dilepas', i.nilai_dilepas != null ? rupiah(i.nilai_dilepas) : 'tidak tersedia'],
    ['Kapitalisasi pasar', rupiah(i.market_cap)],
    ['Kelompok', KELOMPOK_FF[i.kelompok] ?? i.kelompok],
  ]
  if (i.papan_pemantauan) baris.push(['Papan Pemantauan Khusus', 'Ya'])
  return (
    <table className="w-full border-collapse font-mono text-[13px] tabular-nums">
      <tbody>
        {baris.map(([k, v]) => (
          <tr key={k} className="border-b border-line last:border-0">
            <td className="py-2">{k}</td>
            <td className="py-2 text-right font-semibold">{v}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function Jembatan({ kode }: { kode: string }) {
  const { setText } = useCek()
  const nav = useNavigate()
  const cekKlaim = () => {
    setText(kode)
    nav('/cek')
  }
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line-2 bg-surface-2 p-[18px]">
      <p className="m-0 text-sm text-ink-2">
        Dengar klaim soal <b className="text-ink">{kode}</b> di grup? Periksa dengan aturan yang sama.
      </p>
      <Button onClick={cekKlaim}>
        Cek klaim saham ini <span aria-hidden="true">→</span>
      </Button>
    </div>
  )
}

export default function DetailFreeFloat() {
  const kode = (useParams().ticker ?? '').toUpperCase()
  const { data, pesan } = useRadar()
  const jejak = [{ label: 'Alat analisis', ke: '/alat' }, { label: 'Radar Free Float', ke: '/alat/free-float' }, { label: kode }]
  const judul = `Radar Free Float: ${kode}`
  const i = data?.items.find((x) => x.ticker === kode)
  if (!i) return <><Remah jejak={jejak} /><JudulLayar judul={judul}>{pesan ?? (data ? tidakDiRadar(kode) : 'Memuat data…')}</JudulLayar></>

  return (
    <section className="pb-6">
      <Remah jejak={jejak} />
      <JudulLayar judul={judul}>{i.company}</JudulLayar>
      <AngkaUtama i={i} />
      <Panel>
        <Angka i={i} />
        <details className="mt-3 text-sm text-ink-2">
          <summary className="mb-2 cursor-pointer font-semibold text-ink">Cara hitungnya</summary>
          <DaftarAturan aturan={ATURAN_RADAR} />
        </details>
        <p className="mt-3 mb-0 font-mono text-[11.5px] text-muted-foreground">
          {SUMBER_RADAR}
          {dataPer(data?.as_of)}
        </p>
      </Panel>
      <Jembatan kode={kode} />
      <div className="mt-4">
        <TautanKembali ke="/alat/free-float">← Kembali ke radar</TautanKembali>
      </div>
    </section>
  )
}
