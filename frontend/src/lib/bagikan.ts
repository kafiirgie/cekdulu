// Kartu hasil → PNG untuk dikirim ke grup WhatsApp, plus ringkasan teks.
import { teksAtauJudul } from '@/components/hasil/kartu'
import type { CekResponse } from './contract'
import { dataPer } from './format'
import { VERDICT_LABEL } from './labels'

/** Lebar gambar akhir: kartu 4:5 jadi 1080×1350. */
const LEBAR_PNG = 1080

/** html-to-image dimuat saat dipakai saja, supaya tidak menambah muatan awal halaman. */
export async function gambarKartu(node: HTMLElement): Promise<Blob> {
  const { toBlob } = await import('html-to-image')
  const blob = await toBlob(node, { pixelRatio: LEBAR_PNG / node.offsetWidth })
  if (!blob) throw new Error('gambar kartu kosong')
  return blob
}

/** Bisa membagikan berkas lewat lembar bagikan HP (Web Share API level 2)? */
export function bisaBagikanBerkas(): boolean {
  try {
    return Boolean(navigator.canShare?.({ files: [new File([''], 'cek.png', { type: 'image/png' })] }))
  } catch {
    return false
  }
}

/** Buka lembar bagikan HP (WhatsApp dan lainnya) dengan gambar + ringkasan. */
export async function bagikanBerkas(blob: Blob, nama: string, teks: string): Promise<void> {
  await navigator.share({ files: [new File([blob], nama, { type: 'image/png' })], text: teks })
}

export function unduhBerkas(blob: Blob, nama: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = nama
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

/** Ringkasan teks untuk ditempel di grup (cadangan kalau gambar tidak bisa dikirim). */
export function ringkasanTeks(hasil: CekResponse, teksKlaim: Record<string, string>): string {
  const baris = hasil.claims.map((c) => `• "${teksAtauJudul(c, teksKlaim)}": ${VERDICT_LABEL[c.verdict].toUpperCase()}`)
  return [
    hasil.claims.length ? `Klaim soal ${hasil.ticker}, sudah dicek pakai cek dulu.` : `${hasil.ticker}: ${hasil.summary}`,
    ...baris,
    ...(hasil.untold[0] ? [`Yang tidak diceritakan: ${hasil.untold[0].headline}`] : []),
    `Data dari Sectors${dataPer(hasil.data_as_of)}. Bukan saran investasi.`,
    `Cek sendiri: ${window.location.origin}`,
  ].join('\n')
}
