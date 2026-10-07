// Layar 10 — Radar Free Float: emiten di bawah batas free float, tenggatnya, dan berat tekanannya (aturan R-1).
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Remah from '@/components/alat/Remah'
import TagTekanan from '@/components/alat/TagTekanan'
import TentangRadar from '@/components/alat/TentangRadar'
import { SUMBER_RADAR, teksHariSerap, useRadar } from '@/components/alat/radar'
import InputBulat from '@/components/InputBulat'
import JudulLayar from '@/components/JudulLayar'
import { Button } from '@/components/ui/button'
import type { FreeFloatItem } from '@/lib/contract'
import { dataPer, fmt, tanggal } from '@/lib/format'
import { KELOMPOK_FF } from '@/lib/labels'

const JEJAK = [{ label: 'Alat analisis', ke: '/alat' }, { label: 'Radar Free Float' }]

// Yang belum dihitung hari serapnya ditaruh paling bawah; sisanya dari tekanan terberat.
const urutkan = (a: FreeFloatItem, b: FreeFloatItem) => (b.hari_serap ?? -1) - (a.hari_serap ?? -1)

function Statistik({ items }: { items: FreeFloatItem[] }) {
  const terdekat = items.map((i) => i.tenggat).sort()[0]
  const kotak = [
    { k: 'Belum memenuhi', v: fmt(items.length, 'int'), s: 'emiten di radar' },
    { k: 'Tenggat terdekat', v: terdekat ? tanggal(terdekat) : '–', s: `${items.filter((i) => i.tenggat === terdekat).length} emiten` },
    { k: 'Tekanan berat', v: fmt(items.filter((i) => i.tekanan === 'berat').length, 'int'), s: 'emiten' },
  ]
  return (
    <div className="mb-4 grid grid-cols-3 gap-2">
      {kotak.map((x) => (
        <div key={x.k} className="rounded-lg border border-line bg-surface p-3 shadow-soft">
          <div className="text-[11px] font-semibold text-muted-foreground">{x.k}</div>
          <div className="mt-0.5 text-[15px] leading-tight font-bold">{x.v}</div>
          <div className="text-[11px] text-muted-foreground">{x.s}</div>
        </div>
      ))}
    </div>
  )
}

/** Langsung ke layar detail; detail yang menjelaskan kalau kodenya tidak ada di radar. */
function CariKode() {
  const [kode, setKode] = useState('')
  const nav = useNavigate()
  const cari = (e: FormEvent) => {
    e.preventDefault()
    nav(`/alat/free-float/${kode.trim().toUpperCase()}`)
  }
  return (
    <form onSubmit={cari} className="mb-4 flex gap-2">
      <InputBulat
        value={kode}
        onChange={(e) => setKode(e.target.value)}
        maxLength={4}
        placeholder="Cek saham: ketik kode, mis. BREN"
        aria-label="Kode saham"
        className="uppercase placeholder:normal-case"
      />
      <Button type="submit" disabled={kode.trim().length < 4}>
        Cek
      </Button>
    </form>
  )
}

/** Pilihan kelompok diambil dari data, supaya kelompok baru dari backend tetap muncul. */
function FilterKelompok({ items, pilih, onPilih }: { items: FreeFloatItem[]; pilih: string; onPilih: (k: string) => void }) {
  const kelompok = [...new Set(items.map((i) => i.kelompok))]
  const pilihan: [string, string, number][] = [
    ['semua', 'Semua', items.length],
    ...kelompok.map((k): [string, string, number] => [k, KELOMPOK_FF[k] ?? k, items.filter((i) => i.kelompok === k).length]),
  ]
  return (
    <div role="group" aria-label="Kelompok tenggat" className="mb-3 flex flex-wrap gap-1.5">
      {pilihan.map(([k, label, n]) => (
        <Button key={k} size="sm" variant={pilih === k ? 'default' : 'outline'} aria-pressed={pilih === k} onClick={() => onPilih(k)}>
          {label} ({n})
        </Button>
      ))}
    </div>
  )
}

function BarisRadar({ i, nomor }: { i: FreeFloatItem; nomor: number }) {
  return (
    <li className="border-t border-line first:border-t-0">
      <Link to={`/alat/free-float/${i.ticker}`} className="grid grid-cols-[1.75rem_1fr_auto] items-center gap-2.5 px-3.5 py-3 hover:bg-surface-2">
        <span className="font-mono text-xs text-muted-foreground">{nomor}</span>
        <span className="min-w-0">
          <span className="font-mono font-semibold">{i.ticker}</span>
          {i.papan_pemantauan && <span className="ml-1.5 rounded bg-hl-soft px-1.5 text-[10.5px] font-bold">Papan Pemantauan</span>}
          <span className="block truncate text-xs text-muted-foreground">{i.company}</span>
          <span className="block text-xs text-ink-2">
            {fmt(i.free_float, 'pct')} → {fmt(i.target, 'pct')} · {tanggal(i.tenggat)}
          </span>
        </span>
        <span className="grid justify-items-end gap-1 text-right">
          <b className="font-mono text-sm">{teksHariSerap(i)}</b>
          <TagTekanan tekanan={i.tekanan} />
        </span>
      </Link>
    </li>
  )
}

export default function RadarFreeFloat() {
  const { data, pesan } = useRadar()
  const [kelompok, setKelompok] = useState('semua')
  if (pesan || !data) return <><Remah jejak={JEJAK} /><JudulLayar judul="Radar Free Float">{pesan ?? 'Memuat data…'}</JudulLayar></>

  const daftar = data.items.filter((i) => kelompok === 'semua' || i.kelompok === kelompok).sort(urutkan)
  return (
    <section className="pb-6">
      <Remah jejak={JEJAK} />
      <JudulLayar judul="Radar Free Float">Apakah saham ini wajib melepas saham ke publik, dan seberapa berat tekanannya?</JudulLayar>
      <TentangRadar items={data.items} />
      <CariKode />
      <Statistik items={data.items} />
      <FilterKelompok items={data.items} pilih={kelompok} onPilih={setKelompok} />
      <ul className="m-0 list-none overflow-hidden rounded-xl border border-line bg-surface p-0 shadow-soft">
        {daftar.map((i, n) => (
          <BarisRadar key={i.ticker} i={i} nomor={n + 1} />
        ))}
      </ul>
      <p className="mt-3 text-[12.5px] text-muted-foreground">
        Hari serap <b>Dihitung</b> dari data, bukan ramalan; ketuk emiten untuk cara hitungnya. {SUMBER_RADAR}
        {dataPer(data.as_of)}. Bukan saran investasi.
      </p>
    </section>
  )
}
