// Kontrak FE–BE. HARUS sama dengan backend/app/schemas.py dan contract/examples/*.json.
// Ubah kontrak = PR berlabel `kontrak` (lihat contract/README.md).

export type Verdict = 'sesuai' | 'menyesatkan' | 'tidak_sesuai' | 'tidak_bisa_dicek' | 'info'
export type FormStatus = 'temuan' | 'aman' | 'modul_aktif' | 'tidak_relevan' | 'data_kurang' | 'gagal'
export type Fmt = 'pct' | 'rp' | 'int' | 'num' | 'x' | 'text'

export interface KlaimRequest {
  text?: string | null
  image_base64?: string | null
  ticker?: string | null
}

export interface Claim {
  id: string
  text: string
  span?: [number, number] | null
  checks: string[]
}

export interface KlaimResponse {
  ticker: string | null
  company?: string | null
  claims: Claim[]
  used_ai?: boolean
  /** Teks yang dibaca AI dari screenshot; `span` klaim menunjuk ke teks ini. Kosong untuk input teks. */
  source_text?: string | null
}

export interface Evidence { label: string; value: number | string | null; fmt: Fmt }
/** Label titik = tanggal ISO atau nama kategori; nilai mentah, diformat FE dengan `fmt` (bawaan BE: 'num'). */
export interface ChartSeries { name: string; points: [string, number][]; fmt: Fmt }
export interface Chart { type: 'line' | 'bar'; series: ChartSeries[] }
export interface Source { name: string; as_of?: string | null }

export interface Card {
  // A-3: konflik memakai rule_id A-3; periode/keterbatasan di reason, sumber per dataset yang tersedia.
  // H-2: harga awal yang paling dekat dan harga terakhir di evidence, masing-masing bertanggal di sources.
  claim_id?: string | null
  verdict: Verdict
  check?: string | null
  headline: string
  reason: string
  rule_id?: string | null
  rule_text?: string | null
  evidence: Evidence[]
  chart?: Chart | null
  sources: Source[]
}

export interface Step { check: string; label: string; ms: number }
export interface FormRow { check: string; status: FormStatus; why: string }
export interface Quota { used: number; limit: number; reset_at: string }

export interface CekRequest { ticker: string; claims: Claim[] }

export interface CekResponse {
  id: string
  ticker: string
  company?: string | null
  data_as_of?: string | null
  summary: string
  steps: Step[]
  claims: Card[]
  untold: Card[]
  form: FormRow[]
  quota?: Quota | null
}

export interface TanyaRequest { cek_id: string; card: string; question: string }

/** Nilai `bagian` ditentukan kode (JEV), bukan teks bebas LLM. */
export type BagianJawaban = 'angka_bukti' | 'alasan_aturan' | 'sumber_tanggal' | 'istilah' | 'di_luar_kartu'
/** Bagian internal yang dipakai kode untuk merakit jawaban. */
export type AnswerKind = 'angka' | 'aturan' | 'sumber' | 'istilah' | 'saran' | 'ringkasan' | 'tidak_ada'

export interface TanyaResponse {
  answer: string
  refused: boolean
  /** true = jawaban lewat klasifikasi JEV; false = dirakit kode penuh. */
  used_ai?: boolean
  answer_kind?: AnswerKind | null
  bagian?: BagianJawaban | null
}

export interface FreeFloatItem {
  ticker: string
  company?: string | null
  free_float: number
  market_cap: number
  kelompok: string
  target: number
  tenggat: string
  nilai_dilepas?: number | null
  hari_serap?: number | null
  tekanan?: 'ringan' | 'sedang' | 'berat' | null
  papan_pemantauan: boolean
}
export interface FreeFloatList { as_of?: string | null; items: FreeFloatItem[] }

export interface KomoditasItem {
  ticker: string
  komoditas: string
  porsi_pendapatan: number | null
  komoditas_terbesar: string | null
  porsi_terbesar: number | null
  tahun_buku: number | null
  korelasi: number
  kategori: 'lemah' | 'sedang' | 'cukup kuat'
  periode: string
  n_bulan: number
  total_return_saham: number | null
  perubahan_komoditas: number | null
  arah_tahunan: string[]
  sources: Source[]
}
export interface KomoditasList { as_of: string; jenis: string; items: KomoditasItem[] }
export interface KomoditasDetail { ticker: string; as_of: string; items: KomoditasItem[] }

export interface Rule { id: string; check: string | null; status: 'final' | 'usulan'; text: string; params: Record<string, number>; catatan?: string }
export interface Catalog {
  checks: { id: string; label: string; step_label: string; standar: boolean }[]
  untold: { id: string; label: string }[]
  rules: Rule[]
  quota: { cek_per_hari: number }
  tanya_tolak_regex: string
  /** Glosarium ikut kontrak: FE memakai teksnya, BE memakai kuncinya untuk menjawab Tanya. */
  glosarium: Glosarium
}

export interface GlosariumItem { key: string; nama: string; arti: string }
export interface GlosariumPemetaan { checks: Record<string, string>; untold: Record<string, string> }
/** Glosarium ikut kontrak: FE memakai teksnya (ikon info), BE memakai kuncinya untuk menjawab Tanya. */
export interface Glosarium { versi: string; pemetaan: GlosariumPemetaan; istilah: GlosariumItem[] }

/** Harus sama dengan backend/app/schemas.py → GlosariumKey dan kunci di contract/glosarium.json. */
export type KunciGlosarium =
  | 'laba' | 'per' | 'pbv' | 'dividen' | 'yield' | 'payout' | 'orang_dalam' | 'asing' | 'suspensi'
  | 'free_float' | 'hari_serap' | 'korelasi' | 'kapitalisasi' | 'papan_pemantauan'

export class KuotaHabisError extends Error {
  quota: Quota
  constructor(quota: Quota) {
    super('kuota_habis')
    this.quota = quota
  }
}
