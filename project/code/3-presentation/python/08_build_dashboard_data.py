"""Data kecil untuk dashboard: kondisi, harian, jalur, dan grid simulasi batas NG rate (aturan walk-forward)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "2-analysis" / "python"))
import common as C  # noqa: E402
from rule_lib import load, metrics, run  # noqa: E402

for src, dst in [("conditions.csv", "dash_conditions.csv"), ("daily_summary.csv", "dash_daily.csv"), ("weekly_trend.csv", "dash_weekly.csv"), ("path_test.csv", "dash_path.csv"),
                 ("mode_test.csv", "dash_mode.csv"), ("hypotheses.csv", "dash_hypotheses.csv"), ("ict_to_fct.csv", "dash_cross.csv")]:
    pd.read_csv(C.result(src)).to_csv(C.RES_PRESENT / dst, index=False)
w = load()
FAM = {"IC lot saja": ["ic_lot"], "Tiga lot material": ["ic_lot", "pcb_lot", "conn_lot"], "Semua enam kondisi": C.CONDITIONS}
days = sorted(w.reflow_date.unique())
base_skip = w[(w.path == "Skip") & (w.reflow_date >= days[C.WARMUP_DAYS])].ng.mean()
rows = []
for fam, conds in FAM.items():
    for T in np.round(np.arange(0.01, 0.0801, 0.005), 3):
        rows.append(dict(aturan=fam, batas=float(T), **metrics(run(w, conds, float(T)), w), late_ng_rate_skip_semua=base_skip))
pd.DataFrame(rows).round(8).to_csv(C.RES_PRESENT / "dash_threshold_sim.csv", index=False)
print("dash: grid", len(rows), "baris")
