"""Aturan skip walk-forward dipakai bersama oleh skenario (06) dan uji sensitivitas (07)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402


def load():
    U, I, F = (pd.read_csv(C.CLEAN_DIR / f"{n}.csv") for n in ("units", "ict", "fct"))
    v = U.merge(I[["unit_id"]].assign(in_ict=True), on="unit_id", how="left").merge(F[["unit_id", "result"]], on="unit_id", how="left")
    v["path"] = np.where(v.in_ict.fillna(False).astype(bool), "ICT", "Skip")
    w = v[v.result.notna()].copy()
    w["ng"] = w.result.eq("NG")
    return w


def run(w, conds, T, min_units=C.MIN_UNITS, warmup=C.WARMUP_DAYS):
    """Unit hasil evaluasi + kolom safe; keputusan hari D hanya memakai unit di-skip dari hari sebelum D."""
    days = sorted(w.reflow_date.unique())
    cnt, out = {}, []
    for i, d in enumerate(days):
        day = w[w.reflow_date == d]
        if i >= warmup:
            ok = np.ones(len(day), bool)
            for c in conds:
                ok &= day[c].map(lambda x, c=c: (lambda t: t[0] >= min_units and t[1] / t[0] <= T)(cnt.get((c, x), (0, 0)))).values
            out.append(day.assign(safe=ok))
        sk = day[day.path == "Skip"]
        for c in C.CONDITIONS:
            for val, t in sk.groupby(c).ng.agg(["size", "sum"]).iterrows():
                a = cnt.setdefault((c, val), [0, 0]); a[0] += int(t["size"]); a[1] += int(t["sum"])
    return pd.concat(out)


def metrics(d, w):
    sc = C.UNITS_PER_MONTH / len(d)                      # skala ke 4.000 unit per bulan (asumsi)
    S, R = d[d.safe], d[~d.safe]
    sk_s, ic_s, sk_r, ic_r = S[S.path == "Skip"], S[S.path == "ICT"], R[R.path == "Skip"], R[R.path == "ICT"]
    r_sk_s, r_ic_s = sk_s.ng.mean() if len(sk_s) else np.nan, ic_s.ng.mean() if len(ic_s) else np.nan
    r_sk_r, r_ic_r = sk_r.ng.mean() if len(sk_r) else np.nan, ic_r.ng.mean() if len(ic_r) else np.nan
    saved = len(ic_s) * sc
    extra = saved * max(0.0, r_sk_s - r_ic_s) if len(ic_s) and len(sk_s) else 0.0
    redirect = min(saved, len(sk_r) * sc)
    avoided = redirect * max(0.0, r_sk_r - r_ic_r) if len(sk_r) and len(ic_r) else 0.0
    return dict(unit_dievaluasi=len(d), unit_aman=int(d.safe.sum()), porsi_unit_aman=d.safe.mean(), skip_aman=len(sk_s), ict_aman=len(ic_s), late_ng_skip_aman=int(sk_s.ng.sum()),
                late_ng_rate_skip_aman=r_sk_s, ng_rate_ict_aman=r_ic_s, late_ng_rate_skip_berisiko=r_sk_r, ng_rate_ict_berisiko=r_ic_r,
                unit_ict_dihemat_per_bulan=saved, jam_ict_dihemat_per_bulan=saved * C.ICT_MIN_PER_UNIT / 60, tambahan_late_ng_per_bulan=extra, unit_dialihkan_per_bulan=redirect,
                late_ng_dihindari_per_bulan=avoided, net_late_ng_per_bulan=avoided - extra)
