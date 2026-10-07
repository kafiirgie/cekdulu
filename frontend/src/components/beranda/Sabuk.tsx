// Sabuk klaim: klaim mentah lewat meja periksa lalu keluar sebagai kartu bercap vonis.
// Posisi digerakkan langsung lewat DOM (requestAnimationFrame) supaya tidak me-render React tiap frame;
// React hanya me-render ulang saat satu slot berganti isi.
import { memo, useEffect, useRef, useState, type CSSProperties } from 'react'
import { Logo } from '@/components/Logo'
import Stamp from '@/components/Stamp'
import { cn } from '@/lib/utils'
import type { ContohSabuk } from './contoh'

interface Slot {
  kunci: number
  contoh: ContohSabuk
  miring: number
  miringCap: number
}

const acak = (min: number, max: number) => Math.round((min + Math.random() * (max - min)) * 10) / 10

/** Ukuran sabuk dari lebar layar + variabel CSS --iw (lebar item) dan --mw (lebar meja). */
function ukur(akar: HTMLElement) {
  const cs = getComputedStyle(akar)
  const iw = parseFloat(cs.getPropertyValue('--iw'))
  const mw = parseFloat(cs.getPropertyValue('--mw'))
  const lebar = akar.clientWidth
  const jarak = iw + (lebar < 640 ? 46 : 70)
  const n = Math.ceil((lebar + iw) / jarak) + 1
  return { iw, mw, lebar, jarak, n, panjang: n * jarak, cepat: lebar < 640 ? 42 : 58 }
}

function KlaimMentah({ c, miring }: { c: ContohSabuk; miring: number }) {
  const style = { '--rot': `${miring}deg` } as CSSProperties
  if (c.jenis === 'tempel') {
    return (
      <div className="klaim-mentah kertas-tempel px-3.5 py-4" style={style}>
        <p className="tulisan-tangan m-0 text-[15px] sm:text-[17px]">{c.teks}</p>
      </div>
    )
  }
  if (c.jenis === 'chat') {
    return (
      <div className="klaim-mentah rounded-[14px] border border-line bg-surface px-3 py-2.5 text-left shadow-lift" style={style}>
        <div className="text-[10.5px] font-bold text-muted-foreground">{c.dari}</div>
        <p className="gelembung-chat mt-1.5 mb-0 px-2.5 py-2 text-[11.5px] leading-snug sm:text-[13px]">{c.teks}</p>
      </div>
    )
  }
  return (
    <div className="klaim-mentah rounded-md border border-line bg-surface p-3.5 text-left shadow-lift" style={style}>
      <span className="mb-1.5 block text-[10.5px] font-semibold text-muted-foreground">{c.dari}</span>
      <p className="m-0 text-[11.5px] leading-snug font-semibold sm:text-[13.5px]">“{c.teks}”</p>
    </div>
  )
}

function KlaimHasil({ c, miring }: { c: ContohSabuk; miring: number }) {
  return (
    <div className="klaim-hasil rounded-xl border border-line bg-surface p-3 text-left shadow-soft">
      <span className="text-[10.5px] font-semibold text-muted-foreground">Klaim</span>
      <p className="mt-0.5 mb-0 text-[11.5px] leading-tight font-bold tracking-[-0.01em] sm:text-[13px]">{c.hasil}</p>
      <Stamp verdict={c.vonis} miring={miring} className="absolute right-2.5 bottom-2.5 text-[10.5px] sm:text-xs" />
    </div>
  )
}

