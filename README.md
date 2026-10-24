[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 7: NG Sampling vs ICT

**Status: Design (rancangan).**

**Tujuan:** Membangun analisis dan dashboard yang membandingkan hasil FCT unit PCBA board 8-layer yang melewati ICT dengan unit yang langsung di-skip, untuk menemukan kondisi produksi yang aman dilewati ICT, sehingga kapasitas ICT yang terbatas dapat difokuskan pada unit yang paling berisiko.

| | |
|---|---|
| Kategori | Manufaktur (PCBA) |
| Tingkat | Mudah |
| Data | Data produksi yang dianonimkan: sampling NG, hasil ICT dan FCT (PCBA board 8-layer) |
| Tools | DuckDB + SQL, Python (pandas, SciPy), Excel (opsional), Streamlit + Plotly |

## 1. Problem
Untuk kondisi produksi apa ICT board 8-layer aman dilewati, dan berapa waktu uji yang bisa dihemat tanpa menambah NG yang baru ketahuan di FCT?

## 2. Data
Data kerja yang dianonimkan: nomor seri menjadi kode acak, operator menjadi Op_01 dan seterusnya, lot menjadi Lot_A dan seterusnya, tanggal digeser, nama perusahaan dan pelanggan dihapus, serta nama produk, stasiun, dan parameter uji disamarkan dengan padanan umum PCBA. Mapping key disimpan terpisah dan tidak pernah diunggah. Data mentah tidak disimpan di repo.

## 3. Analysis
Rencana: OK rate harian ICT dan FCT, NG rate FCT unit yang lolos ICT vs di-skip (uji Fisher), NG rate per kondisi dengan confidence interval, skenario aturan skip (jam ICT dihemat vs tambahan late NG). Belum dikerjakan.

## 4. Recommendation
Belum dikerjakan.

## 5. Impact
Belum dikerjakan. Angka dampak akan diberi label `estimated` / `simulated`.

## Batasan yang sudah diketahui
- Sampel unit NG kecil; hasil dibaca sebagai indikasi.
- Pola belum tentu penyebab; penyebab dicek di lapangan.
- Unit masuk FCT di hari berbeda dari ICT, sehingga perbandingan dilakukan per unit.
- Izin perusahaan untuk data kerja dipastikan sebelum dipublikasikan.

## Struktur repository (rencana)
```
docs/            # definisi KPI, kamus data, checklist anonimisasi
data/sample/     # contoh data anonim kecil
scripts/         # anonimisasi, cleaning, pemuat data
sql/             # query dan view KPI
notebooks/       # analisis
dashboard/       # aplikasi Streamlit
index.html       # halaman rancangan (GitHub Pages)
README.md
```
