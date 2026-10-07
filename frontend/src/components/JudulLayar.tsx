// Judul + kalimat pembuka di layar alat (gaya .sheet di prototipe).
import type { ReactNode } from 'react'

export default function JudulLayar({ judul, children }: { judul: ReactNode; children?: ReactNode }) {
  return (
    <header className="mt-3.5 mb-[22px]">
      <h1 className="m-0 mb-1.5 text-[clamp(27px,4.4vw,38px)] leading-[1.1] font-bold tracking-[-0.04em] text-balance">{judul}</h1>
      {children && <p className="m-0 text-ink-2">{children}</p>}
    </header>
  )
}