function Sabuk({ contoh, className }: { contoh: ContohSabuk[]; className?: string }) {
  const akarRef = useRef<HTMLDivElement>(null)
  const mejaRef = useRef<HTMLDivElement>(null)
  const garisRef = useRef<HTMLDivElement>(null)
  const itemRef = useRef<(HTMLDivElement | null)[]>([])
  const tataRef = useRef<() => void>(null)
  const [slots, setSlots] = useState<Slot[]>([])

  useEffect(() => {
    const akar = akarRef.current
    const meja = mejaRef.current
    const garis = garisRef.current
    if (!akar || !meja || !garis) return

    const diam = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let kunci = 0
    let urut = 0
    let offset = 0
    let last = 0
    let raf = 0
    let pertama = true
    let u = ukur(akar)
    let isi: Slot[] = []
    let posLalu: (number | null)[] = []

    const slotBaru = (): Slot => ({
      kunci: kunci++,
      contoh: contoh[urut++ % contoh.length],
      miring: acak(-7, 7),
      miringCap: acak(-9, -3),
    })

    function bangun() {
      u = ukur(akar!)
      urut = 0
      offset = u.jarak * 0.35
      pertama = true
      isi = Array.from({ length: u.n }, slotBaru)
      posLalu = isi.map(() => null)
      setSlots(isi)
    }

    function gerak(t: number) {
      const dt = last ? Math.min((t - last) / 1000, 0.05) : 0
      last = t
      offset += u.cepat * dt
      tata()
      if (!diam) raf = requestAnimationFrame(gerak)
    }

    // Satu frame: geser item, ganti isi item yang balik ke kiri, pasang cap saat lewat meja.
    function tata() {
      const { iw, mw, jarak, panjang } = u
      const tengah = u.lebar / 2
      let berganti = false
      isi.forEach((_, i) => {
        const p = ((i * jarak + offset) % panjang) - iw
        const lalu = posLalu[i]
        posLalu[i] = p
        if (lalu !== null && p < lalu) {
          isi[i] = slotBaru()
          berganti = true
          return
        }
        const node = itemRef.current[i]
        if (!node) return
        node.style.transform = `translateX(${p}px)`
        if (!node.classList.contains('selesai') && p + iw / 2 >= tengah) {
          node.classList.add('selesai')
          if (pertama) node.classList.add('instant')
          else {
            meja!.classList.remove('sibuk')
            void meja!.offsetWidth
            meja!.classList.add('sibuk')
          }
        }
        if (node.classList.contains('selesai') && !node.classList.contains('stamped') && p >= tengah + mw / 2 - 8) {
          node.classList.add('stamped')
        }
      })
      if (itemRef.current.some(Boolean)) pertama = false
      garis!.style.transform = `translateX(${offset % 23}px)`
      if (berganti) setSlots([...isi])
    }

    function mulai() {
      if (diam || raf) return
      last = 0
      raf = requestAnimationFrame(gerak)
    }
    function berhenti() {
      cancelAnimationFrame(raf)
      raf = 0
    }

    tataRef.current = tata
    bangun()

    const terlihat = new IntersectionObserver(([e]) => (e.isIntersecting ? mulai() : berhenti()))
    terlihat.observe(akar)

    let tundaUkur = 0
    const ukurUlang = () => {
      clearTimeout(tundaUkur)
      tundaUkur = window.setTimeout(() => {
        const jalan = raf !== 0
        berhenti()
        bangun()
        if (jalan) mulai()
      }, 150)
    }
    window.addEventListener('resize', ukurUlang)

    return () => {
      berhenti()
      clearTimeout(tundaUkur)
      terlihat.disconnect()
      window.removeEventListener('resize', ukurUlang)
    }
  }, [contoh])

  // Tata ulang tepat setelah React memasang item baru, supaya item tidak sempat tampil di posisi awal.
  // Di mode gerak-dikurangi ini satu-satunya frame yang digambar.
  useEffect(() => tataRef.current?.(), [slots])

  return (
    <div ref={akarRef} className={cn('sabuk', className)} aria-hidden="true">
      <div className="sabuk-jalur">
        <div ref={garisRef} className="sabuk-garis" />
      </div>
      {slots.map((s, i) => (
        <div
          key={s.kunci}
          ref={(n) => {
            itemRef.current[i] = n
          }}
          className="sabuk-item"
        >
          <KlaimMentah c={s.contoh} miring={s.miring} />
          <KlaimHasil c={s.contoh} miring={s.miringCap} />
        </div>
      ))}
      <div
        ref={mejaRef}
        className="meja-periksa absolute top-1/2 left-1/2 z-[4] flex size-[var(--mw)] -translate-1/2 flex-col items-center justify-center gap-3 rounded-[28px] border border-line-2 bg-surface shadow-[0_30px_50px_-24px_rgb(0_0_0/0.35),inset_0_0_0_6px_var(--cd-surface-2),inset_0_0_0_7px_var(--cd-line)]"
      >
        <Logo className="h-auto w-[42%]" />
        <span className="flex items-center gap-[7px] text-[11px] font-semibold text-ink-2">
          <span className="led size-[7px] rounded-full bg-line-2" />
          MEJA PERIKSA
        </span>
      </div>
    </div>
  )
}

// Di formulir berjalan induknya re-render tiap langkah; props sabuk tetap sama.
export default memo(Sabuk)
