// Judul bagian rata kiri di layar panjang (Hasil, Metodologi) + keterangan kecil di kanan.
import type { ReactNode } from 'react'

export default function Seksi({ judul, sub, children }: { judul: string; sub?: string; children: ReactNode }) {
  return (
    <>
      <div className="mt-[34px] mb-3 flex items-baseline justify-between gap-3">
        <h2 className="m-0 text-[19px] font-bold tracking-[-0.025em]">{judul}</h2>
        {sub && <span className="text-[13px] text-muted-foreground">{sub}</span>}
      </div>
      {children}
    </>
  )
}
