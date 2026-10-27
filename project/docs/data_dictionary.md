# Kamus data (Project 7)

Semua data adalah simulasi dan sudah dianonimkan (lihat `anonymization_checklist.md` dan `simulation_spec.md`).

| Tabel | Kolom | Keterangan |
|---|---|---|
| units | unit_id (PK), reflow_date, shift, smt_op, smt_line, ic_lot, pcb_lot, conn_lot, fct_available | Satu board setelah SMT Reflow. Kode anonim; tanggal digeser |
| ict | unit_id (PK, FK), test_date, result (OK/NG), fail_net | Satu hasil ICT. Tidak ada baris = unit di-skip. `fail_net` terisi hanya jika NG |
| fct | unit_id (PK, FK), test_date, result (OK/NG), vdrop_max_mv, leak_max_ua, fail_mode (VD/LC), date_flag | Satu hasil FCT. `fail_mode` terisi hanya jika NG; `date_flag` menandai tanggal salah |
| daily_summary | date (PK), units_reflowed, ict_tested, ict_ok_rate, fct_tested, fct_ok_rate, skip_rate | Ringkasan per tanggal (hasil uji dihitung pada tanggal ujinya) |

View: v_unit (riwayat per unit, jalur, late_ng), v_path, v_mode, v_cross, v_cond, v_daily.
