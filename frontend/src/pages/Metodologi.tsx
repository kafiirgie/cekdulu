// Layar 11 — Metodologi: vonis, pemeriksa + aturan (rules.json lewat api.rules()), peran AI, batas, sumber data.
import { useEffect, useState } from 'react'
import { Pil } from '@/components/beranda/Bagian'
import DaftarAturan from '@/components/DaftarAturan'
import Istilah from '@/components/Istilah'
import JudulLayar from '@/components/JudulLayar'
import KotakDaftar from '@/components/KotakDaftar'
import Seksi from '@/components/Seksi'
import Stamp from '@/components/Stamp'
import { api } from '@/lib/api'
import type { Catalog, Verdict } from '@/lib/contract'
import { ISTILAH_CEK } from '@/lib/istilah'
import { VERDICT_ARTI } from '@/lib/labels'

// Peran AI (FINAL_PLAN §5).
const KOLOM_AI = [
  {
    judul: 'AI dipakai untuk',
    isi: [
      'Membaca teks dan screenshot',
      'Memecah teks jadi klaim dan kode saham',
      'Memilih pemeriksa yang relevan dengan klaim',
      'Menulis ulang hasil ke bahasa sehari-hari',
      'Menjawab pertanyaan lanjutan, hanya dari angka di kartu',
    ],
    gaya: 'border-line bg-surface',
  },
  {
    judul: 'AI tidak dipakai untuk',
    isi: ['Menentukan vonis', 'Menghitung angka', 'Memilih data', 'Memberi saran beli atau jual', 'Menebak harga'],
    gaya: 'border-dashed border-line-2 bg-surface-2',
  },
]

// Tanggal snapshot ikut data/bahan_produk/KAMUS_DATA.md; perbarui bersama datanya.
const SUMBER_LUAR = [
  { nama: 'World Bank Pink Sheet (CC BY)', isi: 'harga komoditas dunia bulanan, diperbarui 2 Sep 2026' },
  { nama: 'BPS WebAPI dataexim', isi: 'nilai ekspor bulanan per kode HS, sampai Jul 2026' },
  { nama: 'FRED CCUSMA02IDM618N', isi: 'kurs rupiah per dolar AS, rata-rata bulanan' },
  { nama: 'BEI', isi: 'Papan Pemantauan Khusus (unduh manual 30 Sep 2026) dan Peraturan I-A soal tenggat free float' },
]

function LimaVonis() {
  return (
    <ul className="m-0 grid list-none gap-2.5 p-0">
      {(Object.keys(VERDICT_ARTI) as Verdict[]).map((v) => (
        <li key={v} className="grid grid-cols-[8.5rem_1fr] items-center gap-3 rounded-lg border border-line bg-surface p-3 shadow-soft">
          <Stamp verdict={v} miring={-4} className="justify-self-start text-xs" />
          <span className="text-sm text-ink-2">{VERDICT_ARTI[v]}</span>
        </li>
      ))}
    </ul>
  )
}

function GrupPemeriksa({ cat, standar }: { cat: Catalog; standar: boolean }) {
  const cek = cat.checks.filter((c) => c.standar === standar)
  return (
    <KotakDaftar
      judul={standar ? 'Pemeriksa standar' : 'Modul khusus'}
      keterangan={standar ? 'selalu dijalankan' : 'aktif kalau syaratnya terpenuhi'}
      className="mb-3.5"
    >
      {cek.map((c) => {
        const istilah = ISTILAH_CEK[c.id]
        return (
          <li key={c.id} className="grid gap-2 border-t border-line px-4 py-3 first:border-t-0">
            <span className="text-[15px] font-bold">{istilah ? <Istilah k={istilah}>{c.label}</Istilah> : c.label}</span>
            <DaftarAturan aturan={cat.rules.filter((r) => r.check === c.id)} />
          </li>
        )
      })}
    </KotakDaftar>
  )
}

function DaftarPemeriksa({ cat, pesan }: { cat: Catalog | null; pesan: string | null }) {
  if (!cat) return <p className="m-0 text-sm text-ink-2">{pesan ?? 'Memuat aturan…'}</p>
  return (
    <>
      <GrupPemeriksa cat={cat} standar />
      <GrupPemeriksa cat={cat} standar={false} />
    </>
  )
}

function PeranAi() {
  return (
    <div className="grid gap-2.5 sm:grid-cols-2">
      {KOLOM_AI.map(({ judul, isi, gaya }) => (
        <div key={judul} className={`rounded-lg border p-3.5 ${gaya}`}>
          <h3 className="m-0 mb-2 text-sm font-bold">{judul}</h3>
          <ul className="m-0 grid gap-1 pl-4 text-sm text-ink-2">
            {isi.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

function SumberData() {
  return (
    <div className="grid gap-3 text-sm text-ink-2">
      <p className="m-0">
        Sumber inti: <b className="text-ink">Sectors API</b> (laporan keuangan, harga harian, transaksi investor asing,
        dividen, laporan orang dalam, suspensi, kepemilikan, segmen pendapatan, rating analis, aksi korporasi). Setiap
        angka di hasil menampilkan sumber dan tanggal datanya.
      </p>
      <ul className="m-0 grid gap-1.5 pl-4">
        {SUMBER_LUAR.map(({ nama, isi }) => (
          <li key={nama}>
            <b className="text-ink">{nama}</b>: {isi}
          </li>
        ))}
      </ul>
      <p className="m-0">
        Catatan: definisi <Istilah k="free_float" /> di Sectors tidak persis sama dengan BEI, jadi daftar Radar Free
        Float bisa berbeda dari daftar resmi BEI.
      </p>
    </div>
  )
}

export default function Metodologi() {
  const [cat, setCat] = useState<Catalog | null>(null)
  const [pesan, setPesan] = useState<string | null>(null)
  useEffect(() => {
    api.rules().then(setCat, () => setPesan('Daftar aturan belum bisa dimuat. Coba lagi sebentar lagi.'))
  }, [])
  return (
    <section className="pb-6">
      <div className="mt-3.5">
        <Pil>Metodologi</Pil>
      </div>
      <JudulLayar judul="Bagaimana cek dulu. memeriksa">
        Setiap cek menjalankan pemeriksaan yang sama, dengan urutan yang sama. Vonis ditentukan oleh aturan tertulis di
        bawah ini dan dihitung dari data, bukan dipilih oleh AI.
      </JudulLayar>
      <Seksi judul="Lima vonis">
        <LimaVonis />
      </Seksi>
      <Seksi judul="Pemeriksa dan aturannya" sub="usulan = angka sementara">
        <DaftarPemeriksa cat={cat} pesan={pesan} />

      </Seksi>
      <Seksi judul="Peran AI" sub="aturan yang memutuskan">
        <PeranAi />
      </Seksi>
      <Seksi judul="Yang tidak bisa diperiksa">
        <p className="m-0 mb-2.5 text-sm text-ink-2">
          Prediksi harga, opini, rumor tanpa angka, dan informasi yang belum dipublikasikan. Kami juga sengaja tidak
          membuat ramalan harga atau saran beli/jual.
        </p>
        {cat && <DaftarAturan aturan={cat.rules.filter((r) => r.check === null)} />}
      </Seksi>
      <Seksi judul="Sumber data">
        <SumberData />
      </Seksi>
    </section>
  )
}
