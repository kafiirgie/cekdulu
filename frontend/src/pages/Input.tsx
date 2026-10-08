// Layar 2 — Input: tempel teks dari grup, unggah screenshot, atau ketik kode saham saja.
import { ImagePlus, X } from 'lucide-react'
import { useCallback, useEffect, useState, type ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import JudulLayar from '@/components/JudulLayar'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import type { KlaimRequest } from '@/lib/contract'
import { kecilkanGambar } from '@/lib/gambar'
import { useGalatApi } from '@/lib/galat'
import { CONTOH_KLAIM } from '@/lib/labels'
import { useCek } from '@/lib/store'
import Panah from '@/components/Panah'

const KODE_SAJA = /^\s*[A-Za-z]{4}\s*$/

interface Gambar {
  nama: string
  base64: string
}

function gambarDariClipboard(data: DataTransfer | null): File | null {
  if (!data) return null
  for (const item of Array.from(data.items)) {
    if (item.kind === 'file' && item.type.startsWith('image/')) return item.getAsFile()
  }
  return Array.from(data.files).find((file) => file.type.startsWith('image/')) ?? null
}

function namaClipboard(mime: string): string {
  const ekstensi = mime === 'image/png' ? 'png' : mime === 'image/webp' ? 'webp' : 'jpg'
  return `screenshot-clipboard.${ekstensi}`
}

function ChipContoh({ teks, onPilih }: { teks: string; onPilih: () => void }) {
  return (
    <Button variant="outline" onClick={onPilih} className="h-auto justify-start px-3.5 py-2 text-left text-sm font-normal whitespace-normal">
      {teks.split(/(\b[A-Z]{4}\b)/).map((bagian, i) =>
        i % 2 ? <span key={i} className="font-mono font-semibold">{bagian}</span> : bagian,
      )}
    </Button>
  )
}

interface UnggahProps {
  gambar: Gambar | null
  onGambar: (g: Gambar | null) => void
  onFile: (file: File) => void
  disabled: boolean
}

function UnggahScreenshot({ gambar, onGambar, onFile, disabled }: UnggahProps) {
  function pilih(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (f) onFile(f)
  }

  if (gambar) {
    return (
      <span className="inline-flex min-w-0 items-center gap-1.5 rounded-full border border-line-2 bg-surface-2 py-1 pr-1 pl-3.5 text-sm font-semibold">
        <span className="truncate">{gambar.nama}</span>
        <Button variant="ghost" size="icon-xs" onClick={() => onGambar(null)} aria-label="Hapus screenshot" className="size-7 bg-surface-3 text-ink-2 hover:text-ink">
          <X />
        </Button>
      </span>
    )
  }
  return (
    <label className={`inline-flex items-center gap-2 rounded-full border border-line-2 bg-surface-2 px-3.5 py-2 text-sm font-semibold focus-within:outline-[2.5px] focus-within:outline-offset-2 focus-within:outline-ink ${disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}>
      <input type="file" accept="image/*" onChange={pilih} disabled={disabled} className="sr-only" />
      <ImagePlus className="size-4" aria-hidden="true" />
      Unggah screenshot
    </label>
  )
}

/** Benar setelah `aktif` bertahan beberapa detik, supaya jeda AI yang lama tidak terlihat seperti macet. */
function useLama(aktif: boolean, ms = 3000) {
  const [lama, setLama] = useState(false)
  useEffect(() => {
    if (!aktif) return
    const t = setTimeout(() => setLama(true), ms)
    return () => {
      clearTimeout(t)
      setLama(false)
    }
  }, [aktif, ms])
  return lama
}

export default function Input() {
  const { text, setText, setKlaim, setHasil, mulaiCek } = useCek()
  const [gambar, setGambar] = useState<Gambar | null>(null)
  const [memprosesGambar, setMemprosesGambar] = useState(false)
  const [loading, setLoading] = useState(false)
  const [pesan, setPesan] = useState<string | null>(null)
  const menungguLama = useLama(loading)
  const nav = useNavigate()
  const galat = useGalatApi()

  // Satu masukan dalam satu waktu: teks dan screenshot saling menggantikan.
  function isiTeks(t: string) {
    setText(t)
    setGambar(null)
    setPesan(null)
  }
  function isiGambar(g: Gambar | null) {
    setGambar(g)
    if (g) setText('')
    setPesan(null)
  }

  const pasangGambar = useCallback(async (file: File, nama = file.name || namaClipboard(file.type)) => {
    if (!file.type.startsWith('image/')) {
      setPesan('Clipboard tidak berisi gambar. Tempel gambar atau gunakan Unggah screenshot.')
      return
    }
    setMemprosesGambar(true)
    setPesan(null)
    try {
      const base64 = await kecilkanGambar(file)
      setGambar({ nama, base64 })
      setText('')
    } catch {
      setPesan('Gambar ini tidak bisa dibuka. Coba screenshot lain.')
    } finally {
      setMemprosesGambar(false)
    }
  }, [setText])

  useEffect(() => {
    const tempel = (e: ClipboardEvent) => {
      const file = gambarDariClipboard(e.clipboardData)
      if (!file) return // paste teks tetap memakai perilaku browser biasa
      e.preventDefault()
      void pasangGambar(file, file.name || namaClipboard(file.type))
    }
    window.addEventListener('paste', tempel)
    return () => window.removeEventListener('paste', tempel)
  }, [pasangGambar])

  function permintaan(): KlaimRequest {
    if (gambar) return { image_base64: gambar.base64 }
    if (KODE_SAJA.test(text)) return { ticker: text.trim().toUpperCase() }
    return { text }
  }

  async function lanjut() {
    setLoading(true)
    setPesan(null)
    try {
      const k = await api.klaim(permintaan())
      if (!k.ticker) {
        setPesan(
          gambar
            ? 'Screenshot belum bisa kami baca. Tempel teksnya saja, ya.'
            : 'Kami tidak menemukan kode saham di teks ini. Tambahkan kode 4 huruf, mis. BBRI.',
        )
        return
      }
      if (k.claims.length) {
        setKlaim(k)
        setHasil(null)
        nav('/cek/konfirmasi')
      } else {
        mulaiCek(k) // kode saham saja → cek umum, langsung ke Hasil
        nav('/cek/hasil')
      }
    } catch (e) {
      setPesan(galat(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="pb-6">
      <JudulLayar judul="Apa yang mau kamu cek?">Tempel teksnya apa adanya. Kode saham saja juga bisa.</JudulLayar>
      <div className="rounded-xl border border-line-2 bg-surface p-[18px] shadow-lift focus-within:border-ink-2">
        <label htmlFor="klaim" className="mb-2 block text-[13.5px] font-semibold text-muted-foreground">
          Klaim atau alasan
        </label>
        <textarea
          id="klaim"
          value={text}
          onChange={(e) => isiTeks(e.target.value)}
          rows={5}
          spellCheck={false}
          placeholder={gambar ? 'Screenshot terpasang. Ketik di sini untuk memakai teks saja.' : 'Tempel pesan dari grup, atau ketik kode saham (mis. BBRI)'}
          className="kertas-bergaris min-h-[140px] w-full resize-y border-0 bg-transparent px-0.5 text-ink outline-none placeholder:text-muted-foreground"
        />
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2.5 border-t border-line pt-3">
          <UnggahScreenshot
            gambar={gambar}
            onGambar={isiGambar}
            onFile={(file) => void pasangGambar(file)}
            disabled={memprosesGambar}
          />
          <Button disabled={!(text.trim() || gambar) || loading || memprosesGambar} onClick={lanjut}>
            {memprosesGambar ? 'Menyiapkan gambar…' : loading ? 'Membaca klaim…' : <>Pecah jadi klaim <Panah /></>}
          </Button>
        </div>
        <p className="mt-2.5 mb-0 text-[12.5px] text-muted-foreground">
          Di komputer, bisa juga tempel screenshot dengan Ctrl+V. Screenshot dibaca oleh AI (Google Gemini). Potong nama dan nomor HP sebelum mengunggah.
        </p>
      </div>
      {menungguLama && (
        <p role="status" className="mt-3 text-sm text-ink-2">
          AI sedang membaca pesannya. Biasanya 10–20 detik.
        </p>
      )}
      {pesan && (
        <p role="alert" className="mt-3 text-sm font-semibold text-destructive">
          {pesan}
        </p>
      )}
      <p className="mt-[26px] mb-2.5 text-[13px] font-semibold text-muted-foreground">Atau coba contoh</p>
      <div className="flex flex-wrap gap-2">
        {CONTOH_KLAIM.map((c) => (
          <ChipContoh key={c} teks={c} onPilih={() => isiTeks(c)} />
        ))}
      </div>
    </section>
  )
}
