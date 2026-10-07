"""Bungkus fixture menjadi secret file base64 untuk Render; output tidak boleh di-commit."""
from __future__ import annotations

import argparse
import base64
import io
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data" / "fixtures"
DEFAULT_OUTPUT = ROOT / "deploy" / "fixtures.zip.b64"
BATAS_RENDER = 1_000_000


def buat_arsip() -> bytes:
    berkas = sorted(p for p in FIXTURES.rglob("*.json") if p.is_file())
    if not berkas:
        raise SystemExit("Fixture JSON tidak ditemukan di data/fixtures/.")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as arsip:
        for path in berkas:
            arsip.write(path, path.relative_to(FIXTURES))
    return base64.b64encode(buffer.getvalue())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    isi = buat_arsip()
    if len(isi) > BATAS_RENDER:
        raise SystemExit(f"Secret {len(isi):,} byte melebihi batas Render {BATAS_RENDER:,} byte.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(isi)
    print(f"Tulis {len(isi):,} byte ke {args.output}")
    print("Buat Render Secret File bernama fixtures.zip.b64, lalu tempel isi file ini.")


if __name__ == "__main__":
    main()
