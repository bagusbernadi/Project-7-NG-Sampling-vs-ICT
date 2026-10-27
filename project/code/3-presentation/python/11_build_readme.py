"""Membuat README.md di root repo; semua angka dibaca dari CSV hasil."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import ACCESS_DATE, ICT_MIN_PER_UNIT, MIN_UNITS, ROOT, UNITS_PER_MONTH, result  # noqa: E402

R = lambda n: pd.read_csv(result(n))
f = lambda v, d=1: f"{v:.{d}f}".replace(".", ",")
pc = lambda v, d=1: f(v * 100, d) + "%"
n = lambda v: f"{int(round(float(v))):,}".replace(",", ".")
dq = R("data_quality.csv").set_index("ukuran").nilai
pt, hyp, cc, ct, cs_ = R("path_test.csv").set_index("jalur"), R("hypotheses.csv"), R("crosscheck_pandas.csv"), R("constraint_tests.csv"), R("consistency_checks.csv")
sc = R("skip_scenarios.csv")
h = sc[(sc.aturan == "Tiga lot material") & (sc.batas_late_ng == 0.03)].iloc[0]
cd, ck, tr = R("conditions.csv"), R("anonymization_checklist.csv"), R("truth_recovery.csv")
sig = cd[(cd.p_bonferroni < 0.05) & cd.cukup_unit & (cd.ng_rate_skip > pt.loc["Skip", "ng_rate"])]
conf = R("confounding_check.csv"); conf = conf[conf.kondisi != "ic_lot"].iloc[0]
assert pt.loc["Skip", "p_fisher"] < 0.001
worst = cd[(cd.kondisi == "ic_lot") & cd.cukup_unit].sort_values("ng_rate_skip").iloc[-1]

md = f"""[← Back to portfolio](https://bagusbernadi.github.io/)

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

- **Simulasi bersemi**: {n(dq["unit_setelah_cleaning"])} unit, {n(dq["hari_produksi"])} hari, 8 minggu; {n(dq["unit_di_ict"])} unit di-ICT dan {n(dq["unit_di_skip"])} di-skip. Spesifikasi dan efek yang ditanam ada di `project/docs/simulation_spec.md`. Dibuat {ACCESS_DATE}.
- Data mentah palsu berformat kerja dianonimkan (kode unit acak, Op_01, Lot_A, tanggal digeser); mapping key tidak di-commit. Checklist: {n(ck.lulus.sum())} dari {n(len(ck))} pemeriksaan lulus.
- Cleaning dicatat di `cleaning_log.csv`: {n(dq["unit_tanpa_fct"])} unit tanpa hasil FCT dikeluarkan dari NG rate, baris ICT ganda dan baris FCT tanpa unit dibuang.

## 3. Analysis

- NG rate FCT unit di-skip **{pc(pt.loc["Skip", "ng_rate"])}** vs unit lolos ICT **{pc(pt.loc["ICT", "ng_rate"])}** (risiko relatif {f(pt.loc["Skip", "relative_risk"], 2)}, uji Fisher p < 0,001).
- NG terkumpul di beberapa kondisi: {n(len(sig))} nilai kondisi berisiko tinggi; lot IC tertinggi {worst.nilai} ({pc(worst.ng_rate_skip)}, {n(worst.n_skip)} unit di-skip). Satu lot PCB tampak buruk ({pc(conf.ng_rate_semua)}) tetapi turun ke {pc(conf.ng_rate_tanpa_lot_ic_terburuk)} tanpa unit dari lot IC terburuk (perancu waktu), jadi pola belum tentu penyebab.
- Aturan skip walk-forward (tiga lot material, batas late NG 3%): {pc(h.porsi_unit_aman, 0)} unit memenuhi aturan, late NG rate sebenarnya {pc(h.late_ng_rate_skip_aman)}, **{f(h.jam_ict_dihemat_per_bulan, 1)} jam ICT dihemat per bulan** dengan tambahan {f(h.tambahan_late_ng_per_bulan, 1)} late NG (estimated, ICT {f(ICT_MIN_PER_UNIT, 0)} menit per unit, {n(UNITS_PER_MONTH)} unit per bulan).
- Validasi: {n(len(ct))} uji constraint ditolak, {n(len(cs_))} pemeriksaan konsistensi, {n(len(cc))} pemeriksaan SQL vs pandas lulus; analisis hanya menemukan {n((tr.hasil == "terdeteksi").sum())} dari {n(((tr.risiko_relatif_ditanam > 1) & tr.cukup_unit).sum())} efek ditanam yang bisa dinilai, jadi efek kecil tidak terdeteksi dengan data sebesar ini.

## 4. Recommendation

Pakai aturan skip hanya untuk lot dengan bukti cukup (minimal {MIN_UNITS} unit di-skip) dan late NG rate rendah, tinjau ulang tiap hari, dan perlakukan lot baru sebagai berisiko sampai terkumpul bukti. Ulangi analisis dengan data lini sebenarnya sebelum aturan dipakai.

## 5. Impact

Estimated (simulasi): {f(h.jam_ict_dihemat_per_bulan, 1)} jam ICT dihemat per bulan, tambahan {f(h.tambahan_late_ng_per_bulan, 1)} late NG, dan {f(h.late_ng_dihindari_per_bulan, 1)} late NG dihindari bila kapasitas dialihkan ke kondisi berisiko.

## Batasan

- **Data adalah simulasi**; angka tidak menggambarkan lini nyata, hanya mendemonstrasikan metode. Waktu ICT dan volume per bulan adalah asumsi rancangan.
- Pola belum tentu penyebab; lot yang berdekatan waktu saling memengaruhi.
- Efek kecil tidak terdeteksi pada ukuran data ini. Dashboard belum di-deploy.

## Menjalankan

```
pip install -r project/requirements.txt
cd project/code/1-data-preparation/python && python 00_simulate_raw.py && python 01_anonymize_load.py && python 02_build_db.py
cd ../../2-analysis/python && for s in 03 04 05 06 07; do python ${{s}}_*.py; done
cd ../../3-presentation/python && for s in 08 09 10 11; do python ${{s}}_*.py; done
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
"""
(ROOT.parent / "README.md").write_text(md, encoding="utf-8")
print("README.md ditulis")
