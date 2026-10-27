[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 7: NG Sampling vs ICT

**Status: Selesai di branch `project-7-build` (menunggu review sebelum digabung ke `main`). Data adalah SIMULASI, bukan data pabrik.**

Halaman rancangan dan Report: https://bagusbernadi.github.io/Project-7-NG-Sampling-vs-ICT/

| | |
|---|---|
| Kategori | Manufaktur (PCBA) |
| Tingkat | Mudah |
| Data | Simulasi board 8-layer (data kerja asli tidak tersedia); dianonimkan dengan checklist |
| Tools | SQL (DuckDB), Python (pandas, SciPy), Jupyter, Streamlit + Plotly, GitHub |

## 1. Problem

Untuk kondisi produksi apa ICT board 8-layer aman dilewati, dan berapa waktu uji yang bisa dihemat tanpa menambah NG yang baru ketahuan di FCT? Dipecah menjadi 14 pertanyaan (9 utama); jawabannya ada di tab Report.

## 2. Data

- **Simulasi bersemi**: 7.396 unit, 48 hari, 8 minggu; 3.850 unit di-ICT dan 3.546 di-skip. Spesifikasi dan efek yang ditanam ada di `project/docs/simulation_spec.md`. Dibuat 25 Oktober 2026.
- Data mentah palsu berformat kerja dianonimkan (kode unit acak, Op_01, Lot_A, tanggal digeser); mapping key tidak di-commit. Checklist: 10 dari 10 pemeriksaan lulus.
- Cleaning dicatat di `cleaning_log.csv`: 88 unit tanpa hasil FCT dikeluarkan dari NG rate, baris ICT ganda dan baris FCT tanpa unit dibuang.

## 3. Analysis

- NG rate FCT unit di-skip **4,2%** vs unit lolos ICT **2,0%** (risiko relatif 2,11, uji Fisher p < 0,001).
- NG terkumpul di beberapa kondisi: 2 nilai kondisi berisiko tinggi; lot IC tertinggi Lot_B (12,3%, 422 unit di-skip). Satu lot PCB tampak buruk (8,4%) tetapi turun ke 4,1% tanpa unit dari lot IC terburuk (perancu waktu), jadi pola belum tentu penyebab.
- Aturan skip walk-forward (tiga lot material, batas late NG 3%): 17% unit memenuhi aturan, late NG rate sebenarnya 3,0%, **17,9 jam ICT dihemat per bulan** dengan tambahan 2,1 late NG (estimated, ICT 3 menit per unit, 4.000 unit per bulan).
- Validasi: 14 uji constraint ditolak, 11 pemeriksaan konsistensi, 22 pemeriksaan SQL vs pandas lulus; analisis hanya menemukan 1 dari 6 efek ditanam yang bisa dinilai, jadi efek kecil tidak terdeteksi dengan data sebesar ini.

## 4. Recommendation

Pakai aturan skip hanya untuk lot dengan bukti cukup (minimal 30 unit di-skip) dan late NG rate rendah, tinjau ulang tiap hari, dan perlakukan lot baru sebagai berisiko sampai terkumpul bukti. Ulangi analisis dengan data lini sebenarnya sebelum aturan dipakai.

## 5. Impact

Estimated (simulasi): 17,9 jam ICT dihemat per bulan, tambahan 2,1 late NG, dan 10,1 late NG dihindari bila kapasitas dialihkan ke kondisi berisiko.

## Batasan

- **Data adalah simulasi**; angka tidak menggambarkan lini nyata, hanya mendemonstrasikan metode. Waktu ICT dan volume per bulan adalah asumsi rancangan.
- Pola belum tentu penyebab; lot yang berdekatan waktu saling memengaruhi.
- Efek kecil tidak terdeteksi pada ukuran data ini. Dashboard belum di-deploy.

## Menjalankan

```
pip install -r project/requirements.txt
cd project/code/1-data-preparation/python && python 00_simulate_raw.py && python 01_anonymize_load.py && python 02_build_db.py
cd ../../2-analysis/python && for s in 03 04 05 06 07; do python ${s}_*.py; done
cd ../../3-presentation/python && for s in 08 09 10 11; do python ${s}_*.py; done
streamlit run ../streamlit/app.py
python design-and-report/src/build_report.py   # dari root repo
```

## Struktur repository

```
index.html                 Pengalihan ke design-and-report/
design-and-report/         Halaman Design dan Report (src/ berisi generator)
project/
  code/1-data-preparation  Simulasi data, anonimisasi dan cleaning, database (python, sql)
  code/2-analysis          View SQL, analisis statistik, skenario aturan skip, validasi
  code/3-presentation      Data dashboard, infografis, notebook, README, Streamlit
  results/                 CSV hasil per tahap, infografis, notebook
  docs/                    Definisi, kamus data, checklist anonimisasi, spesifikasi simulasi
  data/                    README, sampel anonim kecil (data mentah, bersih, dan mapping key tidak di-commit)
```
