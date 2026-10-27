# Data (Project 7)

Data kerja asli tidak tersedia. Seluruh data adalah **simulasi bersemi** yang dibuat ulang oleh `code/1-data-preparation/python/00_simulate_raw.py` (lihat `docs/simulation_spec.md`).

| Item | Keterangan |
|---|---|
| Sumber | Simulasi (versi sim-1, dibuat 25 Oktober 2026); bukan dataset publik |
| Data mentah | `data/raw/` berisi file palsu berformat kerja dengan identitas karangan; tidak di-commit |
| Mapping key | `data/mapping_key.csv` dibuat saat anonimisasi; tidak pernah di-commit |
| Data bersih | `data/clean/` (anonim); tidak di-commit, dibuat ulang |
| Sampel | `data/sample/` berisi 300 unit anonim (units, ict, fct) yang di-commit sebagai contoh bentuk data |
| Lisensi | Tidak berlaku (data buatan sendiri) |

Menjalankan ulang: `python 00_simulate_raw.py` lalu `python 01_anonymize_load.py` (lihat README di root repositori).
