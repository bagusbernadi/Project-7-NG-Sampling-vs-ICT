# Checklist anonimisasi (Project 7)

Kolom yang diganti pada `01_anonymize_load.py` (mapping key disimpan di `project/data/mapping_key.csv`, tidak pernah di-commit):

| Kolom asal | Pengganti | Catatan |
|---|---|---|
| Nomor seri | U-0001 dan seterusnya, urutan acak | Kode unik, tidak bisa ditebak dari urutan |
| Operator | Op_01 dan seterusnya | Urutan acak |
| Lot IC, PCB, konektor | Lot_A dan seterusnya | Satu rangkaian huruf untuk semua jenis lot |
| Lini SMT, shift | Line_n, Shift_n | Nama mesin dan nama shift dihapus |
| Nama net ICT | NET_nn | |
| Pelanggan, model produk, nama stasiun | dihapus | Kolom tidak dibawa ke data bersih |
| Tanggal | digeser dengan selisih tetap | Selisih bagian dari kunci, tidak dipakai analisis |

Pemeriksaan otomatis (hasil di `results/1-data-preparation/anonymization_checklist.csv` dan `results/2-analysis/leak_scan.csv`): tabel bersih memakai format kode yang benar, nilai asli tidak muncul di data bersih, sampel, hasil, dan dokumen; mapping key dan data mentah diabaikan Git.
