// Grafik kecil di kartu hasil (card.chart). Kontrak tidak membawa format angka untuk grafik,
// jadi grafik hanya memperlihatkan bentuk; angkanya ada di tabel bukti kartu yang sama.
import type { Chart } from '@/lib/contract'
import { tanggal } from '@/lib/format'

function Batang({ chart }: { chart: Chart }) {
  const seri = chart.series[0]
  if (!seri) return null
  const maks = Math.max(...seri.points.map(([, v]) => v), 0) || 1
  return (
    <figure className="m-0 mt-3">
      <figcaption className="mb-2 text-xs font-semibold text-muted-foreground">{seri.name}</figcaption>
      <div className="grid gap-1.5">
        {seri.points.map(([label, v]) => (
          <div key={label} className="grid grid-cols-[minmax(0,8rem)_1fr] items-center gap-2 text-[12.5px]">
            <span className="truncate">{label}</span>
            <span className="h-2.5 overflow-hidden rounded-full bg-surface-3">
              <i className="block h-full rounded-full bg-ink-2" style={{ width: `${(Math.max(v, 0) / maks) * 100}%` }} />
            </span>
          </div>
        ))}
      </div>
    </figure>
  )
}

const LEBAR = 320
const TINGGI = 110
const TEPI = 6

function Garis({ chart }: { chart: Chart }) {
  const semua = chart.series.flatMap((s) => s.points.map(([, v]) => v))
  if (!semua.length) return null
  const min = Math.min(...semua)
  const rentang = Math.max(...semua) - min || 1
  const jalur = (titik: [string, number][]) =>
    titik
      .map(([, v], i) => {
        const x = TEPI + (i / (titik.length - 1 || 1)) * (LEBAR - 2 * TEPI)
        const y = TEPI + (1 - (v - min) / rentang) * (TINGGI - 2 * TEPI)
        return `${x},${y}`
      })
      .join(' ')
  const sumbuX = chart.series[0]?.points ?? []
  return (
    <figure className="m-0 mt-3">
      <figcaption className="mb-2 text-xs font-semibold text-muted-foreground">{chart.series.map((s) => s.name).join(' · ')}</figcaption>
      <svg viewBox={`0 0 ${LEBAR} ${TINGGI}`} className="h-auto w-full" role="img" aria-label={chart.series.map((s) => s.name).join(', ')}>
        {chart.series.map((s, i) => (
          <polyline
            key={s.name}
            points={jalur(s.points)}
            fill="none"
            stroke={i ? 'var(--cd-muted)' : 'var(--cd-ink)'}
            strokeWidth="2"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>
      <div className="mt-1 flex justify-between font-mono text-[11px] text-muted-foreground">
        <span>{sumbuX[0] && tanggal(sumbuX[0][0])}</span>
        <span>{sumbuX.length > 1 && tanggal(sumbuX[sumbuX.length - 1][0])}</span>
      </div>
    </figure>
  )
}

export default function Grafik({ chart }: { chart: Chart }) {
  return chart.type === 'bar' ? <Batang chart={chart} /> : <Garis chart={chart} />
}
