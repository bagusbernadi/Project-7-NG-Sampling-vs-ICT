# Definisi (Project 7)

| Istilah | Definisi |
|---|---|
| Unit | Satu board 8-layer setelah SMT Reflow; kunci `unit_id` (kode anonim U-0001 dan seterusnya) |
| Jalur ICT / Skip | ICT = unit punya baris hasil ICT; Skip = unit tidak punya baris ICT (dilewati karena kapasitas) |
| ICT OK rate | unit OK di ICT ÷ unit yang diuji ICT (per hari uji) |
| FCT OK rate | unit OK di FCT ÷ unit yang diuji FCT (per hari uji; baris bertanda tanggal salah dikeluarkan) |
| Skip rate | unit di-skip ÷ unit SMT Reflow pada hari yang sama |
| NG rate FCT (per jalur) | unit NG di FCT ÷ unit dengan hasil FCT, pada jalur itu |
| Late NG | unit di-skip yang NG di FCT; masalah baru ketahuan setelah unit melewati proses lanjutan |
| Mode NG | VD = voltage drop, LC = leakage current |
| Kondisi | lot IC, lot PCB, lot konektor, operator SMT, lini SMT, shift |
| Jumlah unit minimum | 30 unit di-skip per nilai kondisi; kurang dari itu tidak dijadikan dasar aturan skip |
| Interval kepercayaan | Wilson 95% untuk proporsi |
| Aturan skip (walk-forward) | Unit boleh di-skip jika semua kondisi yang dipakai aturan punya late NG rate historis (unit di-skip pada hari sebelumnya) di bawah batas dan n ≥ 30. Hari awal (6 hari) hanya mengumpulkan bukti; lot baru tanpa bukti cukup dianggap berisiko |
| Jam ICT dihemat (estimated) | unit yang sekarang di-ICT tetapi berada di kondisi aman × menit ICT per unit ÷ 60, diskalakan ke 4.000 unit per bulan |
| Tambahan late NG (estimated) | unit ICT di kondisi aman × selisih NG rate (di-skip − lolos ICT), tidak kurang dari 0 |
| Late NG dihindari (estimated) | kapasitas yang dibebaskan dialihkan ke unit di-skip di kondisi berisiko × selisih NG rate (di-skip − lolos ICT) di kondisi itu |
| Asumsi | ICT 3 menit per unit dan 4.000 unit per bulan adalah angka contoh rancangan, bukan data kerja |
