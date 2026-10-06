# Kamus data — bahan_produk/

Snapshot data per **30 Sep 2026**. Dibuat ulang dengan `python skrip/buat_bahan_produk.py` (0 kredit).
Aturan umum: angka persen/porsi disimpan sebagai **desimal** (0,25 = 25%). Rupiah dalam Rp penuh, dolar dalam US$ penuh.
Di aplikasi, setiap angka dari data luar wajib menampilkan **sumber + tanggal**.

## Dari Sectors (sumber inti)

### `segmen_pendapatan.csv` — "saham X itu sebenarnya jualan apa?"
| Kolom | Arti |
|---|---|
| symbol | Kode saham |
| tahun_buku | Tahun laporan keuangan (kebanyakan 2024; ITMG 2025) |
| segmen | Nama sumber pendapatan menurut laporan emiten (bahasa asli) |
| pendapatan_idr | Pendapatan segmen itu, Rp |
| porsi | Bagian dari total pendapatan (0–1) |
Sumber: `/v2/company/get-segments/`. Emiten: ANTM, ADRO, AADI, AMMN, BUMI, BYAN, DSSA, GEMS, INCO, ITMG, MBMA, MDKA, NCKL, ADMR.

### `rating_analis.csv`
| Kolom | Arti |
|---|---|
| buy / hold / sell / strong_buy / strong_sell | Jumlah rekomendasi analis per jenis |
| jumlah_rekomendasi | Total (kolom API `n_analyst`; bisa berisi beberapa rekomendasi per analis → sebut "rekomendasi") |
| diperbarui | Tanggal data rating |
| tahun_proyeksi | Tahun yang diproyeksikan |
| proyeksi_pertumbuhan_eps | Perkiraan perubahan laba per saham vs tahun sebelumnya (−0,46 = turun 46%) |
| proyeksi_pertumbuhan_pendapatan | Perkiraan perubahan pendapatan |
Sumber: company report section `future`.

### `komposisi_pemegang_saham.csv` — siapa yang pegang saham
| Kolom | Arti |
|---|---|
| tanggal | Akhir bulan |
| jumlah_pemegang | Jumlah pemegang saham (baru terisi mulai Sep 2025) |
| perubahan_pemegang | Selisih dengan bulan sebelumnya |
| jumlah_saham | Total saham beredar |
| porsi_ritel_lokal | Porsi saham milik investor perorangan dalam negeri |
| porsi_reksadana_lokal | Porsi milik reksa dana dalam negeri |
| porsi_lokal / porsi_asing | Total porsi investor dalam negeri / luar negeri |
| porsi_ritel_asing | Porsi milik perorangan asing |
| cakupan | porsi_lokal + porsi_asing. **Berbeda per emiten** (PTBA ~0,34; ADRO, MGLV ~1,0) → bandingkan tren dalam satu emiten, jangan antar-emiten |
Sumber: `/v2/company/shareholders-composition/`. Emiten: BBRI, PTBA, BREN (2026), ADRO, MDKA (2025–26), ANTM (2023–26), BUMI (2021–26), MGLV (2024–26).

### `dividen_payout_yield.csv`
| Kolom | Arti |
|---|---|
| yield_ttm | Dividen 12 bulan terakhir ÷ harga saham |
| payout_ratio | Dividen ÷ laba. > 1 = dividen lebih besar dari laba |
| kapitalisasi_pasar | Harga × jumlah saham (Rp); kosong untuk daftar payout |
| daftar | `payout>100%` (31 emiten) atau `yield tertinggi` (100 teratas) |
Sumber: screener `/v2/companies/`.

### `kalender_aksi_korporasi.csv` — 30 Sep s.d. 28 Des 2026
| Kolom | Arti |
|---|---|
| jenis | upcoming_dividend, right_issue, stock_split, bonus, warrant |
| tanggal | Tanggal ex (hari pertama saham diperdagangkan tanpa hak tersebut) |
| detail_json | Rincian asli (harga, rasio, tanggal cum/recording/payment) |
Sumber: `/v2/corporate-actions/`.

