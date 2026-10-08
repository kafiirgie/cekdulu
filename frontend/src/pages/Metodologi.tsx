// Layar 11 — Metodologi: alasan aturan, vonis, pemeriksa + aturan (rules.json lewat api.rules()), peran AI, batas, kartu konteks, sumber data.
import { useEffect, useState } from 'react'
import DaftarAturan from '@/components/DaftarAturan'
import Istilah from '@/components/Istilah'
import JudulLayar from '@/components/JudulLayar'
import KotakDaftar from '@/components/KotakDaftar'
import Seksi from '@/components/Seksi'
import Stamp from '@/components/Stamp'
import { api } from '@/lib/api'
import type { Catalog, Verdict } from '@/lib/contract'
import { ISTILAH, ISTILAH_CEK, istilah, type KunciIstilah } from '@/lib/istilah'
import { ATURAN_TIDAK_BISA_DICEK, VERDICT_ARTI } from '@/lib/labels'

// Peran AI (FINAL_PLAN §5).
const KOLOM_AI = [
  {
    judul: 'AI dipakai untuk',
    isi: [
      'Membaca teks dan screenshot',
      'Memecah teks jadi klaim dan kode saham',
      'Memilih pemeriksa yang relevan dengan klaim',
      'Menandai ramalan dan target harga, supaya tidak diberi vonis',
      'Memilih bagian kartu yang menjawab pertanyaan lanjutan',
    ],
    gaya: 'border-line bg-surface',
  },
  {
    judul: 'AI tidak dipakai untuk',
    isi: ['Menentukan vonis', 'Menghitung angka', 'Memilih data', 'Menulis kalimat hasil dan jawaban', 'Memberi saran beli atau jual', 'Menebak harga'],
    gaya: 'border-dashed border-line-2 bg-surface-2',
  },
]

