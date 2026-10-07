// Kecilkan screenshot di browser sebelum dikirim: sisi terpanjang ≤ 1280 px, JPEG.
// Backend menolak gambar > 4 MB (tugas C2), dan unggahan kecil lebih cepat di jaringan HP.
const SISI_MAKS = 1280
const MUTU_JPEG = 0.85

/** Mengembalikan isi JPEG sebagai base64 tanpa awalan "data:...;base64,". */
export async function kecilkanGambar(file: File): Promise<string> {
  const bmp = await createImageBitmap(file)
  const skala = Math.min(1, SISI_MAKS / Math.max(bmp.width, bmp.height))
  const kanvas = document.createElement('canvas')
  kanvas.width = Math.round(bmp.width * skala)
  kanvas.height = Math.round(bmp.height * skala)
  const ctx = kanvas.getContext('2d')
  if (!ctx) throw new Error('canvas 2d tidak tersedia')
  // Latar putih: PNG transparan jadi hitam kalau langsung diubah ke JPEG.
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, kanvas.width, kanvas.height)
  ctx.drawImage(bmp, 0, 0, kanvas.width, kanvas.height)
  bmp.close()
  return kanvas.toDataURL('image/jpeg', MUTU_JPEG).split(',')[1]
}
