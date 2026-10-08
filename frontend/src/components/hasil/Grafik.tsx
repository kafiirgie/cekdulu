// Grafik kecil di kartu hasil (card.chart). Titik dan formatnya dari BE (seri.fmt); FE hanya menggambar.
// Label titik: tanggal ISO diformat lewat tanggal(); label lain (mis. "Q2 2025") tampil apa adanya.
import type { Chart, ChartSeries } from '@/lib/contract'
import { fmt, tanggal } from '@/lib/format'

// Lebih dari ini, label per batang terlalu rapat di layar HP; cukup tanggal awal dan akhir.
const LABEL_PER_BATANG = 8

function Ujung({ seri }: { seri: ChartSeries }) {
  const [awal, akhir] = [seri.points[0], seri.points[seri.points.length - 1]]
  if (!awal || seri.points.length < 2) return null
  return (
    <div className="mt-1.5 flex justify-between gap-3 text-[11.5px] text-muted-foreground">
      <span>
        {tanggal(awal[0])} · <b className="font-mono font-semibold text-ink">{fmt(awal[1], seri.fmt)}</b>
      </span>
      <span className="text-right">
        {tanggal(akhir[0])} · <b className="font-mono font-semibold text-ink">{fmt(akhir[1], seri.fmt)}</b>
      </span>
    </div>
  )
}

function Batang({ seri }: { seri: ChartSeries }) {
  const nilai = seri.points.map(([, v]) => v)
  const atas = Math.max(0, ...nilai)
  const rentang = atas - Math.min(0, ...nilai) || 1
  const garisNol = (atas / rentang) * 100
  const kolom = { gridTemplateColumns: `repeat(${seri.points.length}, minmax(0, 1fr))` }
  const berlabel = seri.points.length <= LABEL_PER_BATANG
  return (
    <>
      <div className="relative grid h-28 gap-1" style={kolom}>
        <span aria-hidden="true" className="absolute inset-x-0 border-t border-line-2" style={{ top: `${garisNol}%` }} />
        {seri.points.map(([label, v]) => (
          <div key={label} className="relative" title={`${tanggal(label)}: ${fmt(v, seri.fmt)}`}>
            <i
              className={`absolute inset-x-0 rounded-[3px] ${v < 0 ? 'bg-tidak-sesuai' : 'bg-ink-2'}`}
              style={v < 0 ? { top: `${garisNol}%`, height: `${(-v / rentang) * 100}%` } : { bottom: `${100 - garisNol}%`, height: `${(v / rentang) * 100}%` }}
            />
          </div>
        ))}
      </div>
      {berlabel ? (
        <div className="mt-1.5 grid gap-1 text-center" style={kolom}>
          {seri.points.map(([label, v]) => (
            <span key={label} className="min-w-0 text-[11px] leading-tight text-muted-foreground">
              <b className="block truncate font-mono font-semibold text-ink">{fmt(v, seri.fmt)}</b>
              {tanggal(label)}
            </span>
          ))}
        </div>
      ) : (
        <Ujung seri={seri} />
      )}
    </>
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
  return (
    <>
      <svg viewBox={`0 0 ${LEBAR} ${TINGGI}`} className="h-auto w-full" aria-hidden="true">
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
      {chart.series[0] && <Ujung seri={chart.series[0]} />}
    </>
  )
}

/** Ringkasan untuk pembaca layar: nama seri + nilai awal dan akhir. */
function ringkasan(chart: Chart): string {
  return chart.series
    .map((s) => {
      const [awal, akhir] = [s.points[0], s.points[s.points.length - 1]]
      return awal && akhir ? `${s.name}: ${fmt(awal[1], s.fmt)} sampai ${fmt(akhir[1], s.fmt)}` : s.name
    })
    .join('; ')
}

export default function Grafik({ chart }: { chart: Chart }) {
  const seri = chart.series[0]
  if (!seri?.points.length) return null
  return (
    <figure className="m-0 mt-4" role="img" aria-label={ringkasan(chart)}>
      <figcaption className="mb-2 text-[13px] font-bold">{chart.series.map((s) => s.name).join(' · ')}</figcaption>
      {chart.type === 'bar' ? <Batang seri={seri} /> : <Garis chart={chart} />}
    </figure>
  )
}
