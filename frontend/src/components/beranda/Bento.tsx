// "Yang kamu dapat": empat ubin yang memperlihatkan isi hasil cek. Angka dari FINAL_PLAN §6 (data 30 Sep 2026).
import { Info } from 'lucide-react'
import type { ReactNode } from 'react'
import { Logo, Wordmark } from '@/components/Logo'
import StatusIkon from '@/components/StatusIkon'
import Stamp from '@/components/Stamp'
import type { Verdict } from '@/lib/contract'
import { ATURAN, CEK_STANDAR } from '@/lib/labels'
import { cn } from '@/lib/utils'
import JudulBagian, { CatatanSumber } from './Bagian'

const kartuMini = 'rounded-[12px] border border-line bg-surface px-3.5 py-3 text-left text-[13px] shadow-lift'

function Ubin({ judul, isi, lebar = false, children }: { judul: string; isi: string; lebar?: boolean; children: ReactNode }) {
  return (
    <div className={cn('flex flex-col overflow-hidden rounded-xl border border-line bg-surface p-[22px] shadow-soft md:min-h-[300px]', lebar ? 'md:col-span-3' : 'md:col-span-2')}>
      <div className="relative grid flex-1 place-items-center pt-2.5 pb-[18px]" aria-hidden="true">
        {children}
      </div>
      <h3 className="m-0 text-[17px] font-bold tracking-[-0.02em]">{judul}</h3>
      <p className="mt-1 mb-0 text-sm text-ink-2">{isi}</p>
    </div>
  )
}

function VonisMini({ vonis, k, isi, gaya }: { vonis: Verdict; k: string; isi: string; gaya: string }) {
  return (
    <div className={cn(kartuMini, 'grid w-[min(280px,100%)] grid-cols-[1fr_auto] items-start gap-x-2.5', gaya)}>
      <span className="pt-1 text-[10.5px] font-semibold text-muted-foreground">{k}</span>
      <Stamp verdict={vonis} miring={-7} className="text-xs" />
      <p className="col-span-2 mt-2 mb-0 text-sm leading-[1.3] font-bold">{isi}</p>
    </div>
  )
}

const GAYA_BARIS = { aman: '', jalan: 'bg-surface-2 font-bold', antre: 'text-muted-foreground' }

function LangkahMini() {
  const [a, b, c] = CEK_STANDAR
  const baris: { teks: string; tanda: keyof typeof GAYA_BARIS }[] = [
    { teks: 'Membaca klaim', tanda: 'aman' },
    { teks: a.step_label, tanda: 'aman' },
    { teks: b.step_label, tanda: 'jalan' },
    { teks: c.step_label, tanda: 'antre' },
  ]
  return (
    <div className={cn(kartuMini, 'grid w-[min(290px,100%)] gap-0.5 p-2')}>
      {baris.map((r) => (
        <div key={r.teks} className={cn('grid grid-cols-[18px_1fr] items-center gap-2 rounded-lg px-2 py-[7px]', GAYA_BARIS[r.tanda])}>
          <StatusIkon status={r.tanda} className="size-[15px] border-[1.5px] text-[9px]" />
          <span>{r.teks}</span>
        </div>
      ))}
    </div>
  )
}

function KartuBagiMini() {
  const baris: { teks: string; vonis: Verdict }[] = [
    { teks: 'Bakal terbang', vonis: 'tidak_bisa_dicek' },
    { teks: 'Dari 600 ke 14 ribuan', vonis: 'sesuai' },
    { teks: 'Disuspensi 7 kali', vonis: 'info' },
  ]
  return (
    <div className={cn(kartuMini, 'flex aspect-[4/5] w-[196px] -rotate-[4deg] flex-col gap-1.5')}>
      <div className="flex items-center gap-1.5 text-xs font-extrabold tracking-[-0.02em]">
        <Logo className="size-4" />
        <Wordmark className="text-xs" /> · MGLV
      </div>
      {baris.map((r) => (
        <div key={r.teks} className="flex items-center justify-between gap-1 rounded-md bg-surface-2 px-1.5 py-[5px] text-[10.5px] font-semibold">
          {r.teks}
          <Stamp verdict={r.vonis} miring={-4} className="border-[1.5px] text-[8.5px] shadow-none" />
        </div>
      ))}
      <div className="mt-auto text-[8.5px] text-muted-foreground">Data dari Sectors · Bukan saran investasi</div>
    </div>
  )
}

function AturanMini({ id }: { id: string }) {
  const aturan = ATURAN.find((r) => r.id === id)
  if (!aturan) return null
  return (
    <div className={cn(kartuMini, 'w-[min(260px,100%)] font-mono text-[11.5px] leading-relaxed text-ink-2')}>
      <b className="text-ink">{aturan.id}</b> {aturan.text}
    </div>
  )
}

export default function Bento() {
  return (
    <section className="pt-2.5 pb-10">
      <JudulBagian
        pil="Yang kamu dapat"
        judul="Jelas, jujur, dan bisa dikirim balik ke grup."
        sub="Kami tidak bilang harus apa. Kami tunjukkan datanya."
      />
      <div className="grid gap-3.5 md:grid-cols-6">
        <Ubin lebar judul="Vonis per klaim" isi="Satu kalimat sederhana dulu. Angka dan sumbernya ada kalau kamu mau lihat.">
          <div>
            <VonisMini vonis="sesuai" k="BUMI · klaim 1" isi="Pemegang saham naik dari 226 rb ke 590 rb." gaya="-translate-x-2.5 -rotate-2" />
            <VonisMini vonis="tidak_sesuai" k="BUMI · klaim 2" isi="Porsi asing justru turun dari 81% ke 69%." gaya="-mt-2 translate-x-4 rotate-2" />
          </div>
        </Ubin>
        <Ubin lebar judul="Prosesnya terlihat" isi="Kamu tahu apa yang sedang diperiksa, satu per satu.">
          <LangkahMini />
        </Ubin>
        <Ubin judul="Istilah dijelaskan" isi="Ketuk ikon info untuk arti dalam bahasa sehari-hari.">
          <div className="w-[min(260px,100%)]">
            <div className="text-sm leading-normal text-ink-2">
              …pembagian <u className="decoration-dotted underline-offset-[3px]">dividen</u>
              <Info aria-hidden="true" className="ml-0.5 inline-block size-[0.85em] align-[-0.08em] text-muted-foreground" /> tahun ini…
            </div>
            <div className="mt-2.5 rounded-[10px] bg-pop px-3 py-2.5 text-[12.5px] leading-[1.45] text-on-pop">
              <b className="block text-hl">Dividen</b>
              Bagian keuntungan yang dibagikan ke pemegang saham. Mirip bagi hasil.
            </div>
          </div>
        </Ubin>
        <Ubin judul="Kirim balik ke grup" isi="Satu kartu yang langsung dikenali di WhatsApp.">
          <KartuBagiMini />
        </Ubin>
        <Ubin judul="Aturan tertulis" isi="Setiap vonis punya nomor aturan yang bisa kamu baca di Metodologi.">
          <AturanMini id="T-1" />
        </Ubin>
      </div>
      <CatatanSumber />
    </section>
  )
}
