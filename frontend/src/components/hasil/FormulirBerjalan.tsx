// Layar 4 — formulir berjalan: pemeriksa dari steps[] jalan satu per satu, lalu pindah ke Hasil.
import { useEffect, useMemo, useState } from 'react'
import Sabuk from '@/components/beranda/Sabuk'
import type { ContohSabuk } from '@/components/beranda/contoh'
import { teksAtauJudul } from '@/components/hasil/kartu'
import KotakDaftar from '@/components/KotakDaftar'
import StatusIkon from '@/components/StatusIkon'
import type { CekResponse } from '@/lib/contract'
import { fmt } from '@/lib/format'
import { isStandar } from '@/lib/labels'
import { cn } from '@/lib/utils'

/** Total animasi ±5 detik: cukup dramatis untuk video, tidak membuat juri menunggu lama. */
const TOTAL_MS = 5000
const JEDA_SELESAI_MS = 1200
const DIAM = window.matchMedia('(prefers-reduced-motion: reduce)').matches
const JENIS_KERTAS: ContohSabuk['jenis'][] = ['tempel', 'chat', 'potongan']

const detik = (ms: number) => fmt(ms / 1000, 'num')

interface Props {
  hasil: CekResponse
  /** Teks klaim per claim_id, untuk sabuk klaim di atas formulir. */
  teksKlaim: Record<string, string>
  onSelesai: () => void
}

export default function FormulirBerjalan({ hasil, teksKlaim, onSelesai }: Props) {
  const [selesai, setSelesai] = useState(0)
  const { steps } = hasil
  const total = steps.reduce((a, s) => a + s.ms, 0)
  const skala = DIAM ? 0.05 : Math.min(1, TOTAL_MS / (total || 1))
  const status = new Map(hasil.form.map((f) => [f.check, f.status]))
  const sabuk = useMemo<ContohSabuk[]>(
    () =>
      hasil.claims.map((c, i) => ({
        jenis: JENIS_KERTAS[i % JENIS_KERTAS.length],
        dari: 'Grup',
        teks: teksAtauJudul(c, teksKlaim),
        vonis: c.verdict,
        hasil: c.headline,
      })),
    [hasil.claims, teksKlaim],
  )

  const tuntas = selesai >= steps.length
  useEffect(() => {
    const t = tuntas
      ? setTimeout(onSelesai, DIAM ? 300 : JEDA_SELESAI_MS)
      : setTimeout(() => setSelesai((n) => n + 1), steps[selesai].ms * skala)
    return () => clearTimeout(t)
  }, [selesai, tuntas, steps, skala, onSelesai])

  const msBerjalan = steps.slice(0, selesai).reduce((a, s) => a + s.ms, 0)
  const nModul = steps.filter((s) => !isStandar(s.check)).length

  return (
    <section className="pb-6" aria-live="polite">
      <div className="mt-3.5 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-[12.5px] font-semibold text-muted-foreground">Memeriksa klaim soal {hasil.ticker}</div>
          <div className="font-mono text-[clamp(40px,7vw,60px)] leading-none font-semibold tracking-[-0.04em] tabular-nums">
            {detik(msBerjalan)}
            <small className="ml-1.5 text-[0.34em] tracking-normal text-muted-foreground">dtk</small>
          </div>
        </div>
        <div className="text-[12.5px] font-semibold text-muted-foreground">
          {selesai} dari {steps.length} pemeriksaan
        </div>
      </div>
      {sabuk.length > 0 && <Sabuk contoh={sabuk} className="-mx-5 mt-2 sm:-mx-6" />}
      <KotakDaftar
        judul={`Formulir inspeksi · ${hasil.ticker}`}
        keterangan={`${steps.length - nModul} standar${nModul > 0 ? ` + ${nModul} modul` : ''}`}
        className="mt-3 shadow-lift"
      >
        {steps.map((s, i) => {
          const jalan = i === selesai
          const beres = i < selesai
          return (
            <li
              key={s.check}
              className={cn(
                'grid grid-cols-[22px_1fr_auto] items-center gap-3 border-t border-line px-4 py-2.5 text-[14.5px] font-medium text-muted-foreground first:border-t-0',
                beres && 'text-ink',
                jalan && 'bg-surface-2 font-bold text-ink',
                !isStandar(s.check) && 'bg-hl-soft',
              )}
            >
              {/* Langkah tanpa baris formulir tidak boleh tampil seolah aman. */}
              <StatusIkon status={beres ? (status.get(s.check) ?? 'antre') : jalan ? 'jalan' : 'antre'} />
              <span>{s.label}</span>
              <span className="font-mono text-xs text-muted-foreground">{beres && `${detik(s.ms)} dtk`}</span>
            </li>
          )
        })}
      </KotakDaftar>
      <p className="mt-2 min-h-[30px] text-center text-[19px] font-bold tracking-[-0.02em]">
        {tuntas && `Selesai dalam ${detik(msBerjalan)} detik.`}
      </p>
    </section>
  )
}
