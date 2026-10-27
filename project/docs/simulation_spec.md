# Spesifikasi simulasi (Project 7)

Data kerja asli tidak tersedia, jadi seluruh data adalah **simulasi bersemi** (`00_simulate_raw.py`, seed di `code/common.py`). Semua nama, nomor seri, dan pelanggan pada data mentah adalah karangan.

- Periode 8 minggu (Senin sampai Sabtu), rata-rata 154 unit per hari (setara ±4.000 unit per bulan), board 8-layer.
- Lot IC, PCB, dan konektor berganti per blok hari (3 sampai 10 hari). Operator terikat shift; lini dua.
- Peluang cacat SMT dasar 1,2%, dikalikan risiko relatif per kondisi: lot IC tertentu 6,0 (dan satu lot uji coba kecil 6,0), lot IC lain 2,2 (tidak muncul pada seed ini), lot PCB 2,0, lot konektor 1,3, satu operator 2,2, lini 2 1,3, shift malam 1,2.
- Skip karena kapasitas: peluang 30% (shift 1), 45% (shift 2), 70% (shift 3).
- ICT menangkap 85% cacat; 1,2% unit baik NG di ICT; cacat yang lolos berujung NG di FCT 90%; 8% unit NG-ICT masih NG di FCT; NG FCT latar 0,8%.
- Mode NG: voltage drop 60% pada cacat SMT, 30% pada latar.
- Pengotor untuk Q13: baris ICT ganda, unit tanpa hasil FCT (1,2%), tanggal FCT sebelum reflow, baris FCT yatim.
- Kebenaran simulasi (`truth_hidden.csv`) hanya dipakai pada `07_validate.py` untuk memeriksa apakah analisis menemukan efek yang ditanam.

Konsekuensi: angka NG rate, kondisi berisiko, dan dampak menggambarkan simulasi, bukan lini produksi nyata. Yang dibuktikan project ini adalah metodenya.