### `radar_free_float.csv` — emiten free float < 15%
| Kolom | Arti |
|---|---|
| free_float | Porsi saham di tangan publik (entri "Public" Sectors; definisi BEI bisa sedikit beda) |
| market_cap | Kapitalisasi pasar, Rp |
| tenggat / target_pertama / tanggal_tenggat | Kelompok tenggat aturan BEI (Peraturan I-A, SE-00004/BEI/03-2026) |
| nilai_perlu_dilepas_idr | (target − free float) × kapitalisasi pasar |
| rata2_nilai_transaksi_60h | Rata-rata nilai transaksi harian 60 hari bursa terakhir |
| hari_serap | nilai_perlu_dilepas ÷ rata-rata transaksi harian → perkiraan kasar, label "Dihitung" |
Hari serap hanya dihitung untuk emiten bertenggat 2027.

### `emiten_tambang_per_komoditas.csv`
Daftar emiten Tbk per komoditas menurut data tambang Sectors (nikel, emas, tembaga, aluminium, perak, seng-timbal).

### `saham_vs_komoditas.csv` — hubungan harga saham dengan harga komoditas (hasil analisis kita)
| Kolom | Arti |
|---|---|
| komoditas | Seri World Bank (Coal Australian = Newcastle; Coal South African = Richards Bay) |
| periode, n_bulan | Rentang & jumlah bulan yang dipakai |
| korelasi_bulanan | Korelasi perubahan bulanan (−1 s.d. 1); saham = total return (dividen & split disesuaikan), dirata-rata per bulan |
| kategori | < 0,3 lemah; 0,3–0,6 sedang; ≥ 0,6 cukup kuat (ambang kasar signifikan ±0,30) |
| korelasi_kuartalan | Sama, per kuartal (n kecil, hanya pembanding) |
| total_return_saham | Perubahan total (termasuk dividen) Jan 2023 → akhir periode |
| perubahan_komoditas | Perubahan harga komoditas di periode yang sama |
| arah_tahunan | Per tahun: searah atau BERLAWANAN |
Dihitung oleh `skrip/cek_harga_dunia.py`. Korelasi ≠ sebab-akibat dan bukan dasar prediksi.

## Data luar (pelengkap, wajib tampil dengan sumber)

### `harga_komoditas_dunia_bulanan.csv`
Harga rata-rata bulanan Jan 2023 – Agu 2026: Coal Australian, Coal South African, Nickel, Copper, Tin, Aluminum ($/mt); Gold, Silver ($/troy oz). Sumber: World Bank Pink Sheet (CC BY), diperbarui 2 Sep 2026.

### `ekspor_bulanan_bps.csv`
| Kolom | Arti |
|---|---|
| grup | batubara (HS 2701 + lignit 2702), nikel (7202.60, 7501, 7502), tembaga (2603, 7403), emas (7108.12), timah (8001) |
| nilai_usd, berat_kg | Total ekspor per bulan |
| harga_satuan_usd_per_ton | nilai ÷ berat |
Sumber: BPS WebAPI `dataexim`, s.d. Jul 2026. Catatan: ekspor batu bara di Sectors = HS 2701 saja (tanpa lignit) → angka grup batubara di sini lebih besar. **Grup emas tidak cocok dengan Sectors dan angka 2026 janggal → jangan ditampilkan.**

### `kurs_idr_per_usd_bulanan.csv`
Rata-rata bulanan rupiah per USD, Des 2022 – Agu 2026. Sumber: FRED `CCUSMA02IDM618N` (OECD).

### `papan_pemantauan_khusus.csv` + `papan_pemantauan_kriteria.csv`
Daftar emiten yang pernah/sedang di Papan Pemantauan Khusus BEI (unduh manual 30 Sep 2026) dan arti tiap kriteria.
| Kolom | Arti |
|---|---|
| tanggal_masuk / tanggal_keluar | Kosong = masih di papan |
| aktif | ya / tidak |
| kriteria | Nomor kriteria (bisa lebih dari satu, dipisah koma) |
| durasi_hari | Lama di papan (sampai 30 Sep 2026 kalau masih aktif) |
File BEI hanya berisi **satu baris per emiten** (kemungkinan episode terakhir). Kriteria 1, 6, 7, 10 dihapus mulai 28 Sep 2026; arti lamanya ada di file kriteria.
