// Layar Kamus: semua istilah dari contract/glosarium.json (teks yang sama dengan ikon info), dikelompokkan per abjad.
import { useState } from 'react'
import InputBulat from '@/components/InputBulat'
import JudulLayar from '@/components/JudulLayar'
import { cocok } from '@/lib/cari'
import { ISTILAH, ISTILAH_CEK } from '@/lib/istilah'
import { labelCek } from '@/lib/labels'

/** Pemeriksa yang memakai istilah ini; nama yang sama dengan istilahnya dilewati karena tidak menambah info. */
function dipakaiDi(kunci: string, nama: string): string[] {
  return Object.entries(ISTILAH_CEK)
    .filter(([, k]) => k === kunci)
    .map(([id]) => labelCek(id))
    .filter((label) => label.toLowerCase() !== nama.toLowerCase())
}

const ENTRI = [...ISTILAH]
  .sort((a, b) => a.nama.localeCompare(b.nama, 'id'))
  .map((i) => {
    const tempat = dipakaiDi(i.key, i.nama)
    return { ...i, tempat, huruf: i.nama[0].toUpperCase(), teksCari: [i.nama, i.arti, ...tempat].join(' ') }
  })
type Entri = (typeof ENTRI)[number]

function kelompokkan(entri: Entri[]): [string, Entri[]][] {
  const grup = new Map<string, Entri[]>()
  for (const e of entri) grup.set(e.huruf, [...(grup.get(e.huruf) ?? []), e])
  return [...grup]
}

const SEMUA_HURUF = kelompokkan(ENTRI).map(([h]) => h)

function IndeksHuruf({ ada }: { ada: Set<string> }) {
  return (
    <nav aria-label="Lompat ke huruf" className="mb-6 flex flex-wrap gap-1">
      {SEMUA_HURUF.map((h) =>
        ada.has(h) ? (
          <a
            key={h}
            href={`#huruf-${h}`}
            className="grid size-8 place-items-center rounded-full border border-line-2 bg-surface text-sm font-bold shadow-soft hover:bg-hl-soft"
          >
            {h}
          </a>
        ) : (
          <span key={h} aria-hidden="true" className="grid size-8 place-items-center rounded-full border border-dashed border-line text-sm font-bold text-muted-foreground/50">
            {h}
          </span>
        ),
      )}
    </nav>
  )
}

function KartuIstilah({ e }: { e: Entri }) {
  return (
    <li id={e.key} className="rounded-lg border border-line bg-surface p-3.5 shadow-soft">
      <h3 className="m-0 mb-1 text-[15px] font-bold">{e.nama}</h3>
      <p className="m-0 text-sm text-ink-2">{e.arti}</p>
      {e.tempat.length > 0 && <p className="mt-2 mb-0 text-[12.5px] text-muted-foreground">Dipakai di: {e.tempat.join(' · ')}</p>}
    </li>
  )
}

export default function Kamus() {
  const [kueri, setKueri] = useState('')
  // Nama istilah didahulukan: "per" cukup menemukan PER, bukan semua penjelasan yang memuat "perusahaan".
  const cocokNama = ENTRI.filter((e) => cocok(kueri, e.nama))
  const hasil = cocokNama.length ? cocokNama : ENTRI.filter((e) => cocok(kueri, e.teksCari))
  const grup = kelompokkan(hasil)
  return (
    <section className="pb-6">
      <JudulLayar judul="Kamus">
        Istilah saham yang sering muncul di grup dan di hasil cek, dalam bahasa sehari-hari. Penjelasan yang sama muncul
        saat kamu mengetuk ikon ⓘ.
      </JudulLayar>
      <InputBulat
        type="search"
        value={kueri}
        onChange={(e) => setKueri(e.target.value)}
        placeholder="Cari istilah, mis. dividen atau harga saham"
        aria-label="Cari istilah"
        className="mb-3 w-full"
      />
      <IndeksHuruf ada={new Set(grup.map(([h]) => h))} />
      {kueri.trim() && (
        <p aria-live="polite" className="m-0 mb-3 text-sm text-muted-foreground">
          {hasil.length ? `${hasil.length} istilah cocok dengan "${kueri.trim()}".` : `Belum ada istilah untuk "${kueri.trim()}". Coba kata lain, mis. laba atau asing.`}
        </p>
      )}
      {grup.map(([huruf, entri]) => (
        <section key={huruf} id={`huruf-${huruf}`} aria-labelledby={`judul-${huruf}`} className="mb-6 scroll-mt-4">
          <h2 id={`judul-${huruf}`} className="m-0 mb-2.5 border-b border-line pb-1.5 text-[22px] font-bold tracking-[-0.03em]">
            {huruf}
          </h2>
          <ul className="m-0 grid list-none gap-2.5 p-0 sm:grid-cols-2">
            {entri.map((e) => (
              <KartuIstilah key={e.key} e={e} />
            ))}
          </ul>
        </section>
      ))}
    </section>
  )
}
