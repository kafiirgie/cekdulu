"""Pemeriksa modul — "saham X = saham komoditas Y?". Aturan K-1, K-2.  [Lane D]"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..modul import komoditas as k
from ..data.sectors import DataUnavailable
from ..schemas import Claim, Evidence
from ..catalog import param
from .base import Checker, Outcome, card, periode_bulan_id, persen_id


class MKomoditas(Checker):
    id = "m_komoditas"

    def run(self, ticker: str, claim: Optional[Claim], today: date) -> Outcome:
        jenis = k.komoditas_disebut(claim.text) if claim else None
        if claim is None or jenis is None:
            return Outcome("tidak_relevan", "Klaim tidak menyebut komoditas.")
        porsi = k.porsi_pendapatan(ticker, jenis)
        terbesar, porsi_besar = k.komoditas_terbesar(ticker)
        menyesatkan = k.aturan_k1(porsi)
        h = (f"Pendapatan {ticker} paling banyak dari {terbesar} ({persen_id(porsi_besar, 0)}), sedangkan dari {jenis} hanya {persen_id(porsi, 0)}."
             if menyesatkan else f"{persen_id(porsi, 0)} pendapatan {ticker} memang dari {jenis}.")
        ev = [Evidence(label=f"Porsi pendapatan murni {jenis}", value=porsi, fmt="pct"),
              Evidence(label=f"Sumber terbesar: {terbesar}", value=porsi_besar, fmt="pct")]
        sumber = [k.sumber_segmen(ticker)]
        alasan = (f"Sebuah saham baru pantas disebut saham {jenis} kalau minimal "
                  f"{persen_id(param('K-1', 'batas_porsi_pendapatan'), 0)} pendapatannya dari {jenis}. "
                  "Segmen campuran tidak dihitung sebagai pendapatan murni satu komoditas.")
        try:
            data = k.item(ticker, jenis)
            alasan += (f" Harga saham dan harga {jenis} dunia punya hubungan {data.kategori} ({periode_bulan_id(data.periode)}); "
                       "hubungan ini bukan sebab-akibat atau ramalan.")
            ev.append(Evidence(label="Korelasi perubahan bulanan", value=data.korelasi, fmt="num"))
            for label, nilai in (("Total return saham", data.total_return_saham),
                                 (f"Perubahan harga {jenis}", data.perubahan_komoditas)):
                if nilai is not None:
                    ev.append(Evidence(label=label, value=nilai, fmt="pct"))
            sumber.extend(data.sources[:2])
        except DataUnavailable:
            alasan += " Data korelasi tidak tersedia; vonis hanya memakai porsi pendapatan."
        return Outcome(
            "modul_aktif", "Klaim menyebut komoditas.",
            card(verdict="menyesatkan" if menyesatkan else "sesuai", check=self.id, rule_id="K-1", claim=claim,
                 headline=h, reason=alasan, evidence=ev, sources=sumber),
        )
