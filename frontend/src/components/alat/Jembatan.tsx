// Jembatan dari layar detail modul ke cek klaim saham yang sama.
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useCek } from '@/lib/store'

export default function Jembatan({ kode }: { kode: string }) {
  const { setText } = useCek()
  const nav = useNavigate()
  const cekKlaim = () => {
    setText(kode)
    nav('/cek')
  }
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line-2 bg-surface-2 p-[18px]">
      <p className="m-0 text-sm text-ink-2">
        Dengar klaim soal <b className="text-ink">{kode}</b> di grup? Periksa dengan aturan yang sama.
      </p>
      <Button onClick={cekKlaim}>
        Cek klaim saham ini <span aria-hidden="true">→</span>
      </Button>
    </div>
  )
}
