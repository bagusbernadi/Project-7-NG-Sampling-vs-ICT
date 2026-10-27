"""Menjalankan view SQL dan menyimpan hasilnya sebagai CSV (Q1, Q2, Q3, Q4, Q6)."""
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

C.chdir_root()
con = duckdb.connect(str(C.DB_PATH), read_only=True)
q = lambda sql: con.execute(sql).df()
q("SELECT * FROM daily_summary ORDER BY date").to_csv(C.RES_ANALYSIS / "daily_summary.csv", index=False)
q("SELECT * FROM v_path ORDER BY path").to_csv(C.RES_ANALYSIS / "path_rates.csv", index=False)
q("SELECT * FROM v_mode ORDER BY path, fail_mode").to_csv(C.RES_ANALYSIS / "mode_by_path.csv", index=False)
q("SELECT * FROM v_cross ORDER BY ict_result, fct_result").to_csv(C.RES_ANALYSIS / "cross_ict_fct.csv", index=False)
q("""SELECT cond, val, sum(CASE WHEN path = 'Skip' THEN n ELSE 0 END) AS n_skip, sum(CASE WHEN path = 'Skip' THEN n_ng ELSE 0 END) AS ng_skip,
            sum(CASE WHEN path = 'ICT' THEN n ELSE 0 END) AS n_ict, sum(CASE WHEN path = 'ICT' THEN n_ng ELSE 0 END) AS ng_ict
     FROM v_cond GROUP BY cond, val ORDER BY cond, val""").to_csv(C.RES_ANALYSIS / "conditions_sql.csv", index=False)
print("query CSV ditulis")
con.close()
