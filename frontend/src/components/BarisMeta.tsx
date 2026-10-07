// Baris kecil di atas judul layar formulir: lencana (pil/status) + keterangan saham dan tanggal data.
import type { ReactNode } from 'react'

export default function BarisMeta({ lencana, children }: { lencana: ReactNode; children: ReactNode }) {
  return (
    <div className="mt-3.5 flex flex-wrap items-center gap-2.5">
      {lencana}
      <span className="font-mono text-[11px] text-muted-foreground uppercase">{children}</span>
    </div>
  )
}
