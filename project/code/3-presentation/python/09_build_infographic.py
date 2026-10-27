"""Infografis satu halaman (PNG + PDF) dari CSV hasil."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

R = lambda n: pd.read_csv(C.result(n))
pt, cd, sc = R("path_test.csv").set_index("jalur"), R("conditions.csv"), R("skip_scenarios.csv")
h = sc[(sc.aturan == "Tiga lot material") & (sc.batas_late_ng == 0.03)].iloc[0]
ic = cd[cd.kondisi == "ic_lot"].sort_values("ng_rate_skip")
fig = plt.figure(figsize=(11.7, 8.3)); fig.suptitle("Project 7: NG Sampling vs ICT (data simulasi)", fontsize=18, fontweight="bold", x=0.05, ha="left")
t = fig.add_axes([0.05, 0.80, 0.9, 0.1]); t.axis("off")
for i, (lb, v) in enumerate([("NG FCT unit di-skip", f"{pt.loc['Skip', 'ng_rate']:.1%}"), ("NG FCT unit lolos ICT", f"{pt.loc['ICT', 'ng_rate']:.1%}"), ("Jam ICT dihemat/bulan (estimated)", f"{h.jam_ict_dihemat_per_bulan:.0f} jam"), ("Tambahan late NG/bulan (estimated)", f"{h.tambahan_late_ng_per_bulan:.0f} unit")]):
    t.text(i * 0.25, 0.55, v, fontsize=18, fontweight="bold", color="#174EA6"); t.text(i * 0.25, 0.1, lb, fontsize=10.5, color="#5f6368")
a1 = fig.add_axes([0.07, 0.42, 0.38, 0.30])
a1.bar(["Lolos ICT", "Di-skip"], [pt.loc["ICT", "ng_rate"], pt.loc["Skip", "ng_rate"]], color=["#1a73e8", "#e37400"],
       yerr=[[pt.loc["ICT", "ng_rate"] - pt.loc["ICT", "ci_low"], pt.loc["Skip", "ng_rate"] - pt.loc["Skip", "ci_low"]], [pt.loc["ICT", "ci_high"] - pt.loc["ICT", "ng_rate"], pt.loc["Skip", "ci_high"] - pt.loc["Skip", "ng_rate"]]], capsize=4)
a1.set_title("NG rate FCT per jalur (CI 95%)", fontsize=11, loc="left"); a1.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
a2 = fig.add_axes([0.57, 0.42, 0.38, 0.30])
a2.barh(ic.nilai, ic.ng_rate_skip, color=["#9aa0a6" if n < C.MIN_UNITS else ("#d93025" if r > 0.08 else "#1a73e8") for n, r in zip(ic.n_skip, ic.ng_rate_skip)],
        xerr=[ic.ng_rate_skip - ic.ci_low, ic.ci_high - ic.ng_rate_skip], capsize=2)
a2.set_title("Late NG rate per lot IC (abu-abu: unit < 30)", fontsize=11, loc="left"); a2.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
a3 = fig.add_axes([0.07, 0.08, 0.40, 0.24])
g = sc[sc.aturan == "Tiga lot material"]
a3.plot(g.batas_late_ng * 100, g.jam_ict_dihemat_per_bulan, marker="o", color="#1a73e8", label="Jam ICT dihemat")
a3.plot(g.batas_late_ng * 100, g.tambahan_late_ng_per_bulan, marker="s", color="#e37400", label="Tambahan late NG (unit)")
a3.set_xlabel("batas late NG rate (%)"); a3.set_title("Skenario aturan skip, tiga lot material (estimated)", fontsize=11, loc="left"); a3.legend(frameon=False, fontsize=9)
n = fig.add_axes([0.57, 0.08, 0.38, 0.24]); n.axis("off")
n.text(0, 0.95, "Temuan", fontweight="bold", fontsize=12)
n.text(0, 0.75, "Unit di-skip dua kali lebih sering NG di FCT.\nNG terkumpul di beberapa lot; satu lot IC jauh di atas yang lain.\nBeberapa lot aman di-skip (NG rendah, unit >= 30).\nLot yang berdekatan waktu bisa saling memengaruhi.\nSemua angka dari simulasi; waktu ICT 3 menit dan 4.000\nunit per bulan adalah asumsi.", fontsize=10.5, va="top", linespacing=1.6)
for a in (a1, a2, a3):
    a.spines[["top", "right"]].set_visible(False)
fig.savefig(C.RES_PRESENT / "infographic.png", dpi=150); fig.savefig(C.RES_PRESENT / "infographic.pdf")
print("infografis ditulis")
