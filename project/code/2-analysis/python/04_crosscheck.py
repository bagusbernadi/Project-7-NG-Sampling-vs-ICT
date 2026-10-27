"""Cek silang: angka KPI dari SQL (view) vs hitungan pandas pada data bersih (pengganti PivotTable Excel, Q14)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

U, I, F = (pd.read_csv(C.CLEAN_DIR / f"{n}.csv") for n in ("units", "ict", "fct"))
v = U.merge(I[["unit_id", "test_date", "result"]].rename(columns={"test_date": "ict_date", "result": "ict_result"}), on="unit_id", how="left").merge(F, on="unit_id", how="left")
v["path"] = np.where(v.ict_result.isna(), "Skip", "ICT")
v["ng"] = v.result.eq("NG")
w = v[v.result.notna()]
sql = lambda n: pd.read_csv(C.RES_ANALYSIS / n)
out = []


def chk(name, a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    assert a.shape == b.shape, (name, a.shape, b.shape)
    out.append((name, a.size, float(np.nanmax(np.abs(a - b))) if a.size else 0.0))


p = sql("path_rates.csv").set_index("path")
g = w.groupby("path").agg(n=("ng", "size"), ng=("ng", "sum"), rate=("ng", "mean"))
chk("NG rate FCT per jalur", p.loc[["ICT", "Skip"], "ng_rate"], g.loc[["ICT", "Skip"], "rate"])
chk("jumlah unit dan NG per jalur", p.loc[["ICT", "Skip"], ["n_fct", "n_ng"]].values.ravel(), g.loc[["ICT", "Skip"], ["n", "ng"]].values.ravel())
c = sql("conditions_sql.csv")
for cond, t in c.groupby("cond"):
    col = {"smt_op": "smt_op", "shift": "shift"}.get(cond, cond)
    s = w[w.path == "Skip"].groupby(col).ng.agg(["size", "sum"]); i2 = w[w.path == "ICT"].groupby(col).ng.agg(["size", "sum"])
    t = t.set_index("val")
    chk(f"kondisi {cond}: n dan NG, Skip", t[["n_skip", "ng_skip"]].values.ravel(), s.reindex(t.index).fillna(0).values.ravel())
    chk(f"kondisi {cond}: n dan NG, ICT", t[["n_ict", "ng_ict"]].values.ravel(), i2.reindex(t.index).fillna(0).values.ravel())
m = sql("mode_by_path.csv").set_index(["path", "fail_mode"]).n
mm = w[w.ng].groupby(["path", "fail_mode"]).size()
chk("mode NG per jalur", m.sort_index(), mm.sort_index())
x = sql("cross_ict_fct.csv").set_index(["ict_result", "fct_result"]).n
xx = w[w.path == "ICT"].groupby(["ict_result", "result"]).size()
chk("tabel silang ICT x FCT", x.sort_index(), xx.sort_index())
d = sql("daily_summary.csv").set_index("date")
rd = U.groupby("reflow_date").size()
chk("unit SMT Reflow per hari", d.units_reflowed, rd.reindex(d.index).fillna(0))
ict_d = I.groupby("test_date").size(); chk("hasil ICT per hari", d.ict_tested, ict_d.reindex(d.index).fillna(0))
okf = F[F.date_flag == "ok"].groupby("test_date").result.agg(["size", lambda s: (s == "OK").mean()])
chk("hasil FCT per hari", d.fct_tested, okf["size"].reindex(d.index).fillna(0))
chk("FCT OK rate per hari", d.fct_ok_rate.dropna(), okf.iloc[:, 1].reindex(d.fct_ok_rate.dropna().index))
okI = I.groupby("test_date").result.apply(lambda s: (s == "OK").mean())
chk("ICT OK rate per hari", d.ict_ok_rate.dropna(), okI.reindex(d.ict_ok_rate.dropna().index))
sk = v.groupby("reflow_date").path.apply(lambda s: (s == "Skip").mean())
chk("skip rate per hari", d.skip_rate, sk.reindex(d.index))
df = pd.DataFrame(out, columns=["pemeriksaan", "jumlah_nilai", "selisih_maks"])
df["status"] = np.where(df.selisih_maks < 1e-9, "PASS", "GAGAL")
df.to_csv(C.RES_ANALYSIS / "crosscheck_pandas.csv", index=False)
assert (df.status == "PASS").all(), df[df.status != "PASS"]
print(len(df), "pemeriksaan,", int(df.jumlah_nilai.sum()), "nilai, semua PASS")
