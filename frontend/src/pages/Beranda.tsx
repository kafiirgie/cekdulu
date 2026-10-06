// Layar 1 — Beranda, dari prototipe iterasi 3 dengan contoh skenario asli (FINAL_PLAN §6).
import AlatAnalisis from '@/components/beranda/AlatAnalisis'
import Bento from '@/components/beranda/Bento'
import CaraKerja from '@/components/beranda/CaraKerja'
import Hero from '@/components/beranda/Hero'

export default function Beranda() {
  return (
    <>
      <Hero />
      <CaraKerja />
      <AlatAnalisis />
      <Bento />
    </>
  )
}
