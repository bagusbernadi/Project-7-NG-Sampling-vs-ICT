"""Membangun ict.duckdb dari data anonim bersih, menguji constraint, dan memeriksa konsistensi antar tabel."""
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

C.chdir_root()
if C.DB_PATH.exists():
    C.DB_PATH.unlink()
con = duckdb.connect(str(C.DB_PATH))
con.execute((C.SQL_PREP / "01_schema.sql").read_text())
con.execute((C.SQL_PREP / "02_load.sql").read_text())
con.execute((C.SQL_ANALYSIS / "03_views.sql").read_text())
con.execute("INSERT INTO daily_summary SELECT * FROM v_daily")

NEWU = "INSERT INTO units VALUES ('U-9100', '2026-01-01', 'Shift_1', 'Op_01', 'Line_1', 'Lot_A', 'Lot_B', 'Lot_C', TRUE)"   # unit sah untuk uji FK; dibatalkan (rollback)
tests = [("unit tanpa kode anonim (nomor seri asli)", "", "INSERT INTO units VALUES ('SN2412345678', '2026-01-01', 'Shift_1', 'Op_01', 'Line_1', 'Lot_A', 'Lot_B', 'Lot_C', TRUE)"),
         ("unit_id ganda", "", "INSERT INTO units SELECT * FROM units LIMIT 1"),
         ("operator bukan kode anonim", "", "INSERT INTO units VALUES ('U-9001', '2026-01-01', 'Shift_1', 'Budi', 'Line_1', 'Lot_A', 'Lot_B', 'Lot_C', TRUE)"),
         ("shift tidak dikenal", "", "INSERT INTO units VALUES ('U-9002', '2026-01-01', 'Pagi', 'Op_01', 'Line_1', 'Lot_A', 'Lot_B', 'Lot_C', TRUE)"),
         ("hasil ICT untuk unit yang tidak ada", "", "INSERT INTO ict VALUES ('U-9003', '2026-01-01', 'OK', NULL)"),
         ("hasil ICT bukan OK atau NG", NEWU, "INSERT INTO ict VALUES ('U-9100', '2026-01-01', 'Skip', NULL)"),
         ("ICT NG tanpa fail_net", NEWU, "INSERT INTO ict VALUES ('U-9100', '2026-01-01', 'NG', NULL)"),
         ("hasil ICT ganda untuk satu unit", "", "INSERT INTO ict SELECT * FROM ict LIMIT 1"),
         ("hasil FCT ganda untuk satu unit", "", "INSERT INTO fct SELECT * FROM fct LIMIT 1"),
         ("FCT NG tanpa mode NG", NEWU, "INSERT INTO fct VALUES ('U-9100', '2026-01-01', 'NG', 50, 5, NULL, 'ok')"),
         ("mode NG tidak dikenal", NEWU, "INSERT INTO fct VALUES ('U-9100', '2026-01-01', 'NG', 50, 5, 'XX', 'ok')"),
         ("tegangan drop negatif", NEWU, "INSERT INTO fct VALUES ('U-9100', '2026-01-01', 'OK', -1, 5, NULL, 'ok')"),
         ("skip_rate di luar 0 sampai 1", "", "INSERT INTO daily_summary VALUES ('2030-01-01', 1, 1, 1, 1, 1, 1.5)"),
         ("tanggal ganda di daily_summary", "", "INSERT INTO daily_summary SELECT * FROM daily_summary LIMIT 1")]
rows = []
for name, setup, sql in tests:
    con.execute("BEGIN")
    try:
        if setup:
            con.execute(setup)
        con.execute(sql)
        rows.append((name, "DITERIMA"))
    except Exception:
        rows.append((name, "ditolak"))
    finally:
        con.execute("ROLLBACK")
pd.DataFrame(rows, columns=["test", "outcome"]).to_csv(C.RES_PREP / "constraint_tests.csv", index=False)
assert all(o == "ditolak" for _, o in rows), rows

n_u = con.execute("SELECT count(*) FROM units").fetchone()[0]
checks = {
    "setiap hasil ICT punya unit": "SELECT count(*) FROM ict LEFT JOIN units USING (unit_id) WHERE units.unit_id IS NULL",
    "setiap hasil FCT punya unit": "SELECT count(*) FROM fct LEFT JOIN units USING (unit_id) WHERE units.unit_id IS NULL",
    "fct_available cocok dengan keberadaan baris FCT": "SELECT count(*) FROM units u LEFT JOIN fct f USING (unit_id) WHERE u.fct_available <> (f.unit_id IS NOT NULL)",
    "jalur Skip + ICT = jumlah unit": f"SELECT abs((SELECT count(*) FROM v_unit) - {n_u})",
    "v_unit satu baris per unit": "SELECT count(*) - count(DISTINCT unit_id) FROM v_unit",
    "jumlah unit v_path = unit dengan hasil FCT": "SELECT abs((SELECT sum(n_fct) FROM v_path) - (SELECT count(*) FROM fct))",
    "NG per kondisi = NG per jalur (tiap kondisi)": "SELECT count(*) FROM (SELECT cond, sum(n_ng) AS g FROM v_cond GROUP BY cond) WHERE g <> (SELECT sum(n_ng) FROM v_path)",
    "late NG hanya pada unit di-skip": "SELECT count(*) FROM v_unit WHERE late_ng AND path <> 'Skip'",
    "ICT harian = total baris ICT": "SELECT abs((SELECT sum(ict_tested) FROM daily_summary) - (SELECT count(*) FROM ict))",
    "FCT harian = baris FCT tanpa date_flag": "SELECT abs((SELECT sum(fct_tested) FROM daily_summary) - (SELECT count(*) FROM fct WHERE date_flag = 'ok'))",
    "unit SMT Reflow harian = jumlah unit": f"SELECT abs((SELECT sum(units_reflowed) FROM daily_summary) - {n_u})",
}
res = [(k, round(float(con.execute(q).fetchone()[0]), 6)) for k, q in checks.items()]
pd.DataFrame(res, columns=["pemeriksaan", "violations"]).to_csv(C.RES_PREP / "consistency_checks.csv", index=False)
assert all(v < 1e-6 for _, v in res), res
rowsn = [(t, con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]) for t in ("units", "ict", "fct", "daily_summary")]
pd.DataFrame(rowsn, columns=["tabel", "baris"]).to_csv(C.RES_PREP / "table_rows.csv", index=False)
print(rowsn, f"constraint {len(rows)}/{len(rows)} ditolak,", len(res), "pemeriksaan konsistensi 0 pelanggaran")
con.close()
