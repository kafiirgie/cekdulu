import type { Evidence, Fmt } from './contract'

const id = (n: number, max = 0) => n.toLocaleString('id-ID', { maximumFractionDigits: max })

/** BE mengirim angka mentah (desimal / Rupiah penuh). FE yang memformat. */
export function fmt(value: Evidence['value'], f: Fmt): string {
  if (value === null || value === undefined) return 'tidak tersedia'
  if (typeof value === 'string') return value
  switch (f) {
    case 'pct': return `${id(value * 100, 1)}%`
    case 'rp': return rupiah(value)
    case 'int': return id(value)
    case 'x': return `${id(value, 1)}×`
    case 'num': return id(value, 2)
    default: return String(value)
  }
}

const FORMAT_TANGGAL = new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })

/**
 * "2026-09-30" → "30 Sep 2026". Selain tanggal lengkap (mis. tahun buku "2024") dikembalikan apa adanya,
 * supaya tidak tampil seolah ada tanggal pasti yang tidak ada di data.
 */
export function tanggal(teks: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(teks)
  if (!m) return teks
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
  return FORMAT_TANGGAL.format(d)
}

/** Akhiran " · data per 30 Sep 2026" untuk baris keterangan; kosong kalau tanggal data tidak ada. */
export const dataPer = (asOf?: string | null) => (asOf ? ` · data per ${tanggal(asOf)}` : '')

/** 14650 → "Rp14.650"; 9.35e12 → "Rp9,35 T" */
export function rupiah(n: number): string {
  const a = Math.abs(n)
  if (a >= 1e12) return `Rp${id(n / 1e12, 2)} T`
  if (a >= 1e9) return `Rp${id(n / 1e9, 1)} M`
  return `Rp${id(n)}`
}
