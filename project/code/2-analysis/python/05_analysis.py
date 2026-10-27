"""Analisis Q1-Q8: OK rate harian, perbandingan jalur (Fisher), mode NG, kondisi dengan CI, penelusuran sampel NG."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
from stats_lib import n_needed, wilson  # noqa: E402

U, I, F = (pd.read_csv(C.CLEAN_DIR / f"{n}.csv") for n in ("units", "ict", "fct"))
v = U.merge(I[["unit_id", "result"]].rename(columns={"result": "ict_result"}), on="unit_id", how="left").merge(F, on="unit_id", how="left")
v["path"] = np.where(v.ict_result.isna(), "Skip", "ICT")
w = v[v.result.notna()].copy()
w["ng"] = w.result.eq("NG")
rng = np.random.default_rng(C.SEED + 5)

# ---- Q1: OK rate harian dan hubungan antar hari
d = pd.read_csv(C.RES_ANALYSIS / "daily_summary.csv", parse_dates=["date"]).set_index("date")
d = d[d.units_reflowed > 0]
rows = []
for k in range(0, 5):
    a, b = d.ict_ok_rate, d.fct_ok_rate.shift(-k)
    m = a.notna() & b.notna()
    r, p = stats.pearsonr(a[m], b[m])
    rows.append((k, int(m.sum()), r, p))
lag = pd.DataFrame(rows, columns=["lag_hari", "n_hari", "korelasi", "p_value"])
lag.to_csv(C.RES_ANALYSIS / "daily_lag_corr.csv", index=False)
d["minggu"] = ((d.index - d.index.min()).days // 7) + 1
wk = d.groupby("minggu").agg(hari=("units_reflowed", "size"), unit=("units_reflowed", "sum"), ict_ok_rate=("ict_ok_rate", "mean"), fct_ok_rate=("fct_ok_rate", "mean"), skip_rate=("skip_rate", "mean")).reset_index()
wk.to_csv(C.RES_ANALYSIS / "weekly_trend.csv", index=False)
day_sd = pd.DataFrame({"ukuran": ["ict_ok_rate_rata2", "ict_ok_rate_sd", "fct_ok_rate_rata2", "fct_ok_rate_sd", "hari", "unit_per_hari_rata2"],
                       "nilai": [d.ict_ok_rate.mean(), d.ict_ok_rate.std(), d.fct_ok_rate.mean(), d.fct_ok_rate.std(), len(d), d.units_reflowed.mean()]})
day_sd.to_csv(C.RES_ANALYSIS / "daily_stats.csv", index=False)

# ---- Q2: Fisher, unit di-skip vs lolos ICT
g = w.groupby("path").ng.agg(["size", "sum"])
tab = [[int(g.loc["Skip", "sum"]), int(g.loc["Skip", "size"] - g.loc["Skip", "sum"])], [int(g.loc["ICT", "sum"]), int(g.loc["ICT", "size"] - g.loc["ICT", "sum"])]]
orr, pf = stats.fisher_exact(tab)
rr = (tab[0][0] / g.loc["Skip", "size"]) / (tab[1][0] / g.loc["ICT", "size"])
ci = {p: wilson(int(g.loc[p, "sum"]), int(g.loc[p, "size"])) for p in ("Skip", "ICT")}
pd.DataFrame([dict(jalur=p, n=int(g.loc[p, "size"]), ng=int(g.loc[p, "sum"]), ng_rate=g.loc[p, "sum"] / g.loc[p, "size"], ci_low=ci[p][0], ci_high=ci[p][1]) for p in ("ICT", "Skip")]
             ).assign(odds_ratio=orr, relative_risk=rr, p_fisher=pf).to_csv(C.RES_ANALYSIS / "path_test.csv", index=False)

# ---- Q3: mode NG
mo = w[w.ng].groupby(["path", "fail_mode"]).size().unstack(fill_value=0)
tm = [[int(mo.loc["Skip", "VD"]), int(mo.loc["Skip", "LC"])], [int(mo.loc["ICT", "VD"]), int(mo.loc["ICT", "LC"])]]
om, pm = stats.fisher_exact(tm)
pd.DataFrame([dict(jalur=p, ng=int(mo.loc[p].sum()), vd=int(mo.loc[p, "VD"]), lc=int(mo.loc[p, "LC"]), porsi_vd=mo.loc[p, "VD"] / mo.loc[p].sum()) for p in ("ICT", "Skip")]
             ).assign(p_fisher=pm, odds_ratio=om).to_csv(C.RES_ANALYSIS / "mode_test.csv", index=False)
meas = w[w.ng].groupby("fail_mode")[["vdrop_max_mv", "leak_max_ua"]].median().reset_index()
meas.to_csv(C.RES_ANALYSIS / "mode_measurements.csv", index=False)

# ---- Q4/Q5: kondisi dengan CI (hanya unit di-skip) dan uji Fisher nilai vs sisanya
rows = []
sk = w[w.path == "Skip"]
for cond in C.CONDITIONS:
    for val, t in sk.groupby(cond):
        n, k = len(t), int(t.ng.sum())
        rest = sk[sk[cond] != val]
        _, p = stats.fisher_exact([[k, n - k], [int(rest.ng.sum()), len(rest) - int(rest.ng.sum())]])
        lo, hi = wilson(k, n)
        ti = w[(w.path == "ICT") & (w[cond] == val)]
        rows.append(dict(kondisi=cond, nilai=val, n_skip=n, ng_skip=k, ng_rate_skip=k / n, ci_low=lo, ci_high=hi, cukup_unit=n >= C.MIN_UNITS, p_vs_sisanya=p,
                         n_ict=len(ti), ng_ict=int(ti.ng.sum()), ng_rate_ict=ti.ng.mean() if len(ti) else np.nan))
cd = pd.DataFrame(rows)
cd["p_bonferroni"] = (cd.p_vs_sisanya * len(cd)).clip(upper=1)
cd.to_csv(C.RES_ANALYSIS / "conditions.csv", index=False)
nn = pd.DataFrame([dict(ng_rate=p, margin=m, unit_dibutuhkan=n_needed(p, m)) for p in (0.02, 0.03, 0.04, 0.05) for m in (0.02, 0.01)])
nn.to_csv(C.RES_ANALYSIS / "n_needed.csv", index=False)

# ---- Q6: unit NG di ICT, hasilnya di FCT
ix = w[w.path == "ICT"].groupby(["ict_result", "result"]).size().unstack(fill_value=0)
ix["n"] = ix.sum(axis=1); ix["porsi_fct_ng"] = ix["NG"] / ix["n"]
ix.reset_index().to_csv(C.RES_ANALYSIS / "ict_to_fct.csv", index=False)
ict_ng_all, ict_ng_fct = I[I.result == "NG"].unit_id, w[(w.path == "ICT") & (w.ict_result == "NG")]

# ---- Q7: telusur sampel unit NG FCT
ng = w[w.ng]
t7 = pd.DataFrame([("unit NG FCT", len(ng)), ("tidak pernah di-ICT (di-skip)", int((ng.path == "Skip").sum())), ("pernah di-ICT", int((ng.path == "ICT").sum())),
                   ("pernah di-ICT dan OK di ICT (lolos ICT, NG di FCT)", int(((ng.path == "ICT") & (ng.ict_result == "OK")).sum())), ("pernah di-ICT dan NG di ICT (NG di FCT setelah diperbaiki)", int(((ng.path == "ICT") & (ng.ict_result == "NG")).sum()))],
                  columns=["ukuran", "unit"])
t7["porsi"] = t7.unit / len(ng)
t7.to_csv(C.RES_ANALYSIS / "ng_trace.csv", index=False)

# ---- Q8: komposisi sampel NG vs seluruh produksi
rows = []
for cond in C.CONDITIONS:
    ct = pd.crosstab(w[cond], w.ng)
    chi, p, _, _ = stats.chi2_contingency(ct)
    share_all, share_ng = w[cond].value_counts(normalize=True), ng[cond].value_counts(normalize=True).reindex(w[cond].unique()).fillna(0)
    rows.append(dict(kondisi=cond, nilai_beda=len(ct), chi2=chi, p_value=p, selisih_porsi_maks=float((share_ng - share_all.reindex(share_ng.index)).abs().max())))
pd.DataFrame(rows).to_csv(C.RES_ANALYSIS / "ng_sample_vs_all.csv", index=False)
N = 60                                                                    # sampel NG seukuran contoh rancangan
true_best = cd[(cd.kondisi == "ic_lot") & cd.cukup_unit].sort_values("ng_rate_skip").iloc[-1].nilai
hit_cnt = hit_rate = 0
draws = 2000
all_ic = w[w.ng].ic_lot
for _ in range(draws):
    s = all_ic.sample(N, random_state=int(rng.integers(1e9)))
    if s.value_counts().idxmax() == true_best:
        hit_cnt += 1
vol = w.ic_lot.value_counts()
pd.DataFrame([dict(ukuran_sampel=N, undian=draws, lot_ic_ng_rate_tertinggi=true_best, porsi_undian_lot_terbanyak_benar=hit_cnt / draws, lot_ic_volume_terbesar=vol.idxmax(),
                   porsi_undian_lot_terbanyak_sama_volume=float(np.mean([all_ic.sample(N, random_state=int(rng.integers(1e9))).value_counts().idxmax() == vol.idxmax() for _ in range(500)])))]
             ).to_csv(C.RES_ANALYSIS / "ng_sample_draws.csv", index=False)
print(f"skip {tab[0][0]}/{g.loc['Skip','size']} vs ICT {tab[1][0]}/{g.loc['ICT','size']} p={pf:.2g} RR={rr:.2f}; lag0 r={lag.korelasi[0]:.2f}; kondisi {len(cd)}")
print(cd[["kondisi", "nilai", "n_skip", "ng_rate_skip", "ci_low", "ci_high", "p_bonferroni"]].round(3).to_string(index=False))
print(pd.read_csv(C.RES_ANALYSIS / "ng_sample_draws.csv").round(3).T); print(lag.round(3)); print(pd.read_csv(C.RES_ANALYSIS / "ng_sample_vs_all.csv").round(3))
