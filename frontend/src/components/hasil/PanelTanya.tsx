// Panel Tanya: pertanyaan lanjutan tentang satu kartu. Jawaban hanya dari data kartu itu (backend);
// pertanyaan saran beli/jual ditolak dengan sopan.
import { MessageCircle } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import Stamp from '@/components/Stamp'
import StatusIkon from '@/components/StatusIkon'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { api, GalatHttp } from '@/lib/api'
import { useGalatApi } from '@/lib/galat'
import { useCek } from '@/lib/store'
import type { ItemKartu } from './kartu'
import Sumber from './Sumber'

// /api/tanya membalas 404 kalau hasil cek sudah tidak ada di server (biasanya server restart).
const KEDALUWARSA = 'Hasil cek sudah kedaluwarsa, cek ulang ya.'

const SARAN = ['Angka ini dari mana?', 'Apa artinya untuk pemula?', 'Kenapa aturannya begitu?']

interface Tanya {
  pertanyaan: string
  jawaban?: string
  ditolak?: boolean
  galat?: string | null
}

function Jawaban({ t }: { t: Tanya }) {
  if (t.galat) {
    return (
      <p className="m-0 text-sm text-destructive">
        {t.galat}{' '}
        <Link to="/cek" className="font-semibold underline underline-offset-2">
          Cek ulang
        </Link>
      </p>
    )
  }
  if (t.ditolak) {
    return (
      <div className="rounded-md border border-line-2 bg-surface-2 px-3.5 py-3 text-sm">
        {t.jawaban}
        <b className="mt-1.5 block">Keputusan tetap di tanganmu.</b>
      </div>
    )
  }
  if (t.jawaban) return <p className="m-0 text-[15px] leading-relaxed text-ink">{t.jawaban}</p>
  return (
    <p className="m-0 flex items-center gap-2 text-sm text-muted-foreground">
      <StatusIkon status="jalan" className="size-4" /> Memeriksa data kartu ini…
    </p>
  )
}

function Percakapan({ riwayat }: { riwayat: Tanya[] }) {
  return (
    <ul className="m-0 grid list-none gap-3 p-0" aria-live="polite">
      {riwayat.map((t, i) => (
        <li key={i} className="grid gap-2">
          <p className="m-0 ml-auto max-w-[85%] rounded-[14px_14px_4px_14px] bg-surface-3 px-3 py-2 text-sm font-semibold">{t.pertanyaan}</p>
          <Jawaban t={t} />
        </li>
      ))}
    </ul>
  )
}

export default function PanelTanya({ item, kunci }: { item: ItemKartu; kunci: string }) {
  const { hasil } = useCek()
  const galat = useGalatApi()
  const [riwayat, setRiwayat] = useState<Tanya[]>([])
  const [ketik, setKetik] = useState('')
  const sibuk = riwayat.some((t) => !t.jawaban && !t.galat)

  async function tanya(pertanyaan: string) {
    if (!hasil || !pertanyaan.trim() || sibuk) return
    setKetik('')
    setRiwayat((r) => [...r, { pertanyaan }])
    let isi: Partial<Tanya>
    try {
      const res = await api.tanya({ cek_id: hasil.id, card: kunci, question: pertanyaan })
      isi = { jawaban: res.answer, ditolak: res.refused }
    } catch (e) {
      isi = { galat: e instanceof GalatHttp && e.status === 404 ? KEDALUWARSA : galat(e) }
    }
    setRiwayat((r) => r.map((t, i) => (i === r.length - 1 ? { ...t, ...isi } : t)))
  }

  const kirim = (e: FormEvent) => {
    e.preventDefault()
    void tanya(ketik)
  }
  const saran = SARAN.filter((s) => !riwayat.some((t) => t.pertanyaan === s))

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" className="ml-auto text-ink-2">
          <MessageCircle /> Tanya soal ini
        </Button>
      </SheetTrigger>
      <SheetContent side="bottom" className="mx-auto max-h-[88dvh] w-full max-w-md gap-0 overflow-y-auto rounded-t-[22px]">
        <SheetHeader className="border-b border-line pr-12 text-left">
          <SheetDescription className="text-[11.5px] font-semibold">{item.judul}</SheetDescription>
          <div className="flex items-start justify-between gap-3">
            <SheetTitle className="text-base leading-snug">{item.card.headline}</SheetTitle>
            <Stamp verdict={item.card.verdict} miring={-4} className="mt-0.5 flex-none text-[11px]" />
          </div>
          <Sumber sources={item.card.sources} />
        </SheetHeader>
        <div className="grid gap-4 p-4">
          <Percakapan riwayat={riwayat} />
          {saran.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {saran.map((s) => (
                <Button key={s} variant="outline" size="sm" disabled={sibuk} onClick={() => tanya(s)}>
                  {s}
                </Button>
              ))}
            </div>
          )}
          <form onSubmit={kirim} className="flex gap-2">
            <input
              value={ketik}
              onChange={(e) => setKetik(e.target.value)}
              placeholder="Tanya tentang kartu ini…"
              aria-label="Tanya tentang kartu ini"
              className="min-w-0 flex-1 rounded-full border border-line-2 bg-surface px-4 py-2 text-[15px] outline-none focus:border-ink-2"
            />
            <Button type="submit" disabled={sibuk || !ketik.trim()}>
              Tanya
            </Button>
          </form>
          <p className="m-0 text-[12.5px] text-muted-foreground">
            Jawaban hanya memakai data kartu ini. Kami tidak memberi saran beli, jual, atau tahan.
          </p>
        </div>
      </SheetContent>
    </Sheet>
  )
}
