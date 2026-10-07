// Layar 7 — Detail pemeriksa ("Lihat aturannya"): aturan yang berlaku + kartu terkait dari hasil cek.
import { Navigate, useParams } from 'react-router-dom'
import BarisMeta from '@/components/BarisMeta'
import DaftarAturan from '@/components/DaftarAturan'
import DaftarKartu from '@/components/hasil/DaftarKartu'
import { itemKlaim, itemTakDiceritakan, teksPerKlaim } from '@/components/hasil/kartu'
import TautanModul from '@/components/hasil/TautanModul'
import JudulLayar from '@/components/JudulLayar'
import Panel from '@/components/Panel'
import StatusIkon, { TagStatus } from '@/components/StatusIkon'
import TautanKembali from '@/components/TautanKembali'
import type { FormRow } from '@/lib/contract'
import { dataPer } from '@/lib/format'
import { ARTI_STATUS, ATURAN, isStandar, labelCek, STATUS_LABEL } from '@/lib/labels'
import { useCek } from '@/lib/store'


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
      <div className="-mt-3 mb-3.5">
        <TautanModul check={check} />
      </div>
      <Pemberitahuan f={f} />
      {kartu.length > 0 && (
        <Panel judul="Temuan dari cek ini">
          <DaftarKartu item={kartu} />
        </Panel>
      )}
      <Panel judul="Aturan yang dipakai">
        <DaftarAturan aturan={ATURAN.filter((r) => r.check === check)} />
      </Panel>
      <TautanKembali ke="/cek/formulir">Kembali ke formulir</TautanKembali>
    </section>
  )
}
