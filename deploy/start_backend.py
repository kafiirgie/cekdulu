"""Siapkan fixture rahasia, lalu jalankan satu proses Uvicorn di Render."""
from __future__ import annotations

import base64
import io
import os
import zipfile
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data" / "fixtures"
SECRET_DEFAULT = Path("/etc/secrets/fixtures.zip.b64")


def _ada_fixture() -> bool:
    return any(FIXTURES.rglob("*.json"))


def _lokasi_secret() -> Path | None:
    dari_env = os.getenv("CEKDULU_FIXTURES_B64_FILE")
    kandidat = [Path(dari_env)] if dari_env else []
    kandidat.extend([SECRET_DEFAULT, ROOT / "fixtures.zip.b64"])
    return next((path for path in kandidat if path.is_file()), None)


def _ekstrak_fixture(secret: Path) -> None:
    try:
        zip_bytes = base64.b64decode(secret.read_bytes(), validate=True)
    except ValueError as exc:
        raise SystemExit("Secret fixtures.zip.b64 bukan base64 yang valid.") from exc

    FIXTURES.mkdir(parents=True, exist_ok=True)
    tujuan = FIXTURES.resolve()
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as arsip:
        for anggota in arsip.infolist():
            target = (FIXTURES / anggota.filename).resolve()
            if not target.is_relative_to(tujuan):
                raise SystemExit(f"Path fixture tidak aman: {anggota.filename}")
        arsip.extractall(FIXTURES)


def main() -> None:
    load_dotenv(ROOT / ".env")
    mode = os.getenv("CEKDULU_DATA_MODE", "fixture").lower()
    if mode == "fixture" and not _ada_fixture():
        secret = _lokasi_secret()
        if secret is None:
            raise SystemExit(
                "Mode fixture memerlukan data/fixtures atau Render Secret File fixtures.zip.b64."
            )
        _ekstrak_fixture(secret)
    if mode == "fixture" and not _ada_fixture():
        raise SystemExit("Secret fixture berhasil dibaca tetapi tidak berisi JSON.")

    port = os.getenv("PORT", "8000")
    os.execvp("uvicorn", [
        "uvicorn", "app.main:app", "--app-dir", str(ROOT / "backend"),
        "--host", "0.0.0.0", "--port", port,
    ])


if __name__ == "__main__":
    main()
