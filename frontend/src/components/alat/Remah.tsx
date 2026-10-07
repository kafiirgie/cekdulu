// Jejak navigasi kecil di atas judul layar alat: "Alat analisis / Radar Free Float / BREN".
import { Fragment } from 'react'
import { Link } from 'react-router-dom'

export default function Remah({ jejak }: { jejak: { label: string; ke?: string }[] }) {
  return (
    <nav aria-label="Jejak" className="mt-3.5 flex flex-wrap items-center gap-1.5 text-[13px] font-semibold text-muted-foreground">
      {jejak.map((j, i) => (
        <Fragment key={j.label}>
          {i > 0 && <span aria-hidden="true">/</span>}
          {j.ke ? (
            <Link to={j.ke} className="hover:text-ink">
              {j.label}
            </Link>
          ) : (
            <span className="text-ink">{j.label}</span>
          )}
        </Fragment>
      ))}
    </nav>
  )
}
