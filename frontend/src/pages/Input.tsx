// Layar 2 — Input. [A1] unggah screenshot (image_base64), gaya kertas bergaris dari prototipe.
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { CONTOH_KLAIM } from '@/lib/labels'
import { useCek } from '@/lib/store'

export default function Input() {
  const { text, setText, setKlaim, setHasil } = useCek()
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const nav = useNavigate()

  async function lanjut() {
    setLoading(true)
    setErr(null)
    try {
      const kodeSaja = /^\s*[A-Za-z]{4}\s*$/.test(text)
      const k = await api.klaim(kodeSaja ? { ticker: text.trim().toUpperCase() } : { text })
      setKlaim(k)
      setHasil(null)
      nav(k.claims.length ? '/cek/konfirmasi' : '/cek/hasil')
    } catch (e) {
      setErr(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <h2 className="text-lg font-semibold">Tempel klaimnya</h2>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={6}
        placeholder="Tempel pesan dari grup, atau ketik kode saham saja (mis. BBRI)"
        className="mt-2 w-full rounded-lg border border-neutral-300 bg-white p-3"
      />
      <div className="mt-2 flex flex-wrap gap-2">
        {CONTOH_KLAIM.map((c) => (
          <button key={c} onClick={() => setText(c)} className="rounded-full border px-3 py-1 text-xs">
            {c.slice(0, 28)}…
          </button>
        ))}
      </div>
      <button
        disabled={!text.trim() || loading}
        onClick={lanjut}
        className="mt-4 w-full rounded-lg bg-black py-3 font-semibold text-white disabled:opacity-40"
      >
        {loading ? 'Membaca klaim…' : 'Cek dulu'}
      </button>
      {err && <p className="mt-2 text-sm text-red-700">{err}</p>}
    </section>
  )
}
