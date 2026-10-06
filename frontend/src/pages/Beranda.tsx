// [A0] Ganti dengan hero, sabuk klaim → cap vonis, 3 langkah, bento dari prototipe iterasi 3.
import { Link } from 'react-router-dom'

export default function Beranda() {
  return (
    <section className="py-8">
      <h1 className="text-3xl font-bold leading-tight">Dengar klaim soal saham? Cek dulu sebelum percaya.</h1>
      <p className="mt-3 text-neutral-700">
        Tempel pesan dari grup. Kami pecah jadi klaim, lalu cek satu per satu ke data pasar dengan aturan tertulis.
      </p>
      <Link to="/cek" className="mt-6 inline-block rounded-lg bg-black px-5 py-3 font-semibold text-white">
        Cek klaim sekarang
      </Link>
    </section>
  )
}
