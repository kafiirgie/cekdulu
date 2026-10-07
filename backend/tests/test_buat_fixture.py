"""Penyiapan fixture tidak menimpa data atau memakai kredit tanpa --live."""
import json
import sys
from dataclasses import replace

import pytest

from app.config import settings
from app.data import sectors
from scripts import buat_fixture


@pytest.fixture
def lokasi(monkeypatch, tmp_path):
    konfigurasi = replace(settings, fixtures_dir=tmp_path / "fixtures", cache_dir=tmp_path / "cache")
    monkeypatch.setattr(buat_fixture, "settings", konfigurasi)
    monkeypatch.setattr(sectors, "_call_live", lambda *args: pytest.fail("Tes tidak boleh memanggil Sectors"))
    return konfigurasi


def test_cache_api_dipakai_fixture_lama_dipertahankan(lokasi, monkeypatch):
    cache = lokasi.cache_dir / "MGLV"
    cache.mkdir(parents=True)
    (cache / "report.json").write_text('{"company_name": "Dari cache"}', encoding="utf-8")
    (cache / "suspensi.json").write_text('{"results": []}', encoding="utf-8")
    fixture = lokasi.fixtures_dir / "MGLV"
    fixture.mkdir(parents=True)
    lama = '{"company_name": "Fixture asli"}'
    (fixture / "report.json").write_text(lama, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["buat_fixture.py", "MGLV", "--kunci", "report", "suspensi"])
    buat_fixture.main()
    assert (fixture / "report.json").read_text(encoding="utf-8") == lama
    assert json.loads((fixture / "suspensi.json").read_text(encoding="utf-8")) == {"results": []}
    assert not (fixture / "harga_harian.json").exists()


def test_cache_lab_harga_digabung_dan_diurutkan(lokasi):
    cache = lokasi.cache_dir / "cache"
    cache.mkdir(parents=True)
    (cache / "eks_daily_MGLV_1.json").write_text(json.dumps([
        {"date": "2026-09-30", "close": 14650}, {"date": "2026-01-02", "close": 600}]), encoding="utf-8")
    (cache / "eks_daily_MGLV_2.json").write_text(json.dumps({"data": [
        {"date": "2026-09-30", "close": 14650}]}), encoding="utf-8")
    harga = buat_fixture.kumpulkan(lokasi.cache_dir, "MGLV", "harga_harian")
    assert [h["close"] for h in harga] == [600, 14650]


def test_tanpa_cache_tetap_laporkan_kunci_kosong(lokasi, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["buat_fixture.py", "MGLV", "--sumber", str(lokasi.cache_dir), "--kunci", "report"])
    with pytest.raises(SystemExit, match="1 kunci fixture masih kosong"):
        buat_fixture.main()
    assert "MGLV" in capsys.readouterr().out
    assert not (lokasi.fixtures_dir / "MGLV" / "report.json").exists()


def test_report_memakai_bagian_sah_dan_batas_kredit(monkeypatch):
    import httpx
    konfigurasi = replace(settings, sectors_api_key="kunci-uji", sectors_credit_budget=2)
    monkeypatch.setattr(sectors, "settings", konfigurasi)
    monkeypatch.setattr(sectors, "_credits_used", 0)
    calls = []

    def http_palsu(url, *, params, headers, timeout):
        calls.append(params)
        return httpx.Response(200, json={"company_name": "Emiten uji"}, request=httpx.Request("GET", url))

    monkeypatch.setattr(sectors.httpx, "get", http_palsu)
    assert sectors._call_live("MGLV", "report")["company_name"] == "Emiten uji"
    assert calls == [{"sections": "overview,ownership"}]
    assert sectors.credits_used() == 2
    with pytest.raises(sectors.DataUnavailable, match="Batas kredit"):
        sectors._call_live("MGLV", "report")
    assert len(calls) == 1
