"""Skenario aturan skip (Q9-Q11), evaluasi walk-forward: keputusan hari D hanya memakai unit di-skip dari hari sebelum D.
Lot baru tanpa bukti cukup (< 30 unit di-skip) dianggap berisiko. Semua dampak berlabel estimated."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
from rule_lib import load, metrics, run  # noqa: E402

w = load()
days = sorted(w.reflow_date.unique())
FAM = {"IC lot saja": ["ic_lot"], "Tiga lot material": ["ic_lot", "pcb_lot", "conn_lot"], "Semua enam kondisi": C.CONDITIONS}
base_skip = w[(w.path == "Skip") & (w.reflow_date >= days[C.WARMUP_DAYS])].ng.mean()
rows = []
for fam, conds in FAM.items():
    for T in C.THRESHOLDS:
        d = run(w, conds, T)
        rows.append(dict(aturan=fam, batas_late_ng=T, **metrics(d, w), late_ng_rate_skip_semua=base_skip))
sc = pd.DataFrame(rows)
sc.to_csv(C.RES_ANALYSIS / "skip_scenarios.csv", index=False)
n_eval = int(sc.unit_dievaluasi.iloc[0])
pd.DataFrame({"ukuran": ["hari_warmup", "hari_dievaluasi", "unit_dievaluasi", "skala_ke_4000_per_bulan"], "nilai": [C.WARMUP_DAYS, len(days) - C.WARMUP_DAYS, n_eval, C.UNITS_PER_MONTH / n_eval]}).to_csv(C.RES_ANALYSIS / "scenario_setup.csv", index=False)
print(sc[["aturan", "batas_late_ng", "unit_aman", "porsi_unit_aman", "late_ng_rate_skip_aman", "ng_rate_ict_aman", "jam_ict_dihemat_per_bulan", "tambahan_late_ng_per_bulan", "net_late_ng_per_bulan"]].round(3).to_string(index=False))
