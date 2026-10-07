// Layar 5 — Hasil: ringkasan, kartu per klaim, "Yang tidak diceritakan", ajakan ke formulir lengkap.
import type { CSSProperties, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import StatusIkon from '@/components/StatusIkon'
import Stamp from '@/components/Stamp'
import { Button } from '@/components/ui/button'
import type { CekResponse, FormRow } from '@/lib/contract'
import { dataPer } from '@/lib/format'
import { isStandar, STATUS_LABEL } from '@/lib/labels'
import DaftarKartu from './DaftarKartu'
import { itemKlaim, itemTakDiceritakan } from './kartu'

// Cap ringkasan dicap satu per satu setelah halaman tampil, sebelum cap kartu (DaftarKartu mulai dari 1).
const tunda = (i: number) => ({ '--tunda': `${350 + i * 260}ms` }) as CSSProperties

function Ringkasan({ hasil, teksAsli }: { hasil: CekResponse; teksAsli: string }) {
  const vonis = [...new Set(hasil.claims.map((c) => c.verdict))]
  const tempel = teksAsli.trim()
  return (
    <div className="mt-2.5 rounded-xl border border-line bg-surface-2 p-[22px] shadow-lift">
      <p className="m-0 mb-1 text-[13.5px] text-muted-foreground">
        {hasil.claims.length && tempel ? (
          <>
            Yang kamu tempel: <q className="text-ink-2">{tempel}</q>
          </>
        ) : (
          `Cek umum untuk ${hasil.ticker}`
        )}
      </p>
      <p className="m-0 mb-2.5 text-[13.5px] text-muted-foreground">
        {hasil.company ?? hasil.ticker}
        {dataPer(hasil.data_as_of)}
      </p>
      <h1 className="m-0 text-[clamp(22px,3.4vw,28px)] leading-[1.22] font-bold tracking-[-0.03em] text-balance">{hasil.summary}</h1>
      {vonis.length > 0 && (
        <div className="dicap mt-4 flex flex-wrap gap-x-3.5 gap-y-2.5">
          {vonis.map((v, i) => (
            <span key={v} style={tunda(i)}>
              <Stamp verdict={v} miring={-4} className="text-xs" />
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function Bagian({ judul, sub, children }: { judul: string; sub: string; children: ReactNode }) {
  return (
    <>
      <div className="mt-[34px] mb-3 flex items-baseline justify-between gap-3">
        <h2 className="m-0 text-[19px] font-bold tracking-[-0.025em]">{judul}</h2>
        <span className="text-[13px] text-muted-foreground">{sub}</span>
      </div>
      {children}
    </>
  )
}


function RingkasanFormulir({ form }: { form: FormRow[] }) {
  const standar = form.filter((f) => isStandar(f.check)).length
  const modul = form.length - standar
  const hitung = Object.entries(STATUS_LABEL).flatMap(([s, label]) => {
    const n = form.filter((f) => f.status === s).length
    return n ? [`${n} ${label.toLowerCase()}`] : []
  })
  return (
    <div className="mt-7 flex flex-wrap items-center justify-between gap-4 rounded-xl border border-line-2 bg-surface p-[18px] shadow-soft">
      <div>
        <h3 className="m-0 text-[17px] font-bold tracking-[-0.02em]">Lihat formulir inspeksi lengkap</h3>
        <p className="mt-1 mb-0 text-sm text-ink-2">
          {standar} pemeriksaan standar{modul > 0 && ` + ${modul} modul`}: {hitung.join(', ')}.
        </p>
        <div className="mt-2.5 flex gap-1" aria-hidden="true">
          {form.map((f) => (
            <StatusIkon key={f.check} status={f.status} className="size-[18px] text-[9.5px]" />
          ))}
        </div>
      </div>
      <Button asChild>
        <Link to="/cek/formulir">
          Buka formulir <span aria-hidden="true">→</span>
        </Link>
      </Button>
    </div>
  )
}

interface Props {
  hasil: CekResponse
  teksAsli: string
  teksKlaim: Record<string, string>
}

export default function HasilCek({ hasil, teksAsli, teksKlaim }: Props) {
  return (
    <section className="pb-6">
      <Ringkasan hasil={hasil} teksAsli={teksAsli} />
      {hasil.claims.length > 0 && (
        <Bagian judul="Klaim yang diperiksa" sub="Ketuk untuk lihat alasannya">
          <DaftarKartu item={itemKlaim(hasil, teksKlaim)} mulai={1} />

        </Bagian>
      )}
      {hasil.untold.length > 0 && (
        // Bagian ini nilai jual utama ketika banyak klaim tidak bisa dicek, jadi diberi bingkai sendiri.
        <div className="mt-[34px] rounded-[22px] border border-hl-edge/40 bg-surface-2 px-3 pb-3 [&>div:first-child]:mt-4">
          <Bagian judul="Yang tidak diceritakan" sub="Penting, tapi tidak disebut">
            <DaftarKartu item={itemTakDiceritakan(hasil)} mulai={1 + hasil.claims.length} />
          </Bagian>
        </div>
      )}
      <RingkasanFormulir form={hasil.form} />
      <div className="mx-auto mt-10 max-w-[30rem] text-center">
        <p className="m-0 text-[clamp(19px,3vw,23px)] font-bold tracking-[-0.025em] text-balance">
          Ini yang perlu kamu tahu. Keputusan tetap di tanganmu.
        </p>
        <p className="mt-2.5 text-[12.5px] text-muted-foreground">
          cek dulu. memeriksa klaim terhadap data yang tercatat. Ini bukan saran investasi. Data dari Sectors.
        </p>
        <Button asChild variant="outline" className="mt-4">
          <Link to="/cek">Cek klaim lain</Link>
        </Button>
      </div>
    </section>
  )
}
