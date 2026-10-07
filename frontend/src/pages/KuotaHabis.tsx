// Layar 12 — Kuota habis. Data kuota datang dari respons 429 (diteruskan lewat state navigasi, lib/galat.ts);
// kalau layar dibuka langsung, batas hariannya dari rules.json.
import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import Stamp from '@/components/Stamp'
import { Button } from '@/components/ui/button'
import type { Quota } from '@/lib/contract'
import { fmt, jamWib } from '@/lib/format'
import { KUOTA_PER_HARI } from '@/lib/labels'
import { useCek } from '@/lib/store'

/** Kalimat kapan kuota kembali; hitung mundur diperbarui tiap 30 detik selama ada `reset_at`. */
function useKapanKembali(resetAt?: string) {
  const [sekarang, setSekarang] = useState(() => Date.now())
  useEffect(() => {
    if (!resetAt) return
    const t = setInterval(() => setSekarang(Date.now()), 30_000)
    return () => clearInterval(t)
  }, [resetAt])
  if (!resetAt) return 'Kuota baru: besok, pukul 00.00 WIB'
  const menit = Math.ceil((new Date(resetAt).getTime() - sekarang) / 60_000)
  if (menit <= 0) return 'Kuota sudah kembali. Silakan cek lagi.'
  const jam = Math.floor(menit / 60)
  return `Kuota baru dalam ${jam ? `${fmt(jam, 'int')} jam ` : ''}${menit % 60} menit (pukul ${jamWib(resetAt)})`
}

export default function KuotaHabis() {
  const quota = (useLocation().state as { quota?: Quota } | null)?.quota
  const { hasil } = useCek()
  const batas = quota?.limit ?? KUOTA_PER_HARI
  const kapan = useKapanKembali(quota?.reset_at)
  return (
    <section className="pb-6 text-center">
      <div className="mt-6 rounded-xl border border-line bg-surface px-5 py-7 shadow-lift">
        <Stamp verdict="info" miring={-5} className="text-[15px]">
          Kuota harian
        </Stamp>
        <div className="mt-5 flex justify-center gap-1.5" aria-hidden="true">
          {Array.from({ length: batas }, (_, i) => (
            <i key={i} className="h-1.5 w-5 rounded bg-ink" />
          ))}
        </div>
        <h1 className="mt-5 mb-2 text-[clamp(24px,4vw,30px)] leading-tight font-bold tracking-[-0.03em]">Kuota cek hari ini sudah habis.</h1>
        <p className="m-0 text-ink-2">Kami membatasi {batas} cek per hari per perangkat supaya data tetap cukup untuk semua orang.</p>
        <p className="mt-3 mb-0 font-mono text-sm font-semibold">{kapan}</p>
        <div className="mt-5 flex flex-wrap justify-center gap-2">
          {hasil && (
            <Button asChild variant="outline" size="sm">
              <Link to="/cek/hasil">Lihat hasil terakhir</Link>
            </Button>
          )}
          <Button asChild variant="outline" size="sm">
            <Link to="/metodologi">Baca metodologi</Link>
          </Button>
        </div>
      </div>
      <p className="mt-3 text-[12.5px] text-muted-foreground">Tidak perlu daftar atau login. Kuota dihitung per perangkat.</p>
    </section>
  )
}
