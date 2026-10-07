// Layar 3 — Konfirmasi klaim: teks asli dengan stabilo per klaim (claim.span), klaim bisa diubah atau dihapus.
import { X } from 'lucide-react'
import type { ReactNode } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import JudulLayar from '@/components/JudulLayar'
import TautanKembali from '@/components/TautanKembali'
import { Button } from '@/components/ui/button'
import type { Claim } from '@/lib/contract'
import { CEK_STANDAR, labelCek } from '@/lib/labels'
import { useCek } from '@/lib/store'

/** Potong teks jadi bagian biasa dan bagian berstabilo. Span yang tumpang tindih dilewati. */
function TeksDistabilo({ teks, claims }: { teks: string; claims: Claim[] }) {
  const rentang = claims
    .flatMap((c) => (c.span ? [c.span] : []))
    .sort((a, b) => a[0] - b[0])
  const bagian: ReactNode[] = []
  let pos = 0
  let ke = 0
  for (const [s, e] of rentang) {
    if (s < pos) continue
    bagian.push(teks.slice(pos, s))
    // Stabilo muncul satu per satu, seperti dicoret berurutan.
    bagian.push(
      <mark key={s} className="stabilo bg-transparent text-ink" style={{ animationDelay: `${300 + ke++ * 380}ms` }}>
        {teks.slice(s, e)}
      </mark>,
    )
    pos = e
  }
  bagian.push(teks.slice(pos))
  return <p className="m-0 text-[19px] leading-[1.65] font-medium">{bagian}</p>
}

function BarisKlaim({ klaim, nomor, onUbah }: { klaim: Claim; nomor: number; onUbah: (k: Claim | null) => void }) {
  return (
    <li className="rounded-md border border-line-2 bg-surface py-1.5 pr-1.5 pl-3.5 shadow-soft focus-within:border-ink-2">
      <div className="flex items-center gap-2.5">
        <span className="font-mono text-[11px] whitespace-nowrap text-muted-foreground">KLAIM {nomor}</span>
        <input
          value={klaim.text}
          onChange={(e) => onUbah({ ...klaim, text: e.target.value })}
          aria-label={`Klaim ${nomor}`}
          className="min-w-0 flex-1 border-0 bg-transparent py-1.5 text-[15px] font-semibold text-ink outline-none"
        />
        <Button variant="ghost" size="icon-sm" onClick={() => onUbah(null)} aria-label={`Hapus klaim ${nomor}`} className="bg-surface-3 text-ink-2 hover:text-ink">
          <X />
        </Button>
      </div>
      <p className="m-0 pb-1.5 text-[12.5px] text-muted-foreground">
        {klaim.checks.length ? `Diperiksa: ${klaim.checks.map(labelCek).join(', ')}` : 'Prediksi/opini — tidak bisa dicek'}
      </p>
    </li>
  )
}

export default function Konfirmasi() {
  const { teksAsli, klaim, setKlaim, mulaiCek } = useCek()
  const nav = useNavigate()
  if (!klaim?.ticker) return <Navigate to="/cek" replace />

  const ubah = (id: string, baru: Claim | null) =>
    setKlaim({
      ...klaim,
      claims: baru ? klaim.claims.map((c) => (c.id === id ? baru : c)) : klaim.claims.filter((c) => c.id !== id),
    })

  const periksa = () => {
    // Klaim yang dikosongkan saat diubah dianggap dihapus.
    const claims = klaim.claims.map((c) => ({ ...c, text: c.text.trim() })).filter((c) => c.text)
    mulaiCek({ ...klaim, claims })
    nav('/cek/hasil')
  }

  const n = klaim.claims.length
  return (
    <section className="pb-6">
      <JudulLayar judul={n ? `Kami menemukan ${n} klaim soal ${klaim.ticker}.` : 'Semua klaim dihapus.'}>
        {n
          ? 'Bagian yang distabilo yang akan diperiksa. Ubah atau hapus kalau ada yang keliru.'
          : `Kami tetap menjalankan ${CEK_STANDAR.length} pemeriksaan standar untuk ${klaim.ticker}.`}
      </JudulLayar>
      {teksAsli.trim() && (
        <div className="rounded-xl border border-line-2 bg-surface p-[18px] shadow-lift">
          {klaim.source_text && <p className="m-0 mb-2 text-[12.5px] font-semibold text-muted-foreground">Teks yang dibaca AI dari screenshot</p>}
          <TeksDistabilo teks={teksAsli} claims={klaim.claims} />
        </div>
      )}
      <ul className="mt-4 grid gap-2">
        {klaim.claims.map((c, i) => (
          <BarisKlaim key={c.id} klaim={c} nomor={i + 1} onUbah={(baru) => ubah(c.id, baru)} />
        ))}
      </ul>
      <div className="mt-5 flex items-center justify-between">
        <TautanKembali />
        <Button onClick={periksa}>
          Cek sekarang <span aria-hidden="true">→</span>
        </Button>
      </div>
    </section>
  )
}
