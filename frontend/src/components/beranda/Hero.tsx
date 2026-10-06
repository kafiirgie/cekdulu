import { Link, useNavigate } from 'react-router-dom'
import Stamp from '@/components/Stamp'
import { Button } from '@/components/ui/button'
import { CONTOH_KLAIM } from '@/lib/labels'
import { useCek } from '@/lib/store'
import { Pil } from './Bagian'

function BendaMeja() {
  return (
    <>
      <div className="mb-8 flex items-start justify-center gap-3.5 lg:contents" aria-hidden="true">
        <div className="kertas-tempel relative w-40 -rotate-[5deg] px-3.5 pt-5 pb-3.5 lg:absolute lg:top-0 lg:-left-2 lg:w-[180px] lg:px-[18px] lg:pt-6 lg:pb-5">
          <span className="absolute -top-2.5 left-1/2 h-[22px] w-[70px] -translate-x-1/2 -rotate-3 border border-black/5 bg-white/60" />
          <small className="mb-1.5 block text-[11px] font-semibold">Diteruskan dari grup</small>
          <p className="tulisan-tangan m-0 text-[16.5px] lg:text-xl">MDKA saham emas, emas naik pasti ikut!!</p>
        </div>
        <div className="relative mt-3 w-[170px] rotate-[4deg] rounded-lg border border-line bg-surface px-3 pt-6 pb-3 text-left shadow-lift lg:absolute lg:top-2 lg:-right-2 lg:mt-0 lg:w-[210px] lg:p-3.5">
          <Stamp verdict="menyesatkan" miring={8} className="absolute -top-3.5 -right-2.5 bg-surface text-xs lg:text-[15px]" />
          <div className="text-[11px] font-semibold text-muted-foreground">MDKA · data 30 Sep 2026</div>
          <p className="mt-1 mb-2 text-xs leading-tight font-bold lg:mb-3 lg:text-[13.5px]">82% pendapatan MDKA dari proyek nikel, bukan emas.</p>
          <div className="flex justify-between border-t border-line pt-1 font-mono text-[10px] text-ink-2 lg:text-[11.5px]">
            <span>Porsi nikel</span>
            <b>82%</b>
          </div>
        </div>
      </div>
      <div className="absolute bottom-14 left-7 hidden w-60 rotate-[3deg] rounded-lg border border-line bg-surface px-3.5 py-3 text-left shadow-lift lg:block" aria-hidden="true">
        <div className="flex justify-between text-[11.5px] font-bold text-ink-2">
          Grup Saham Keluarga <span className="font-medium text-muted-foreground">08.41</span>
        </div>
        <div className="gelembung-chat mt-2 px-3 py-2 text-[13.5px] leading-snug">MGLV masih bakal terbang, buruan masuk!</div>
      </div>
      <div className="absolute right-11 bottom-[86px] hidden h-[38px] w-[180px] -rotate-[18deg] lg:block" aria-hidden="true">
        <span className="absolute top-0 left-0 h-[38px] w-[132px] rounded-[10px_6px_6px_10px] bg-hl shadow-soft" />
        <span className="absolute top-0.5 left-[124px] h-[34px] w-[50px] rounded-[4px_12px_12px_4px] bg-ink" />
      </div>
    </>
  )
}

export default function Hero() {
  const { setText } = useCek()
  const nav = useNavigate()

  function cobaContoh() {
    setText(CONTOH_KLAIM[0])
    nav('/cek')
  }

  return (
    <section className="relative flex flex-col items-center justify-center pt-4 pb-14 text-center lg:min-h-[540px] lg:py-16" aria-labelledby="judul-beranda">
      <BendaMeja />
      <Pil>Aturan yang memutuskan, bukan AI</Pil>
      <h1 id="judul-beranda" className="mt-[18px] max-w-[17ch] text-[clamp(34px,5.8vw,56px)] leading-[1.05] font-bold tracking-[-0.045em] text-balance">
        <span className="block text-ink-3">Dengar klaim soal saham?</span>
        <span className="block">
          <span className="stabilo">Cek dulu</span> sebelum percaya.
        </span>
      </h1>
      <p className="mx-auto mt-5 max-w-[34rem] text-[clamp(15.5px,1.8vw,17.5px)] text-balance text-ink-2">
        Tempel pesan dari grup WhatsApp atau komentar di forum. Kami pecah jadi klaim, lalu periksa satu per satu ke data
        pasar dengan aturan yang sama setiap kali.
      </p>
      <div className="mt-7 flex flex-wrap justify-center gap-2.5">
        <Button asChild>
          <Link to="/cek">
            Cek klaim sekarang <span aria-hidden="true">→</span>
          </Link>
        </Button>
        <Button variant="outline" onClick={cobaContoh}>
          Coba dengan contoh
        </Button>
      </div>
      <p className="mt-3.5 text-[12.5px] text-muted-foreground">Gratis · Tanpa daftar · Bukan saran investasi</p>
      <a href="#alat" className="mt-3 text-[13.5px] font-semibold text-ink-2 underline decoration-dotted underline-offset-4 hover:text-ink">
        Sudah paham saham? Coba alat analisis
      </a>
    </section>
  )
}
