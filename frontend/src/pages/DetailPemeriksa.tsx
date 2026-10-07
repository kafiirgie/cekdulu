// Layar 7 — Detail pemeriksa ("Lihat aturannya"): aturan yang berlaku + kartu terkait dari hasil cek.
import type { ReactNode } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import BarisMeta from '@/components/BarisMeta'
import DaftarKartu from '@/components/hasil/DaftarKartu'
import { itemKlaim, itemTakDiceritakan, teksPerKlaim } from '@/components/hasil/kartu'
import JudulLayar from '@/components/JudulLayar'
import StatusIkon, { TagStatus } from '@/components/StatusIkon'
import TautanKembali from '@/components/TautanKembali'
import type { FormRow } from '@/lib/contract'
import { dataPer } from '@/lib/format'
import { ARTI_STATUS, ATURAN, isStandar, labelCek, STATUS_LABEL } from '@/lib/labels'
import { useCek } from '@/lib/store'

function Panel({ judul, children }: { judul: string; children: ReactNode }) {
  return (
    <div className="mb-3.5 rounded-xl border border-line bg-surface p-[18px] shadow-soft">
      <h2 className="m-0 mb-2.5 text-sm font-bold text-muted-foreground">{judul}</h2>
      {children}
    </div>
  )
}

/** Pemeriksaan yang gagal atau kekurangan data perlu dijelaskan, bukan disembunyikan. */
function Pemberitahuan({ f }: { f: FormRow }) {
  const arti = ARTI_STATUS[f.status]
  if (!arti) return null
  return (
    <div className="mb-3.5 flex items-start gap-3 rounded-lg border border-line-2 bg-surface p-3.5 text-sm shadow-soft">
      <StatusIkon status={f.status} className="mt-px" />
      <div>
        <b className="block">{STATUS_LABEL[f.status]}</b>
        {arti}
      </div>
    </div>
  )
}

function DaftarAturan({ check }: { check: string }) {
  const aturan = ATURAN.filter((r) => r.check === check)
  if (!aturan.length) return <p className="m-0 text-sm text-ink-2">Belum ada aturan tertulis untuk pemeriksaan ini.</p>
  return (
    <ul className="m-0 grid list-none gap-2 p-0">
      {aturan.map((r) => (
        <li key={r.id} className="rounded-[10px] border border-dashed border-line-2 bg-surface-2 px-3.5 py-3 font-mono text-[13px] leading-relaxed">
          <b>{r.id}</b>
          {r.status === 'usulan' && <span className="ml-2 text-[11px] font-semibold text-menyesatkan">usulan</span>}
          <span className="mt-1 block text-ink">{r.text}</span>
        </li>
      ))}
    </ul>
  )
}

export default function DetailPemeriksa() {
  const { check = '' } = useParams()
  const { klaim, hasil } = useCek()
  if (!hasil) return <Navigate to="/cek" replace />
  const f = hasil.form.find((r) => r.check === check)
  if (!f) return <Navigate to="/cek/formulir" replace />

  const kartu = [...itemKlaim(hasil, teksPerKlaim(klaim)), ...itemTakDiceritakan(hasil)].filter((k) => k.card.check === check)

  return (
    <section className="pb-6">
      <BarisMeta lencana={<TagStatus status={f.status} />}>
        {isStandar(check) ? 'Pemeriksaan standar' : 'Modul khusus'} · {hasil.ticker}
        {dataPer(hasil.data_as_of)}
      </BarisMeta>
      <JudulLayar judul={labelCek(check)}>{f.why}</JudulLayar>
      <Pemberitahuan f={f} />
      {kartu.length > 0 && (
        <Panel judul="Temuan dari cek ini">
          <DaftarKartu item={kartu} />
        </Panel>
      )}
      <Panel judul="Aturan yang dipakai">
        <DaftarAturan check={check} />
      </Panel>
      <TautanKembali ke="/cek/formulir">← Kembali ke formulir</TautanKembali>
    </section>
  )
}
