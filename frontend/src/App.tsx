import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout, { KolomSempit } from '@/components/Layout'
import { CekProvider } from '@/lib/store'
import Beranda from '@/pages/Beranda'
import DetailPemeriksa from '@/pages/DetailPemeriksa'
import Formulir from '@/pages/Formulir'
import Hasil from '@/pages/Hasil'
import Input from '@/pages/Input'
import Konfirmasi from '@/pages/Konfirmasi'
import KuotaHabis from '@/pages/KuotaHabis'
import Metodologi from '@/pages/Metodologi'
import RadarFreeFloat from '@/pages/RadarFreeFloat'

export default function App() {
  return (
    <CekProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Beranda />} />
            <Route element={<KolomSempit />}>
              <Route path="cek" element={<Input />} />
              <Route path="cek/konfirmasi" element={<Konfirmasi />} />
              <Route path="cek/hasil" element={<Hasil />} />
              <Route path="cek/formulir" element={<Formulir />} />
              <Route path="cek/formulir/:check" element={<DetailPemeriksa />} />
              <Route path="alat/free-float" element={<RadarFreeFloat />} />
              <Route path="metodologi" element={<Metodologi />} />
              <Route path="kuota-habis" element={<KuotaHabis />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </CekProvider>
  )
}
