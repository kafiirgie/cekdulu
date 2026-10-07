"""Susun data/fixtures/<TICKER>/<kunci>.json dari cache lab data (0 kredit).  [Lane B, tugas B0]

Jalankan dari folder backend/:
    python scripts/buat_fixture.py                    # 6 saham demo + BBRI/BREN/PTBA
    python scripts/buat_fixture.py MGLV MDKA          # saham tertentu
    python scripts/buat_fixture.py --live MGLV        # isi yang kosong dari Sectors (memakai kredit!)

Sumber cache default: data/cache (ubah dengan --sumber).
Cache lab lama di repo sebelah tetap dipakai jika tersedia.
Fixture yang sudah ada dipertahankan; hanya kunci kosong yang disusun/ditarik.
Kunci = nama file fixture = kunci di app/data/sectors.py ENDPOINTS.
Hasil: tabel "ada / kosong" per saham per kunci. Kunci kosong → status data_kurang di app,
atau tarik dengan --live (cek sisa kredit dulu, lihat FINAL_PLAN §7.3).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402

DEMO = ["MGLV", "MDKA", "ANTM", "BUMI", "PSAB", "BBRI", "BREN", "PTBA"]

# kunci → pola nama file di cache (urut prioritas). {t} = ticker.
# "gabung": True = file list harian digabung & di-dedup per tanggal.
POLA: dict[str, dict] = {
    "report":             {"pola": ["awal/{t}_report.json", "cache/eks_report_{t}.json"]},
    "report_keuangan":    {"pola": []},  # Tambahan valuation/dividend, dipilih lewat --kunci.
    "keuangan_kuartalan": {"pola": ["awal/{t}_quarterly.json"]},
    "harga_harian":       {"pola": ["awal/{t}_daily_90d.json", "cache/daily90_{t}.json", "cache/eks_daily_{t}_*.json",
                                    "cache/daily_{t}_*.json"], "gabung": True},
    "aliran_asing":       {"pola": ["awal/{t}_foreignflow_90d.json"]},
    "filings":            {"pola": ["cache/eks_filings_{t}.json", "cache/filings_{t}*.json", "awal/{t}_filings_90d.json"]},
    "suspensi":           {"pola": ["cache/eks_susp_{t}.json", "awal/{t}_suspensions.json"]},
    "aksi_korporasi":     {"pola": ["cache/corpact_{t}.json", "awal/{t}_corpact.json"]},
    "segmen":             {"pola": ["cache/eks_segments_{t}.json"]},
    "komposisi_pemegang": {"pola": ["cache/eks_shcomp_{t}_*.json", "awal/{t}_shareholders_comp.json"], "gabung_tahun": True},
    "report_future":      {"pola": ["cache/eks_future_{t}.json"]},
}


def _baca(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def kumpulkan(sumber: Path, t: str, kunci: str):
    langsung = sumber / t / f"{kunci}.json"
    if langsung.exists():
        return _baca(langsung)
    spec = POLA[kunci]
    files: list[Path] = []
    for pola in spec["pola"]:
        files += sorted(sumber.glob(pola.format(t=t)))
    if not files:
        return None
    if spec.get("gabung"):
        per_tanggal = {}
        for f in files:
            d = _baca(f)
            for row in d if isinstance(d, list) else d.get("data", []):
                per_tanggal[row["date"]] = row
        return [per_tanggal[k] for k in sorted(per_tanggal)]
    if spec.get("gabung_tahun"):
        semua = {}
        for f in files:
            d = _baca(f)
            for row in d.get("data", []):
                semua[row["date"]] = row
        return {"symbol": f"{t}.JK", "data": [semua[k] for k in sorted(semua)]}
    return _baca(files[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tickers", nargs="*", default=DEMO)
    sumber_lama = settings.fixtures_dir.parents[2] / "cekdulu-datacheck" / "data_mentah" / "sectors"
    ap.add_argument("--sumber", default=str(settings.cache_dir if settings.cache_dir.is_dir() or not sumber_lama.is_dir() else sumber_lama))
    ap.add_argument("--kunci", nargs="+", choices=POLA, default=[k for k in POLA if k != "report_keuangan"], help="batasi kunci fixture yang disusun/ditarik")
    ap.add_argument("--live", action="store_true", help="tarik kunci yang kosong dari Sectors (memakai kredit)")
    a = ap.parse_args()
    sumber = Path(a.sumber)
    if not sumber.is_dir():
        print(f"Folder cache tidak ditemukan: {sumber}\nPakai --sumber <path ke data_mentah/sectors> atau salin cache ke data/cache.")

    kosong = 0
    print(f"{'ticker':7}" + "".join(f"{k[:10]:>12}" for k in a.kunci))
    for t in [x.upper() for x in a.tickers]:
        out = settings.fixtures_dir / t
        out.mkdir(parents=True, exist_ok=True)
        baris = f"{t:7}"
        for kunci in a.kunci:
            tujuan = out / f"{kunci}.json"
            if tujuan.exists():
                baris += f"{'ada':>12}"
                continue
            data = kumpulkan(sumber, t, kunci)
            if data is None and a.live:
                from app.data import sectors
                try:
                    data = sectors._call_live(t, kunci)
                    cache = settings.cache_dir / t / f"{kunci}.json"
                    cache.parent.mkdir(parents=True, exist_ok=True)
                    cache.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
                except Exception as e:  # noqa: BLE001
                    print(f"  {t} {kunci}: {e}")
            if data is not None:
                tujuan.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            else:
                kosong += 1
            baris += f"{'ada' if data is not None else '-':>12}"
        print(baris)
    if a.live:
        from app.data import sectors
        print(f"\nKredit live terpakai: {sectors.credits_used()}")
    if kosong:
        sys.exit(f"{kosong} kunci fixture masih kosong; data tidak diganti dengan angka contoh.")


if __name__ == "__main__":
    main()
