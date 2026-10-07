// Tombol "Bagikan ke grup" yang menempel di bawah layar Hasil, membuka kartu 4:5 untuk disimpan/dibagikan.
import { useRef, useState, type RefObject } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { bagikanBerkas, bisaBagikanBerkas, gambarKartu, ringkasanTeks, unduhBerkas } from '@/lib/bagikan'
import type { CekResponse } from '@/lib/contract'
import KartuBagikan from './KartuBagikan'
import Panah from '@/components/Panah'

// Dukungan berbagi berkas tidak berubah selama sesi.
const BISA_BAGIKAN = bisaBagikanBerkas()

interface Props {
  hasil: CekResponse
  teksKlaim: Record<string, string>
}

function AksiBagikan({ hasil, teksKlaim, kartu }: Props & { kartu: RefObject<HTMLDivElement | null> }) {
  const [sibuk, setSibuk] = useState(false)
  const [pesan, setPesan] = useState<string | null>(null)

  // "Simpan" selalu mengunduh; "Bagikan" hanya muncul kalau perangkat bisa membagikan berkas (umumnya HP).
  async function buatGambar(bagikan: boolean) {
    if (!kartu.current) return
    setSibuk(true)
    setPesan(null)
    try {
      const blob = await gambarKartu(kartu.current)
      const nama = `cekdulu-${hasil.ticker}.png`
      if (bagikan) {
        await bagikanBerkas(blob, nama, ringkasanTeks(hasil, teksKlaim))
      } else {
        unduhBerkas(blob, nama)
        setPesan('Gambar tersimpan. Kirim dari galeri ke grup.')
      }
    } catch (e) {
      // Pengguna menutup lembar bagikan: bukan galat.
      if (!(e instanceof DOMException && e.name === 'AbortError')) setPesan('Gambar belum bisa dibuat. Coba "Salin ringkasan".')
    } finally {
      setSibuk(false)
    }
  }

  async function salinRingkasan() {
    try {
      await navigator.clipboard.writeText(ringkasanTeks(hasil, teksKlaim))
      setPesan('Ringkasan tersalin. Tempel di grup.')
    } catch {
      setPesan('Tidak bisa menyalin di perangkat ini.')
    }
  }

  return (
    <>
      <div className="flex flex-wrap justify-center gap-2">
        {BISA_BAGIKAN && (
          <Button onClick={() => buatGambar(true)} disabled={sibuk}>
            Bagikan gambar
          </Button>
        )}
        <Button variant={BISA_BAGIKAN ? 'outline' : 'default'} onClick={() => buatGambar(false)} disabled={sibuk}>
          {sibuk ? 'Membuat gambar…' : 'Simpan gambar'}
        </Button>
        <Button variant="outline" onClick={salinRingkasan}>
          Salin ringkasan
        </Button>
      </div>
      <p role="status" className="m-0 min-h-5 text-center text-[13px] text-ink-2">
        {pesan}
      </p>
    </>
  )
}

export default function BagikanKeGrup({ hasil, teksKlaim }: Props) {
  const kartu = useRef<HTMLDivElement>(null)
  return (
    <Dialog>
      <div className="sticky bottom-0 z-20 -mx-4 mt-6 flex justify-center bg-gradient-to-t from-page from-45% to-transparent px-4 pt-3.5 pb-[calc(14px+env(safe-area-inset-bottom))]">
        <DialogTrigger asChild>
          <Button className="shadow-lift">
            Bagikan ke grup <Panah arah="keluar" />
          </Button>
        </DialogTrigger>
      </div>
      <DialogContent className="max-h-[92dvh] max-w-[400px] gap-3 overflow-y-auto p-4">
        <DialogTitle>Kartu untuk grup</DialogTitle>
        <DialogDescription>Simpan sebagai gambar lalu kirim balik ke grup tempat klaim ini beredar.</DialogDescription>
        <div className="flex justify-center">
          <KartuBagikan ref={kartu} hasil={hasil} teksKlaim={teksKlaim} />
        </div>
        <AksiBagikan hasil={hasil} teksKlaim={teksKlaim} kartu={kartu} />
      </DialogContent>
    </Dialog>
  )
}