// Alasan vonis memakai aturan tertulis, bukan jawaban AI (FINAL_PLAN §5).
const ALASAN_ATURAN = [
  {
    judul: 'Angka tidak dikarang',
    isi: 'AI bisa menyebut angka yang terdengar yakin padahal salah. Di sini setiap angka dihitung dari data Sectors dan ditampilkan bersama sumber dan tanggalnya.',
  },
  {
    judul: 'Tidak terbawa emosi',
    isi: 'Pesan yang heboh, penuh emoji, atau bikin FOMO tidak membuat klaim jadi lebih benar. Aturan hanya membaca isi klaim, lalu mencocokkannya dengan data.',
  },
  {
    judul: 'Sama untuk semua saham',
    isi: 'Batas angkanya sama untuk saham mana pun dan siapa pun yang mengirim. Data dan klaim yang sama selalu menghasilkan vonis yang sama.',
  },
  {
    judul: 'Bisa kamu periksa sendiri',
    isi: 'Semua aturan tertulis di halaman ini. Kartu hasil menyebut kode aturan yang dipakai, jadi kalau tidak setuju, kamu tahu bagian mana yang dipersoalkan.',
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

function AlasanAturan() {
  return (
    <ul className="m-0 grid list-none gap-2.5 p-0 sm:grid-cols-2">
      {ALASAN_ATURAN.map(({ judul, isi }) => (
        <li key={judul} className="rounded-lg border border-line bg-surface p-3.5 shadow-soft">
          <h3 className="m-0 mb-1 text-sm font-bold">{judul}</h3>
          <p className="m-0 text-sm text-ink-2">{isi}</p>
        </li>
      ))}
    </ul>
  )
}

/** Bagian nama yang sendirinya istilah kamus (Radar "Free Float") diberi ikon info; sisanya teks biasa. */
function LabelBeristilah({ label }: { label: string }) {
  const kecil = label.toLowerCase()
  const i = ISTILAH.find((x) => kecil.includes(x.nama.toLowerCase()))
  if (!i) return <>{label}</>
  const awal = kecil.indexOf(i.nama.toLowerCase())
  const akhir = awal + i.nama.length
  return (
    <>
      {label.slice(0, awal)}
      <Istilah k={i.key}>{label.slice(awal, akhir)}</Istilah>
      {label.slice(akhir)}
    </>
  )
}

/**
 * Nama pemeriksa diberi ikon info hanya kalau istilahnya memang nama itu (Laba → Laba bersih).
 * Kalau beda (Saham vs komoditas → Korelasi), istilahnya ditulis terpisah supaya yang digarisbawahi = yang dijelaskan.
 */
function NamaPemeriksa({ label, k }: { label: string; k?: KunciIstilah }) {
  if (k && istilah(k).nama.toLowerCase().startsWith(label.toLowerCase())) return <Istilah k={k}>{label}</Istilah>
  return (
    <>
      <LabelBeristilah label={label} />
      {k && (
        <span className="ml-2 text-[13px] font-medium text-muted-foreground">
          istilah: <Istilah k={k} />
        </span>
      )}
    </>
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
      {cek.map((c) => (
        <li key={c.id} className="grid gap-2 border-t border-line px-4 py-3 first:border-t-0">
          <span className="text-[15px] font-bold">
            <NamaPemeriksa label={c.label} k={ISTILAH_CEK[c.id]} />
          </span>
          <DaftarAturan aturan={cat.rules.filter((r) => r.check === c.id)} />
        </li>
      ))}
    </KotakDaftar>
  )
}

function DaftarPemeriksa({ cat, pesan }: { cat: Catalog | null; pesan: string | null }) {
  if (!cat) return <p className="m-0 text-sm text-ink-2">{pesan ?? 'Memuat aturan…'}</p>
  return (
    <>
      <p className="m-0 mb-3 text-sm text-ink-2">
        Setiap aturan punya kode, mis. L-1 untuk aturan laba. Kode yang sama muncul di kartu hasil, jadi kamu bisa
        melihat aturan mana yang menentukan vonisnya.
      </p>
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
          <ul className="m-0 grid list-disc gap-1 pl-5 text-sm text-ink-2 marker:text-hl-edge">
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
      <ul className="m-0 grid list-disc gap-1.5 pl-5 marker:text-hl-edge">
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
      <JudulLayar
        judul={
          <>
            Bagaimana <span className="stabilo whitespace-nowrap">cek dulu.</span> memeriksa
          </>
        }
      >
        Setiap cek menjalankan pemeriksaan yang sama, dengan urutan yang sama. Vonis ditentukan oleh aturan tertulis di
        bawah ini dan dihitung dari data, bukan dipilih oleh AI.
      </JudulLayar>
      <Seksi judul="Kenapa aturan, bukan AI?">
        <AlasanAturan />
      </Seksi>
      <Seksi judul="Lima vonis">
        <LimaVonis />
      </Seksi>
      <Seksi judul="Pemeriksa dan aturannya">
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
        <p className="m-0 mb-2.5 text-sm text-ink-2">
          Pos sekali jadi belum dibedakan: kalau <Istilah k="laba" /> naik karena kejadian satu kali, misalnya penjualan
          aset atau keuntungan selisih kurs, cek laba tetap membacanya sebagai kenaikan laba biasa.
        </p>
        {cat && <DaftarAturan aturan={cat.rules.filter((r) => r.id === ATURAN_TIDAK_BISA_DICEK)} />}
      </Seksi>
      <Seksi judul="Yang tidak diceritakan" sub="konteks, bukan vonis">
        <p className="m-0 mb-2.5 text-sm text-ink-2">
          Selain memeriksa klaim, kami menambahkan kartu konteks yang sering tidak disebut di grup. Kartu ini tidak
          menilai klaim, hanya mencatat hal yang perlu diketahui.
        </p>
        {cat && <DaftarAturan aturan={cat.rules.filter((r) => r.check === null && r.id !== ATURAN_TIDAK_BISA_DICEK)} />}
      </Seksi>
      <Seksi judul="Sumber data">
        <SumberData />
      </Seksi>
    </section>
  )
}
