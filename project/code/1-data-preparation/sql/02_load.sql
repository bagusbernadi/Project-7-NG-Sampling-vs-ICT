-- Memuat data anonim bersih (dijalankan dari folder project/ oleh 02_build_db.py).
INSERT INTO units SELECT unit_id, reflow_date, shift, smt_op, smt_line, ic_lot, pcb_lot, conn_lot, fct_available FROM read_csv('data/clean/units.csv', header = true);
INSERT INTO ict SELECT unit_id, test_date, result, fail_net FROM read_csv('data/clean/ict.csv', header = true);
INSERT INTO fct SELECT unit_id, test_date, result, vdrop_max_mv, leak_max_ua, fail_mode, date_flag FROM read_csv('data/clean/fct.csv', header = true);
