// Layar 4 + 5 — Formulir berjalan (loading) lalu Hasil.
// [A2] port tampilan kartu, grafik, "Bagikan ke grup" (kartu 4:5), panel Tanya.
import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import VerdictCard from '@/components/VerdictCard'
import { api } from '@/lib/api'
import { useGalatApi } from '@/lib/galat'
import { useCek } from '@/lib/store'

export default function Hasil() {
  const { klaim, hasil, setHasil } = useCek()
  const [langkah, setLangkah] = useState(0)
  const [err, setErr] = useState<string | null>(null)
  const galat = useGalatApi()

  useEffect(() => {
    if (!klaim?.ticker || hasil) return
    let batal = false
    api
      .cek({ ticker: klaim.ticker, claims: klaim.claims })
      .then(async (res) => {
        // Animasi formulir berjalan dari steps[].ms (dipercepat, maks ±4 detik total)
        for (let i = 0; i < res.steps.length && !batal; i++) {
          setLangkah(i + 1)
          await new Promise((r) => setTimeout(r, Math.min(res.steps[i].ms, 500)))
        }
        if (!batal) setHasil(res)
      })
      .catch((e) => {
        const pesan = galat(e)
        if (pesan) setErr(pesan)
      })
    return () => {
      batal = true
    }
  }, [klaim, hasil, setHasil, galat])

  if (!klaim?.ticker) return <Navigate to="/cek" replace />
  if (err) return <p className="text-destructive">{err}</p>
  if (!hasil) {
    return (
      <section>
        <h2 className="text-lg font-semibold">Memeriksa {klaim.ticker}…</h2>
        <p className="mt-2 text-sm text-muted-foreground">Pemeriksaan ke-{langkah}</p>
      </section>
    )
  }

  const teks = Object.fromEntries(klaim.claims.map((c) => [c.id, c.text]))
  return (
    <section className="space-y-4">
      <header>
        <p className="text-sm text-muted-foreground">{hasil.company ?? hasil.ticker} · data per {hasil.data_as_of}</p>
        <h2 className="text-xl font-bold">{hasil.summary}</h2>
      </header>
      {hasil.claims.map((c) => (
        <VerdictCard key={c.claim_id} card={c} claimText={c.claim_id ? teks[c.claim_id] : undefined} />
      ))}
      {hasil.untold.length > 0 && (
        <>
          <h3 className="pt-4 text-lg font-semibold">Yang tidak diceritakan</h3>
          {hasil.untold.map((c, i) => <VerdictCard key={i} card={c} />)}
        </>
      )}
      <Link to="/cek/formulir" className="block rounded-lg border py-3 text-center font-semibold">
        Lihat formulir lengkap ({hasil.form.length} pemeriksaan)
      </Link>
    </section>
  )
}
