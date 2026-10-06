// Layar 6 — Formulir inspeksi. [A3] gaya formulir dari prototipe + detail pemeriksa (layar 7).
import { Navigate } from 'react-router-dom'
import { STATUS_LABEL } from '@/lib/labels'
import { useCek } from '@/lib/store'

export default function Formulir() {
  const { hasil } = useCek()
  if (!hasil) return <Navigate to="/cek" replace />
  return (
    <section>
      <h2 className="text-lg font-semibold">Formulir inspeksi {hasil.ticker}</h2>
      <table className="mt-3 w-full text-sm">
        <tbody>
          {hasil.form.map((f) => (
            <tr key={f.check} className="border-b align-top">
              <td className="py-2 pr-2 font-medium">{f.check}</td>
              <td className="py-2 pr-2">{STATUS_LABEL[f.status]}</td>
              <td className="py-2 text-muted-foreground">{f.why}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
