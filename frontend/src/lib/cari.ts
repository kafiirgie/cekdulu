// Pencarian longgar untuk Kamus: tidak peduli huruf besar/kecil dan tanda baca, boleh sebagian kata, dan memaafkan salah ketik kecil.

const normal = (s: string) =>
  s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()

/** Jarak Levenshtein: berapa huruf yang harus diganti, ditambah, atau dibuang. */
function jarak(a: string, b: string): number {
  let baris = Array.from({ length: b.length + 1 }, (_, j) => j)
  for (let i = 1; i <= a.length; i++) {
    const baru = [i]
    for (let j = 1; j <= b.length; j++) {
      baru[j] = Math.min(baris[j] + 1, baru[j - 1] + 1, baris[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1))
    }
    baris = baru
  }
  return baris[b.length]
}

// Kata pendek harus persis (mis. "per"), kata panjang boleh meleset 1–2 huruf (mis. "devidin" → dividen).
const toleransi = (kata: string) => (kata.length >= 7 ? 2 : kata.length >= 4 ? 1 : 0)

function kataCocok(kata: string, kandidat: string): boolean {
  if (kandidat.includes(kata)) return true
  const batas = toleransi(kata)
  return batas > 0 && Math.min(jarak(kata, kandidat), jarak(kata, kandidat.slice(0, kata.length))) <= batas
}

/** Semua kata di `kueri` harus cocok dengan salah satu kata di `teks`. Kueri kosong = cocok. */
export function cocok(kueri: string, teks: string): boolean {
  const kandidat = normal(teks).split(' ')
  return normal(kueri)
    .split(' ')
    .filter(Boolean)
    .every((kata) => kandidat.some((k) => kataCocok(kata, k)))
}
