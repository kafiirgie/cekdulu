// ID perangkat untuk kuota 5 cek/hari (tanpa login). Disimpan di localStorage kalau bisa.
let memo: string | null = null

export function deviceId(): string {
  if (memo) return memo
  try {
    memo = localStorage.getItem('cekdulu_device')
    if (!memo) {
      memo = crypto.randomUUID()
      localStorage.setItem('cekdulu_device', memo)
    }
  } catch {
    memo = memo ?? crypto.randomUUID()
  }
  return memo
}
