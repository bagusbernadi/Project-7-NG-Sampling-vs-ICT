"""Validasi temuan: pemulihan efek yang ditanam di simulasi, sensitivitas jumlah minimum unit, pemindaian kebocoran identitas, verdict hipotesis."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
from rule_lib import load, metrics, run  # noqa: E402

R = lambda n: pd.read_csv(C.RES_ANALYSIS / n)
cd, pt, md, lag, nd = R("conditions.csv"), R("path_test.csv").set_index("jalur"), R("mode_test.csv").set_index("jalur"), R("daily_lag_corr.csv"), R("ng_sample_draws.csv").iloc[0]
cmp_ = R("ng_sample_vs_all.csv").set_index("kondisi")
sc = R("skip_scenarios.csv")

# ---- 1. pemulihan efek yang ditanam (butuh data mentah + mapping key lokal; hasilnya di-commit sebagai CSV)
key = pd.read_csv(C.MAPPING_KEY)
code = {(r.jenis, r.nilai_asli): r.kode for r in key.itertuples()}
RR = C.RR                                                                          # parameter yang ditanam (ground truth)
cmap = {"ic_lot": "lot", "pcb_lot": "lot", "conn_lot": "lot", "smt_op": "operator", "smt_line": "line", "shift": "shift"}
shift_raw = {"Night": "Shift_3", "Day": "Shift_1", "Evening": "Shift_2"}
planted = {}
for cond, d in RR.items():
    for val, rr in d.items():
        k = shift_raw[val] if cond == "shift" else code.get((cmap[cond], val))
        if k is not None:                                                            # lot yang tidak pernah dipakai di periode ini tidak ada di data
            planted[(cond, k)] = rr
base = float(pt.loc['Skip', 'ng_rate'])
rows = []
for r in cd.itertuples():
    rr = planted.get((r.kondisi, r.nilai), 1.0)
    flagged = (r.p_bonferroni < 0.05) and (r.ng_rate_skip > base) and r.cukup_unit
    rows.append(dict(kondisi=r.kondisi, nilai=r.nilai, risiko_relatif_ditanam=rr, n_skip=r.n_skip, ng_rate_skip=r.ng_rate_skip, ditandai_berisiko=flagged, cukup_unit=r.cukup_unit))
tr = pd.DataFrame(rows)
tr["hasil"] = np.select([(tr.risiko_relatif_ditanam > 1) & tr.ditandai_berisiko, (tr.risiko_relatif_ditanam > 1) & ~tr.cukup_unit, (tr.risiko_relatif_ditanam > 1), tr.ditandai_berisiko],
                        ["terdeteksi", "tidak dinilai (unit < 30)", "terlewat", "positif palsu"], "benar tidak ditandai")
tr.to_csv(C.RES_ANALYSIS / "truth_recovery.csv", index=False)


# ---- 1b. cek perancu: lot yang ditandai berisiko tetapi tidak ditanam, dihitung ulang tanpa unit dari lot IC terburuk
w0 = load()
sk0 = w0[w0.path == "Skip"]
worst = tr[(tr.hasil == "terdeteksi") & (tr.kondisi == "ic_lot")].nilai.tolist()
rows = []
for r in tr[tr.ditandai_berisiko].itertuples():
    t = sk0[sk0[r.kondisi] == r.nilai]
    t2 = t[~t.ic_lot.isin(worst)] if r.kondisi != "ic_lot" else t
    overlap = t.ic_lot.isin(worst).mean()
    rows.append(dict(kondisi=r.kondisi, nilai=r.nilai, risiko_relatif_ditanam=r.risiko_relatif_ditanam, ng_rate_semua=t.ng.mean(), n=len(t), porsi_unit_lot_ic_terburuk=overlap,
                     ng_rate_tanpa_lot_ic_terburuk=t2.ng.mean(), n_tanpa=len(t2)))
pd.DataFrame(rows).to_csv(C.RES_ANALYSIS / "confounding_check.csv", index=False)

# ---- 2. sensitivitas jumlah minimum unit pada aturan tiga lot, batas 3 persen
w = load()
rows = []
for mu in (10, 30, 60, 100):
    d = run(w, ["ic_lot", "pcb_lot", "conn_lot"], 0.03, min_units=mu)
    rows.append(dict(min_unit=mu, **metrics(d, w)))
pd.DataFrame(rows).to_csv(C.RES_ANALYSIS / "min_units_sensitivity.csv", index=False)

# ---- 3. pindai kebocoran identitas di semua file yang akan di-commit
raw_vals = [str(v) for v in key.nilai_asli if len(str(v)) >= 3]
raw = {c: pd.read_csv(C.RAW_DIR / f"raw_{n}.csv") for c, n in (("u", "units"), ("i", "ict"), ("f", "fct"))}
raw_vals += list(raw["u"].serial_no) + [raw["u"].customer[0], raw["u"].board_model[0], raw["u"].station_ict[0], raw["u"].station_fct[0]]
files = [p for d in (C.RES_PREP, C.RES_ANALYSIS, C.DOCS_DIR, C.SAMPLE_DIR, C.CODE.parent / "data") for p in d.rglob("*") if p.is_file() and p.suffix in (".csv", ".md", ".py", ".sql", ".txt")
         and p.name not in ("mapping_key.csv",) and "raw" not in p.parts and "clean" not in p.parts]
nm = 0
for p in files:
    t = p.read_text(encoding="utf-8", errors="ignore")
    nm += sum(1 for v in set(raw_vals) if v in t)
pd.DataFrame([dict(file_dipindai=len(files), nilai_asli_dicari=len(set(raw_vals)), kecocokan=nm)]).to_csv(C.RES_ANALYSIS / "leak_scan.csv", index=False)
assert nm == 0, nm

# ---- 4. verdict hipotesis
sig = cd[(cd.p_bonferroni < 0.05) & (cd.cukup_unit) & (cd.ng_rate_skip > base)]
low = cd[(cd.cukup_unit) & (cd.ng_rate_skip <= 0.03)]
h3 = sc[(sc.aturan == "Tiga lot material") & (sc.batas_late_ng == 0.03)].iloc[0]
l0 = lag.set_index("lag_hari")
hyp = pd.DataFrame([
    ("H1", "Unit yang di-skip lebih sering NG di FCT daripada unit yang lolos ICT", "Terbukti", f"NG rate {pt.loc['Skip', 'ng_rate']:.1%} (di-skip) vs {pt.loc['ICT', 'ng_rate']:.1%} (di-ICT), risiko relatif {pt.loc['Skip', 'relative_risk']:.2f}, p Fisher {pt.loc['Skip', 'p_fisher']:.1e}"),
    ("H2", "NG FCT terkumpul di beberapa lot IC atau lot PCB tertentu", "Terbukti", f"{len(sig)} nilai kondisi berisiko tinggi (p Bonferroni < 0,05); lot IC tertinggi {nd.lot_ic_ng_rate_tertinggi}"),
    ("H3", "Ada kondisi produksi dengan NG rate rendah yang aman di-skip", "Sebagian", f"{len(low)} nilai kondisi dengan NG rate <= 3% dan n >= 30; pada evaluasi walk-forward rate sebenarnya {h3.late_ng_rate_skip_aman:.1%} (batas 3%) dengan {h3.jam_ict_dihemat_per_bulan:.1f} jam ICT dihemat per bulan (estimated)"),
    ("H4", "OK rate harian ICT tidak bisa dipakai menebak OK rate FCT di hari yang sama", "Sebagian", f"korelasi hari sama r = {l0.loc[0, 'korelasi']:.2f} (p {l0.loc[0, 'p_value']:.2f}); jeda 1 hari r = {l0.loc[1, 'korelasi']:.2f} (p {l0.loc[1, 'p_value']:.3f})"),
    ("H5", "Sampel unit NG saja tidak cukup; data unit OK dibutuhkan sebagai pembanding", "Sebagian", f"komposisi sampel NG berbeda dari produksi (chi-kuadrat p < 0,05 pada {(cmp_.p_value < 0.05).sum()} dari {len(cmp_)} kondisi); sampel 60 NG menemukan lot IC terburuk pada {nd.porsi_undian_lot_terbanyak_benar:.0%} undian, tetapi tanpa unit OK tidak ada NG rate dan kondisi aman"),
], columns=["id", "hipotesis", "verdict", "bukti"])
hyp.to_csv(C.RES_ANALYSIS / "hypotheses.csv", index=False)
print(tr.hasil.value_counts().to_string()); print(pd.read_csv(C.RES_ANALYSIS / "confounding_check.csv").round(3).to_string(index=False)); print(hyp[["id", "verdict", "bukti"]].to_string(index=False)); print(pd.read_csv(C.RES_ANALYSIS / "min_units_sensitivity.csv")[["min_unit", "unit_aman", "late_ng_rate_skip_aman", "jam_ict_dihemat_per_bulan", "net_late_ng_per_bulan"]].round(3).to_string(index=False))
