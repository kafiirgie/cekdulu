// Layar 3 — Konfirmasi klaim. [A1] stabilo di teks asli (pakai claim.span), edit teks klaim.
import { Navigate, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useCek } from '@/lib/store'

export default function Konfirmasi() {
  const { klaim, setKlaim } = useCek()
  const nav = useNavigate()
  if (!klaim) return <Navigate to="/cek" replace />

  const hapus = (id: string) => setKlaim({ ...klaim, claims: klaim.claims.filter((c) => c.id !== id) })

  return (
    <section>
      <h2 className="text-lg font-semibold">
        Kami menemukan {klaim.claims.length} klaim soal {klaim.ticker ?? 'saham'}
      </h2>
      <ul className="mt-3 space-y-2">
        {klaim.claims.map((c) => (
          <li key={c.id} className="flex items-start justify-between gap-2 rounded-lg bg-surface p-3 shadow-soft">
            <div>
              <mark className="bg-hl-mark text-ink">{c.text}</mark>
              <p className="mt-1 text-xs text-muted-foreground">
                {c.checks.length ? `Diperiksa: ${c.checks.join(', ')}` : 'Prediksi/opini — tidak bisa dicek'}
              </p>
            </div>
            <button onClick={() => hapus(c.id)} className="text-xs text-muted-foreground">hapus</button>
          </li>
        ))}
      </ul>
      <Button size="lg"
        onClick={() => nav('/cek/hasil')}
        className="mt-4 w-full">
        Periksa {klaim.claims.length} klaim
      </Button>
    </section>
  )
}
