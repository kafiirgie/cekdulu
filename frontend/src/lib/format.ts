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

/** 14650 → "Rp14.650"; 9.35e12 → "Rp9,35 T" */
export function rupiah(n: number): string {
  const a = Math.abs(n)
  if (a >= 1e12) return `Rp${id(n / 1e12, 2)} T`
  if (a >= 1e9) return `Rp${id(n / 1e9, 1)} M`
  return `Rp${id(n)}`
}
