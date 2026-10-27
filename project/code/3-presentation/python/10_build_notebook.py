"""Membuat dan menjalankan results/3-presentation/analysis.ipynb (Q1-Q14). Notebook hanya membaca CSV hasil."""
import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

nb = nbf.v4.new_notebook()
M = lambda t: nb.cells.append(nbf.v4.new_markdown_cell(t))
K = lambda t: nb.cells.append(nbf.v4.new_code_cell(t.strip()))
M("# Project 7: NG Sampling vs ICT\nNotebook membaca CSV hasil (`results/`), tidak menghitung ulang. Urutan mengikuti 14 pertanyaan pada Design Project.\n\n"
  "**Data adalah SIMULASI** (data kerja asli tidak tersedia). Waktu ICT 3 menit per unit dan volume 4.000 unit per bulan adalah asumsi.")
K("""
import pandas as pd, matplotlib.pyplot as plt
pd.set_option("display.width", 170); pd.set_option("display.max_columns", 30)
R1, R2 = "../1-data-preparation/", "../2-analysis/"
rd = lambda p: pd.read_csv(p)
""")
S = [("Q1. OK rate harian ICT dan FCT, tren, dan hubungan antar hari", """
d = rd(R2+"daily_summary.csv"); d = d[d.fct_tested > 0]
d.plot(x="date", y=["ict_ok_rate", "fct_ok_rate"], figsize=(10, 3)); plt.show()
print(rd(R2+"weekly_trend.csv").round(3).to_string(index=False)); print(rd(R2+"daily_lag_corr.csv").round(3).to_string(index=False))"""),
("Q2. NG rate FCT: unit lolos ICT vs unit di-skip (uji Fisher)", "print(rd(R2+'path_test.csv').round(4).T.to_string(header=False))"),
("Q3. Mode NG per jalur", "print(rd(R2+'mode_test.csv').round(3).to_string(index=False)); print(rd(R2+'mode_measurements.csv').round(1).to_string(index=False))"),
("Q4. Kondisi dengan NG rate rendah saat di-skip", "c = rd(R2+'conditions.csv'); print(c[['kondisi','nilai','n_skip','ng_skip','ng_rate_skip','ci_low','ci_high','cukup_unit','p_bonferroni','n_ict','ng_rate_ict']].round(3).to_string(index=False))"),
("Q5. Jumlah unit minimum agar kesimpulan bisa dipercaya", "print(rd(R2+'n_needed.csv').to_string(index=False)); print(rd(R2+'min_units_sensitivity.csv')[['min_unit','unit_aman','late_ng_rate_skip_aman','jam_ict_dihemat_per_bulan','net_late_ng_per_bulan']].round(3).to_string(index=False))"),
("Q6. Unit NG di ICT: hasilnya di FCT", "print(rd(R2+'ict_to_fct.csv').round(3).to_string(index=False))"),
("Q7. Penelusuran sampel unit NG FCT", "print(rd(R2+'ng_trace.csv').round(3).to_string(index=False))"),
("Q8. Sampel NG saja vs seluruh produksi", "print(rd(R2+'ng_sample_vs_all.csv').round(3).to_string(index=False)); print(rd(R2+'ng_sample_draws.csv').round(3).T.to_string(header=False))"),
("Q9-Q11. Skenario aturan skip (estimated, walk-forward)", "s = rd(R2+'skip_scenarios.csv'); print(s[['aturan','batas_late_ng','porsi_unit_aman','late_ng_rate_skip_aman','ng_rate_ict_aman','jam_ict_dihemat_per_bulan','tambahan_late_ng_per_bulan','unit_dialihkan_per_bulan','late_ng_dihindari_per_bulan','net_late_ng_per_bulan']].round(3).to_string(index=False))"),
("Q12. Checklist anonimisasi", "print(rd(R1+'anonymization_checklist.csv')[['pemeriksaan','lulus','detail']].to_string(index=False)); print(rd(R2+'leak_scan.csv').to_string(index=False))"),
("Q13. Kualitas data dan pencocokan unit", "print(rd(R1+'cleaning_log.csv')[['kode','masalah','baris','keputusan']].to_string(index=False)); print(rd(R1+'constraint_tests.csv').outcome.value_counts().to_string())"),
("Q14. Cek silang SQL vs pandas", "c = rd(R2+'crosscheck_pandas.csv'); print(c.status.value_counts().to_string()); print(c.to_string(index=False))"),
("Validasi simulasi dan hipotesis", "print(rd(R2+'truth_recovery.csv').hasil.value_counts().to_string()); print(rd(R2+'confounding_check.csv').round(3).to_string(index=False)); print(rd(R2+'hypotheses.csv').to_string(index=False))")]
for t, c in S:
    M("## " + t); K(c)
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(C.RES_PRESENT)}}).execute()
errs = [o for c in nb.cells if c.cell_type == "code" for o in c.outputs if o.output_type == "error"]
assert not errs, errs
nbf.write(nb, C.RES_PRESENT / "analysis.ipynb")
print("notebook:", len(nb.cells), "sel, 0 error")
