// Layar 3 — Konfirmasi klaim. [A1] stabilo di teks asli (pakai claim.span), edit teks klaim.
import { Navigate, useNavigate } from 'react-router-dom'
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
          <li key={c.id} className="flex items-start justify-between gap-2 rounded-lg bg-white p-3 shadow-sm">
            <div>
              <mark className="bg-yellow-200">{c.text}</mark>
              <p className="mt-1 text-xs text-neutral-500">
                {c.checks.length ? `Diperiksa: ${c.checks.join(', ')}` : 'Prediksi/opini — tidak bisa dicek'}
              </p>
            </div>
            <button onClick={() => hapus(c.id)} className="text-xs text-neutral-500">hapus</button>
          </li>
        ))}
      </ul>
      <button
        onClick={() => nav('/cek/hasil')}
        className="mt-4 w-full rounded-lg bg-black py-3 font-semibold text-white"
      >
        Periksa {klaim.claims.length} klaim
      </button>
    </section>
  )
}
