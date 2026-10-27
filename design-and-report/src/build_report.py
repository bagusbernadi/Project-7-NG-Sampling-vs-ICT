"""Membuat design-and-report/index.html (Report Project versi 2) dari page_v1.html dan CSV hasil.

- Pane Design diambil apa adanya dari page_v1.html (dicek identik).
- Semua angka di Report berasal dari project/results/*.csv lewat helper I/D/P/cs (report_lib.py) dan diaudit di akhir.
- DATA PROJECT INI ADALAH SIMULASI (data kerja asli tidak tersedia); hal ini dicatat di bagian 3, 5, 7.6 Report dan README.
Jalankan dari folder mana saja:  python design-and-report/src/build_report.py
"""
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "project" / "code"))
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402
from common import (ACCESS_DATE, DB_PATH, ICT_MIN_PER_UNIT, MIN_UNITS, RES_ANALYSIS, RES_PREP, RES_PRESENT, UNITS_PER_MONTH, WARMUP_DAYS, result)  # noqa: E402
from report_lib import (BLUE, D, GREY, HI, I, NO, OK, P, PART, SOFT, audit, bars, cs, esc, gbars, legend, lines,  # noqa: E402
                        pill, qa, table)

R = lambda n: pd.read_csv(result(n))
PRIO = {1: "Utama", 2: "Utama", 3: "Pendukung", 4: "Utama", 5: "Utama", 6: "Pendukung", 7: "Utama", 8: "Pendukung",
        9: "Utama", 10: "Utama", 11: "Tambahan", 12: "Utama", 13: "Utama", 14: "Pendukung"}
QT = {1: "Berapa OK rate ICT dan FCT per hari, dan bagaimana trennya?",
      2: "Seberapa berbeda NG rate FCT antara unit yang lolos ICT dan unit yang di-skip?",
      3: "Mode NG apa yang dominan (voltage drop atau leakage current), dan apakah berbeda antara unit yang di-skip dan yang di-ICT?",
      4: "Kondisi apa (lot IC, lot PCB, operator SMT, lini, shift) yang NG FCT-nya rendah saat di-skip?",
      5: "Berapa minimal jumlah unit per kondisi agar kesimpulan bisa dipercaya?",
      6: "Seberapa sering unit yang NG di ICT juga NG di FCT setelah diperbaiki?",
      7: "Dari sampel unit NG FCT, berapa persen yang tidak pernah di-ICT, dan bagaimana hasil unit yang pernah?",
      8: "Apakah sampel unit NG saja cukup, atau perlu data unit OK sebagai pembanding?",
      9: "Jika ICT di-skip untuk kondisi aman, berapa jam uji yang dihemat per bulan?",
      10: "Berapa tambahan unit NG yang baru ketahuan di FCT akibat aturan itu?",
      11: "Berapa kapasitas ICT yang bisa dialihkan ke kondisi berisiko?",
      12: "Apakah data sudah dianonimkan dengan benar, tanpa nama, nomor seri asli, atau info pelanggan?",
      13: "Berapa data yang tidak lengkap atau tidak cocok antar tabel, misalnya unit tanpa hasil FCT atau ID ganda?",
      14: "Apakah angka KPI dari database sama persis dengan hitungan manual (Excel atau pandas)?"}
WARN = set()


def Q(n, ans, warn=False):
    if warn:
        WARN.add(n)
    return qa(f"Q{n}", QT[n], PRIO[n], ans, "Terjawab dengan catatan" if warn else "Terjawab", warn)


mk = lambda *a: "".join(a)
CN = {"ic_lot": "Lot IC", "pcb_lot": "Lot PCB", "conn_lot": "Lot konektor", "smt_op": "Operator SMT", "smt_line": "Lini SMT", "shift": "Shift"}

# ---------------------------------------------------------------- data
dq = R("data_quality.csv").set_index("ukuran").nilai.map(lambda v: pd.to_numeric(v, errors="coerce") if pd.notna(pd.to_numeric(v, errors="coerce")) else v)
clog, ck, ctest, cons, rows_t = R("cleaning_log.csv"), R("anonymization_checklist.csv"), R("constraint_tests.csv"), R("consistency_checks.csv"), R("table_rows.csv")
daily, wk, dst, lag = R("daily_summary.csv"), R("weekly_trend.csv"), R("daily_stats.csv").set_index("ukuran").nilai, R("daily_lag_corr.csv").set_index("lag_hari")
pt, mt, mm = R("path_test.csv").set_index("jalur"), R("mode_test.csv").set_index("jalur"), R("mode_measurements.csv").set_index("fail_mode")
cd, nn, i2f, trc = R("conditions.csv"), R("n_needed.csv"), R("ict_to_fct.csv").set_index("ict_result"), R("ng_trace.csv").set_index("ukuran")
cmp_, drw = R("ng_sample_vs_all.csv"), R("ng_sample_draws.csv").iloc[0]
sc, ssu, mus = R("skip_scenarios.csv"), R("scenario_setup.csv").set_index("ukuran").nilai, R("min_units_sensitivity.csv")
tr, cf, leak, hyp, cc = R("truth_recovery.csv"), R("confounding_check.csv"), R("leak_scan.csv").iloc[0], R("hypotheses.csv"), R("crosscheck_pandas.csv")
con = duckdb.connect(str(DB_PATH), read_only=True)
dbc = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("units", "ict", "fct", "daily_summary")}
smp = con.execute("SELECT unit_id, reflow_date, shift, smt_op, ic_lot, path, ict_result, fct_result, fail_mode FROM v_unit WHERE fct_result = 'NG' ORDER BY unit_id LIMIT 4").fetchall()
smp += con.execute("SELECT unit_id, reflow_date, shift, smt_op, ic_lot, path, ict_result, fct_result, fail_mode FROM v_unit WHERE fct_result = 'OK' ORDER BY unit_id LIMIT 3").fetchall()
con.close()
cc_n, cc_v = len(cc), int(cc.jumlah_nilai.sum())
npr = {k: sum(1 for v in PRIO.values() if v == k) for k in ("Utama", "Pendukung", "Tambahan")}
base_skip = float(pt.loc["Skip", "ng_rate"])
cdn = cd[cd.cukup_unit]
sig = cd[(cd.p_bonferroni < 0.05) & cd.cukup_unit & (cd.ng_rate_skip > base_skip)]
low3 = cdn[cdn.ng_rate_skip <= 0.03]
H = sc[(sc.aturan == "Tiga lot material") & (sc.batas_late_ng == 0.03)].iloc[0]
Hs = sc[(sc.aturan == "Semua enam kondisi") & (sc.batas_late_ng == 0.03)].iloc[0]
Hi = sc[(sc.aturan == "IC lot saja") & (sc.batas_late_ng == 0.03)].iloc[0]
ic_c = cd[cd.kondisi == "ic_lot"].sort_values("ng_rate_skip")
worst, small = ic_c[ic_c.cukup_unit].iloc[-1], ic_c[~ic_c.cukup_unit]
confp = cf[cf.kondisi != "ic_lot"].iloc[0]
_z, _n, _k = 1.959964, MIN_UNITS, 1
_p = _k / _n
_c = (_p + _z**2 / (2 * _n)) / (1 + _z**2 / _n)
_h = _z * ((_p * (1 - _p) / _n + _z**2 / (4 * _n**2)) ** 0.5) / (1 + _z**2 / _n)
W30 = (_c - _h, _c + _h)
n_planted = int(((tr.risiko_relatif_ditanam > 1) & tr.cukup_unit).sum())
n_found = int((tr.hasil == "terdeteksi").sum())
n_fp = int((tr.hasil == "positif palsu").sum())

assert (cc.status == "PASS").all() and (ctest.outcome == "ditolak").all() and (cons.violations == 0).all() and ck.lulus.all()
assert pt.loc["Skip", "p_fisher"] < 0.001 and base_skip > pt.loc["ICT", "ng_rate"] and mt.p_fisher.iloc[0] > 0.05
assert leak.kecocokan == 0 and int(dbc["units"]) == int(dq["unit_setelah_cleaning"]) and worst.nilai == drw.lot_ic_ng_rate_tertinggi
assert lag.loc[1, "korelasi"] > lag.loc[0, "korelasi"] and lag.loc[0, "p_value"] > 0.05 and lag.loc[1, "p_value"] < 0.05
assert (abs(H.late_ng_rate_skip_aman - 0.03) < 0.003) and H.net_late_ng_per_bulan > 0 and Hi.net_late_ng_per_bulan > 0 and confp.ng_rate_tanpa_lot_ic_terburuk < confp.ng_rate_semua
assert int(trc.loc["unit NG FCT", "unit"]) == int(dq["fct_ng"])

# ---------------------------------------------------------------- 1. data
kp = lambda c, v, l, d: f'<div class="card kpi" style="--h:var(--{c}H)"><span class="v">{v}</span><span class="l">{l}</span><span class="d">{d}</span></div>'
rp1 = mk(
    '<div class="kpis">',
    kp("navy", I(dbc["units"]), "unit board 8-layer (simulasi)", f"{I(dq['hari_produksi'])} hari produksi (8 minggu, Senin sampai Sabtu); {I(dq['unit_di_ict'])} unit di-ICT dan {I(dq['unit_di_skip'])} di-skip."),
    kp("amber", I(dbc["fct"]), "hasil FCT", f"{I(dq['fct_ng'])} unit NG ({P(dq['fct_ng'] / dq['unit_dengan_fct'], 1)}); {I(dq['unit_tanpa_fct'])} unit tanpa hasil FCT dikeluarkan dari NG rate."),
    kp("teal", I(dbc["ict"]), "hasil ICT", f"{I(dq['ict_ng'])} unit NG di ICT; unit tanpa baris ICT = di-skip."),
    kp("plum", f"{I(ck.lulus.sum())} dari {I(len(ck))}", "pemeriksaan anonimisasi lulus", f"Nilai asli dicari di {I(leak.file_dipindai)} file hasil dan dokumen: {I(leak.kecocokan)} kecocokan."),
    kp("rose", I(cc_v), "nilai dicek silang SQL vs pandas", f"{I(cc_n)} pemeriksaan, semuanya PASS."),
    kp("sky", I(len(ctest)), "uji aturan database", f"Setiap jenis data salah ditolak; {I(len(cons))} pemeriksaan konsistensi menghasilkan 0 pelanggaran."),
    '</div><div class="callout"><h4>Data project ini adalah simulasi</h4><p>Data kerja asli tidak tersedia. Seluruh data dibuat dengan simulasi bersemi (<code>00_simulate_raw.py</code>) dalam format file kerja dengan identitas karangan, lalu dianonimkan dengan alur yang sama seperti data nyata. '
    'Parameter simulasi ada di <code>project/docs/simulation_spec.md</code>. Angka di Report menggambarkan simulasi, bukan lini produksi; yang diuji adalah metodenya.</p></div><h3>1.1 Data mentah dan bersih</h3>')
rp1 += '<div class="card"><h4>Cuplikan riwayat unit (v_unit, data anonim)</h4>' + table(
    ["unit_id", "SMT Reflow", "Shift", "Operator", "Lot IC", "Jalur", "ICT", "FCT", "Mode NG"],
    [[r[0], cs(str(r[1])[:10]), r[2], r[3], r[4], r[5], r[6] or "-", r[7], r[8] or "-"] for r in smp]) + \
    '<p>Satu baris = satu unit. Unit di-skip tidak punya hasil ICT. Kode unit, operator, dan lot sudah anonim; tanggal digeser dengan selisih tetap.</p></div>'
rp1 += '<div class="card"><h4>Tabel 1.1. Kualitas data dan pencocokan unit (log cleaning)</h4>' + table(
    ["Kode", "Masalah", "Baris", "Keputusan"], [[r.kode, r.masalah, I(r.baris), r.keputusan] for r in clog.itertuples()]) + \
    f'<p>Data mentah: {I(dq["unit_baris_mentah"])} baris unit, {I(dq["ict_baris_mentah"])} baris ICT, {I(dq["fct_baris_mentah"])} baris FCT. Setiap keputusan tercatat di <code>cleaning_log.csv</code>. Sumber: simulasi versi sim-1, dibuat {cs(ACCESS_DATE)}.</p></div>'
rp1 += '<h3>1.2 Tabel di database (<code>ict.duckdb</code>)</h3><div class="card"><h4>Tabel 1.2a. Isi database</h4>' + table(
    ["Tabel", "Baris", "Isi"],
    [["units", I(dbc["units"]), "Satu board setelah SMT Reflow. Kunci utama <code>unit_id</code> yang harus berformat kode anonim."],
     ["ict", I(dbc["ict"]), "Satu hasil ICT per unit; tidak ada baris = di-skip. Kunci asing ke units."],
     ["fct", I(dbc["fct"]), "Satu hasil FCT per unit dengan voltage drop, leakage current, dan mode NG; <code>date_flag</code> menandai tanggal salah."],
     ["daily_summary", I(dbc["daily_summary"]), "OK rate ICT dan FCT, jumlah uji, dan skip rate per tanggal."]]) + \
    '<h4>Tabel 1.2b. Uji aturan pengecekan (constraint)</h4>' + table(
    ["Baris salah yang dicoba dimasukkan", "Hasil"], [[r.test, OK("Ditolak") if r.outcome == "ditolak" else NO("Diterima")] for r in ctest.itertuples()]) + \
    f'<p>Seluruh {I(len(ctest))} jenis data salah ditolak, termasuk unit tanpa kode anonim. {I(len(cons))} pemeriksaan konsistensi antar tabel menghasilkan 0 pelanggaran.</p></div>'
FILES = {"anonymization_checklist": ("Checklist anonimisasi", "Q12"), "cleaning_log": ("Log cleaning C1 sampai C8", "Q13"), "consistency_checks": ("Pemeriksaan konsistensi database", "Q13, Q14"),
         "constraint_tests": ("Uji constraint database", "Q13"), "data_quality": ("Ringkasan kualitas data", "Q13"), "profile_columns": ("Profil kolom per tabel", "Q13"), "table_rows": ("Baris per tabel", "Q13"),
         "conditions": ("NG rate dan CI per nilai kondisi", "Q4, Q5"), "conditions_sql": ("Hitungan kondisi dari view SQL", "Q4, Q14"), "confounding_check": ("Cek perancu antar lot", "Q4"), "cross_ict_fct": ("Hasil ICT x FCT dari SQL", "Q6"),
         "crosscheck_pandas": ("KPI SQL vs pandas", "Q14"), "daily_lag_corr": ("Korelasi OK rate harian ICT dan FCT per jeda", "Q1"), "daily_stats": ("Ringkasan OK rate harian", "Q1"), "daily_summary": ("OK rate dan skip rate per tanggal", "Q1"),
         "hypotheses": ("Verdict lima hipotesis", "Hipotesis"), "ict_to_fct": ("Unit di-ICT: hasil ICT vs FCT", "Q6"), "leak_scan": ("Pindai nilai asli di file hasil", "Q12"), "min_units_sensitivity": ("Sensitivitas jumlah unit minimum", "Q5"),
         "mode_by_path": ("Mode NG per jalur dari SQL", "Q3"), "mode_measurements": ("Median pengukuran per mode NG", "Q3"), "mode_test": ("Uji Fisher mode NG per jalur", "Q3"), "n_needed": ("Unit yang dibutuhkan per NG rate dan margin", "Q5"),
         "ng_sample_draws": ("Undian sampel 60 unit NG", "Q8"), "ng_sample_vs_all": ("Komposisi sampel NG vs seluruh produksi", "Q8"), "ng_trace": ("Penelusuran unit NG FCT", "Q7"), "path_rates": ("NG rate per jalur dari SQL", "Q2"),
         "path_test": ("NG rate per jalur, CI, uji Fisher", "Q2"), "scenario_setup": ("Pengaturan evaluasi skenario", "Q9"), "skip_scenarios": ("Skenario aturan skip", "Q9, Q10, Q11"), "truth_recovery": ("Efek ditanam vs hasil analisis", "Validasi"),
         "weekly_trend": ("OK rate dan skip rate per minggu", "Q1")}
resfiles = sorted(p for d in (RES_PREP, RES_ANALYSIS) for p in d.glob("*.csv"))
miss = [p.stem for p in resfiles if p.stem not in FILES]
assert not miss, f"CSV hasil belum didokumentasikan di FILES: {miss}"
rp1 += '<div class="card"><h4>Tabel 1.2c. Data hasil analisis (<code>project/results/</code>)</h4>' + table(
    ["File", "Isi", "Baris", "Menjawab"], [[f"<code>{p.stem}.csv</code>", FILES[p.stem][0], I(len(pd.read_csv(p))), FILES[p.stem][1]] for p in resfiles]) + \
    f'<p>{I(len(resfiles))} file CSV, ditambah {I(len(list(RES_PRESENT.glob("dash_*.csv"))))} CSV data dashboard.</p></div>'
rp1 += '<h3>1.3 Angka kunci (KPI)</h3><div class="card"><h4>Tabel 1.3. Lima KPI (definisi di <code>project/docs/definitions.md</code>)</h4>' + table(
    ["KPI", "Rumus ringkas", "Hasil", "Jumlah data"],
    [["ICT OK rate", "unit OK di ICT ÷ unit diuji ICT", P(dst["ict_ok_rate_rata2"], 1) + " (rata-rata harian)", f"{I(dbc['ict'])} hasil ICT"],
     ["FCT OK rate", "unit OK di FCT ÷ unit diuji FCT", P(dst["fct_ok_rate_rata2"], 1) + " (rata-rata harian)", f"{I(dbc['fct'])} hasil FCT"],
     ["Skip rate", "unit di-skip ÷ unit SMT Reflow", P(dq["unit_di_skip"] / dq["unit_setelah_cleaning"], 1), f"{I(dq['unit_setelah_cleaning'])} unit"],
     ["Late NG rate", "unit di-skip yang NG di FCT ÷ unit di-skip dengan hasil FCT", P(base_skip, 1), f"{I(pt.loc['Skip', 'ng'])} dari {I(pt.loc['Skip', 'n'])} unit"],
     ["Jam ICT dihemat (estimated)", f"unit ICT di kondisi aman × {D(ICT_MIN_PER_UNIT, 0)} menit ÷ 60, per {I(UNITS_PER_MONTH)} unit per bulan", f"{D(H.jam_ict_dihemat_per_bulan, 1)} jam per bulan", "aturan tiga lot, batas 3%, asumsi rancangan"]]) + \
    '<p>Waktu ICT per unit dan volume per bulan adalah angka contoh dari rancangan, bukan data kerja.</p></div>'

# ---------------------------------------------------------------- 2. business questions
dd = daily[daily.fct_tested > 0].reset_index(drop=True)
sec21 = mk(
    '<h3 id="sec21">2.1 Hasil uji: seberapa banyak lolos <span class="qlist">Q1, Q2, Q3</span></h3><div class="card">',
    Q(1, f"Rata-rata harian OK rate ICT {P(dst['ict_ok_rate_rata2'], 1)} (simpangan baku {P(dst['ict_ok_rate_sd'], 1)}) dan FCT {P(dst['fct_ok_rate_rata2'], 1)} ({P(dst['fct_ok_rate_sd'], 1)}), tanpa tren naik atau turun yang tegas; skip rate per minggu berkisar {P(wk.skip_rate.min(), 0)} sampai {P(wk.skip_rate.max(), 0)}. "
         f"OK rate harian ICT dan FCT pada hari yang sama berkorelasi lemah (r = {D(lag.loc[0, 'korelasi'], 2)}, p = {D(lag.loc[0, 'p_value'], 2)}, {I(lag.loc[0, 'n_hari'])} hari) karena unit diuji FCT 1 sampai 4 hari setelah reflow; dengan jeda 1 hari r = {D(lag.loc[1, 'korelasi'], 2)} (p = {D(lag.loc[1, 'p_value'], 3)}), "
         "kemungkinan karena lot bertahan beberapa hari. Hipotesis 4 benar sebagian: angka harian tidak bisa dibandingkan langsung, perbandingan harus per unit."),
    Q(2, f"Unit di-skip NG di FCT {P(pt.loc['Skip', 'ng_rate'], 1)} ({I(pt.loc['Skip', 'ng'])} dari {I(pt.loc['Skip', 'n'])}; CI 95% {P(pt.loc['Skip', 'ci_low'], 1)} sampai {P(pt.loc['Skip', 'ci_high'], 1)}) dibanding {P(pt.loc['ICT', 'ng_rate'], 1)} pada unit yang lolos ICT ({I(pt.loc['ICT', 'ng'])} dari {I(pt.loc['ICT', 'n'])}; {P(pt.loc['ICT', 'ci_low'], 1)} sampai {P(pt.loc['ICT', 'ci_high'], 1)}). "
         f"Risiko relatif {D(pt.loc['Skip', 'relative_risk'], 2)}, uji Fisher p &lt; {D(0.001, 3)}. Hipotesis 1 terbukti. Ini unit yang di-skip karena kapasitas, bukan acak; selisih bisa sebagian berasal dari kondisi yang berbeda (shift malam lebih sering di-skip)."),
    Q(3, f"Voltage drop (VD) {P(mt.loc['Skip', 'porsi_vd'], 0)} dari NG unit di-skip ({I(mt.loc['Skip', 'vd'])} dari {I(mt.loc['Skip', 'ng'])}) dan {P(mt.loc['ICT', 'porsi_vd'], 0)} pada unit lolos ICT ({I(mt.loc['ICT', 'vd'])} dari {I(mt.loc['ICT', 'ng'])}); selisihnya belum nyata (Fisher p = {D(mt.loc['Skip', 'p_fisher'], 2)}). "
         f"Median pengukuran NG: voltage drop {D(mm.loc['VD', 'vdrop_max_mv'], 1)} mV pada mode VD dan leakage {D(mm.loc['LC', 'leak_max_ua'], 1)} µA pada mode LC."),
    '<h4>Grafik 2.1a. OK rate harian ICT dan FCT</h4>',
    lines([f"{i + 1:02d}" for i in range(len(dd))], [("ICT OK rate", BLUE, 2.5, list(dd.ict_ok_rate.fillna(dd.ict_ok_rate.mean()))), ("FCT OK rate", HI, 2.5, list(dd.fct_ok_rate))], lambda v: P(v, 0), "OK rate harian", zero=False),
    legend([(BLUE, "ICT"), (HI, "FCT")]),
    '<h4>Grafik 2.1b. NG rate FCT per jalur (CI 95%)</h4>',
    bars([("Lolos ICT", pt.loc["ICT", "ng_rate"], BLUE, f"Lolos ICT: {P(pt.loc['ICT', 'ng_rate'], 1)}, {I(pt.loc['ICT', 'ng'])} dari {I(pt.loc['ICT', 'n'])}"), ("Di-skip", pt.loc["Skip", "ng_rate"], HI, f"Di-skip: {P(pt.loc['Skip', 'ng_rate'], 1)}, {I(pt.loc['Skip', 'ng'])} dari {I(pt.loc['Skip', 'n'])}")], lambda v: P(v, 1), "NG rate FCT per jalur", rot=0, small=True),
    '<h4>Tabel 2.1c. OK rate dan skip rate per minggu</h4>',
    table(["Minggu", "Hari", "Unit SMT Reflow", "ICT OK rate", "FCT OK rate", "Skip rate"], [[I(r.minggu), I(r.hari), I(r.unit), P(r.ict_ok_rate, 1), P(r.fct_ok_rate, 1), P(r.skip_rate, 1)] for r in wk.itertuples()]), '</div>')
sec22 = mk(
    '<h3 id="sec22">2.2 Kondisi: kapan skip aman <span class="qlist">Q4, Q5, Q6</span></h3><div class="card">',
    Q(4, f"Dari {I(len(cdn))} nilai kondisi dengan unit di-skip cukup (minimal {I(MIN_UNITS)}), {I(len(low3))} punya late NG rate di bawah {P(0.03, 0)}: " + ", ".join(f"{CN[r.kondisi]} {r.nilai} ({P(r.ng_rate_skip, 1)}, n = {I(r.n_skip)})" for r in low3.sort_values('ng_rate_skip').itertuples()) +
         f". Kondisi berisiko tinggi (p Bonferroni &lt; {D(0.05, 2)}): " + ", ".join(f"{CN[r.kondisi]} {r.nilai} ({P(r.ng_rate_skip, 1)})" for r in sig.itertuples()) + ". "
         f"Hati-hati dengan perancu: lot PCB {confp.nilai} tampak {P(confp.ng_rate_semua, 1)}, tetapi {P(confp.porsi_unit_lot_ic_terburuk, 0)} unitnya berasal dari lot IC terburuk dan tanpa unit itu turun ke {P(confp.ng_rate_tanpa_lot_ic_terburuk, 1)}. "
         f"Dari efek yang ditanam di simulasi, analisis hanya menemukan {I(n_found)} dari {I(n_planted)} yang cukup datanya (lot IC dengan risiko 6 kali lipat); efek 1,2 sampai 2,2 kali tidak terdeteksi dengan data sebesar ini. Pola belum tentu penyebab.", warn=True),
    Q(5, f"Untuk NG rate sekitar {P(0.03, 0)}, margin ±{P(0.02, 0)} memerlukan sekitar {I(nn[(nn.ng_rate == 0.03) & (nn.margin == 0.02)].unit_dibutuhkan.iloc[0])} unit di-skip per kondisi, dan margin ±{P(0.01, 0)} sekitar {I(nn[(nn.ng_rate == 0.03) & (nn.margin == 0.01)].unit_dibutuhkan.iloc[0])} unit. "
         f"Batas {I(MIN_UNITS)} unit dari rancangan hanya menyaring kondisi yang terlalu kecil: pada {I(MIN_UNITS)} unit dengan 1 NG, CI 95% Wilson {P(W30[0], 1)} sampai {P(W30[1], 0)}, jadi kondisi berukuran {I(MIN_UNITS)} sampai beberapa ratus unit hanya memberi indikasi. "
         f"Lot IC uji coba {small.nilai.iloc[0]} hanya {I(small.n_skip.iloc[0])} unit di-skip ({P(small.ng_rate_skip.iloc[0], 0)}, CI {P(small.ci_low.iloc[0], 0)} sampai {P(small.ci_high.iloc[0], 0)}) dan karena itu tidak dijadikan dasar aturan."),
    Q(6, f"Dari {I(i2f.loc['NG', 'n'])} unit yang NG di ICT, {I(i2f.loc['NG', 'NG'])} ({P(i2f.loc['NG', 'porsi_fct_ng'], 1)}) masih NG di FCT setelah diperbaiki, dibanding {P(i2f.loc['OK', 'porsi_fct_ng'], 1)} ({I(i2f.loc['OK', 'NG'])} dari {I(i2f.loc['OK', 'n'])}) pada unit yang OK di ICT. "
         "NG di ICT adalah tanda risiko, tetapi sebagian besar unit yang diperbaiki lolos FCT."),
    '<h4>Grafik 2.2a. Late NG rate per lot IC (unit di-skip)</h4>',
    bars([(r.nilai, r.ng_rate_skip, (BLUE if r.cukup_unit else GREY), f"{r.nilai}: {P(r.ng_rate_skip, 1)}, {I(r.ng_skip)} dari {I(r.n_skip)} unit di-skip, CI {P(r.ci_low, 1)} sampai {P(r.ci_high, 1)}" + ("" if r.cukup_unit else " (unit &lt; 30)")) for r in ic_c.itertuples()],
         lambda v: P(v, 0), "Late NG rate per lot IC", rot=0, small=True),
    legend([(BLUE, "Unit di-skip ≥ 30"), (GREY, "Unit di-skip &lt; 30, bukan dasar aturan")]),
    '<h4>Tabel 2.2b. Late NG rate per nilai kondisi (unit di-skip) dengan CI Wilson 95%</h4>',
    table(["Kondisi", "Nilai", "Unit di-skip", "Late NG", "Late NG rate", "CI 95%", "Cukup unit", "p (vs lainnya, Bonferroni)", "NG rate lolos ICT"],
          [[CN[r.kondisi], r.nilai, I(r.n_skip), I(r.ng_skip), P(r.ng_rate_skip, 1), f"{P(r.ci_low, 1)} sampai {P(r.ci_high, 1)}", OK("Ya") if r.cukup_unit else NO("Tidak"), D(r.p_bonferroni, 3), P(r.ng_rate_ict, 1)] for r in cd.itertuples()]),
    '<h4>Tabel 2.2c. Unit yang dibutuhkan agar interval cukup sempit</h4>',
    table(["NG rate", "Margin (± setengah lebar CI)", "Unit di-skip dibutuhkan"], [[P(r.ng_rate, 0), P(r.margin, 0), I(r.unit_dibutuhkan)] for r in nn.itertuples()]), '</div>')
sec23 = mk(
    '<h3 id="sec23">2.3 Sampling: apakah sampel mewakili <span class="qlist">Q7, Q8</span></h3><div class="card">',
    Q(7, f"Dari {I(trc.loc['unit NG FCT', 'unit'])} unit NG FCT, {I(trc.loc['tidak pernah di-ICT (di-skip)', 'unit'])} ({P(trc.loc['tidak pernah di-ICT (di-skip)', 'porsi'], 0)}) tidak pernah di-ICT, jadi akar masalahnya tidak bisa ditelusuri dari hasil ICT. "
         f"{I(trc.loc['pernah di-ICT', 'unit'])} ({P(trc.loc['pernah di-ICT', 'porsi'], 0)}) pernah di-ICT: {I(trc.loc['pernah di-ICT dan OK di ICT (lolos ICT, NG di FCT)', 'unit'])} OK di ICT (lolos, tetapi NG di FCT) dan {I(trc.loc['pernah di-ICT dan NG di ICT (NG di FCT setelah diperbaiki)', 'unit'])} NG di ICT lalu masih NG setelah perbaikan."),
    Q(8, f"Tidak cukup untuk menilai kondisi aman. Komposisi unit NG berbeda dari seluruh produksi pada {I((cmp_.p_value < 0.05).sum())} dari {I(len(cmp_))} kondisi (chi-kuadrat p &lt; {D(0.05, 2)}), sehingga persentase kondisi di sampel NG tidak sama dengan NG rate. "
         f"Dalam {I(drw.undian)} undian sampel {I(drw.ukuran_sampel)} unit NG, lot IC terburuk ({drw.lot_ic_ng_rate_tertinggi}) menjadi yang terbanyak pada {P(drw.porsi_undian_lot_terbanyak_benar, 0)} undian, jadi sampel NG cukup untuk mencurigai lot terburuk, "
         "tetapi tanpa data unit OK tidak ada NG rate, tidak ada CI, dan lot yang aman tidak bisa ditunjuk. Hipotesis 5 benar sebagian.", warn=False),
    '<h4>Tabel 2.3a. Penelusuran unit NG FCT</h4>',
    table(["Ukuran", "Unit", "Porsi dari unit NG"], [[k, I(r.unit), P(r.porsi, 1)] for k, r in trc.iterrows()]),
    '<h4>Tabel 2.3b. Komposisi sampel NG vs seluruh produksi</h4>',
    table(["Kondisi", "Jumlah nilai", "Chi-kuadrat", "p", "Selisih porsi terbesar"], [[CN[r.kondisi], I(r.nilai_beda), D(r.chi2, 1), D(r.p_value, 3), P(r.selisih_porsi_maks, 1)] for r in cmp_.itertuples()]),
    '<p>Selisih porsi terbesar = selisih terbesar antara porsi sebuah nilai kondisi di unit NG dan di seluruh produksi.</p></div>')
sec24 = mk(
    '<h3 id="sec24">2.4 Dampak: jika aturan skip diterapkan <span class="qlist">Q9, Q10, Q11</span></h3><div class="card">',
    Q(9, f"Aturan walk-forward (hari ke-{I(WARMUP_DAYS + 1)} dan seterusnya, memakai bukti dari hari sebelumnya, minimal {I(MIN_UNITS)} unit) pada tiga lot material dengan batas late NG {P(0.03, 0)}: {P(H.porsi_unit_aman, 0)} unit memenuhi aturan; menghemat {D(H.jam_ict_dihemat_per_bulan, 1)} jam ICT per bulan "
         f"({D(H.unit_ict_dihemat_per_bulan, 0)} unit tidak perlu di-ICT, {D(ICT_MIN_PER_UNIT, 0)} menit per unit, {I(UNITS_PER_MONTH)} unit per bulan; keduanya asumsi rancangan). Hasilnya estimated dari data simulasi; batas {P(0.02, 0)} sampai {P(0.05, 0)} dan aturan lain ada di Tabel 2.4a.", warn=True),
    Q(10, f"Pada aturan yang sama, late NG rate sebenarnya unit aman yang di-skip {P(H.late_ng_rate_skip_aman, 1)}, yaitu sekitar batas {P(0.03, 0)} dan bukan di bawahnya dibanding {P(H.ng_rate_ict_aman, 1)} bila tetap di-ICT, sehingga tambahan NG yang baru ketahuan di FCT sekitar {D(H.tambahan_late_ng_per_bulan, 1)} unit per bulan (estimated). "
          f"Tampak kecil, tetapi tergantung noise sampel: pada batas {P(0.02, 0)} untuk tiga lot, NG rate unit yang tetap di-ICT ({P(sc[(sc.aturan == 'Tiga lot material') & (sc.batas_late_ng == 0.02)].ng_rate_ict_aman.iloc[0], 1)}) justru lebih tinggi dari yang di-skip.", warn=True),
    Q(11, f"Jam ICT yang dihemat setara {D(H.unit_ict_dihemat_per_bulan, 0)} unit per bulan yang bisa dialihkan ke unit yang sekarang di-skip di kondisi berisiko. Bila dialihkan ({D(H.unit_dialihkan_per_bulan, 0)} unit), NG di kondisi berisiko yang tertangkap ICT sekitar {D(H.late_ng_dihindari_per_bulan, 1)} unit per bulan, jadi efek bersih sekitar {D(H.net_late_ng_per_bulan, 1)} late NG lebih sedikit per bulan (estimated). "
          f"Aturan satu faktor (lot IC saja, batas {P(0.03, 0)}) menghemat lebih banyak ({D(Hi.jam_ict_dihemat_per_bulan, 1)} jam) tetapi menambah {D(Hi.tambahan_late_ng_per_bulan, 1)} late NG; aturan enam kondisi menghemat {D(Hs.jam_ict_dihemat_per_bulan, 1)} jam.", warn=True),
    '<h4>Grafik 2.4a. Jam ICT dihemat per bulan menurut aturan dan batas (estimated)</h4>',
    gbars([P(t, 0) for t in sorted(sc.batas_late_ng.unique())], [(a, c, list(sc[sc.aturan == a].sort_values("batas_late_ng").jam_ict_dihemat_per_bulan)) for a, c in (("IC lot saja", HI), ("Tiga lot material", BLUE), ("Semua enam kondisi", GREY))],
          lambda v: D(v, 0), "Jam ICT dihemat per bulan", rot=0),
    legend([(HI, "IC lot saja"), (BLUE, "Tiga lot material"), (GREY, "Semua enam kondisi")]),
    '<h4>Tabel 2.4a. Skenario aturan skip (estimated, walk-forward)</h4>',
    table(["Aturan", "Batas late NG", "Unit aman", "Late NG rate aman (di-skip)", "NG rate aman (di-ICT)", "Jam ICT dihemat per bulan", "Tambahan late NG per bulan", "Late NG dihindari per bulan", "Efek bersih per bulan"],
          [[r.aturan, P(r.batas_late_ng, 0), P(r.porsi_unit_aman, 0), P(r.late_ng_rate_skip_aman, 1), P(r.ng_rate_ict_aman, 1), D(r.jam_ict_dihemat_per_bulan, 1), D(r.tambahan_late_ng_per_bulan, 1), D(r.late_ng_dihindari_per_bulan, 1), D(r.net_late_ng_per_bulan, 1)] for r in sc.itertuples()]),
    f'<p>{I(ssu["hari_dievaluasi"])} hari dievaluasi ({I(ssu["unit_dievaluasi"])} unit), diskalakan ke {I(UNITS_PER_MONTH)} unit per bulan. Efek bersih = late NG dihindari − tambahan late NG; positif berarti lebih baik. Late NG rate semua unit di-skip pada periode itu {P(sc.late_ng_rate_skip_semua.iloc[0], 1)}.</p>',
    '<h4>Tabel 2.4b. Sensitivitas jumlah unit minimum (tiga lot, batas 3%)</h4>',
    table(["Unit minimum", "Unit aman", "Late NG rate aman", "Jam ICT dihemat per bulan", "Efek bersih per bulan"], [[I(r.min_unit), I(r.unit_aman), P(r.late_ng_rate_skip_aman, 1), D(r.jam_ict_dihemat_per_bulan, 1), D(r.net_late_ng_per_bulan, 1)] for r in mus.itertuples()]), '</div>')
sec25 = mk(
    '<h3 id="sec25">2.5 Validitas dan privasi data <span class="qlist">Q12, Q13, Q14</span></h3><div class="card">',
    Q(12, f"{I(ck.lulus.sum())} dari {I(len(ck))} pemeriksaan anonimisasi lulus (Tabel 2.5a): kode unit, operator, lot, lini, dan shift diganti; kolom pelanggan, model produk, dan stasiun dihapus; tanggal digeser. Nilai asli dicari ({I(leak.nilai_asli_dicari)} nilai) di {I(leak.file_dipindai)} file hasil, dokumen, kode, dan sampel: {I(leak.kecocokan)} kecocokan. Mapping key dan data mentah diabaikan Git. "
          "Catatan: pada project ini data mentah adalah simulasi dengan identitas karangan, jadi yang dibuktikan adalah prosedur dan pemeriksaannya, bukan keamanan data pabrik sebenarnya.", warn=True),
    Q(13, f"Dari {I(dq['unit_baris_mentah'])} unit, {I(dq['unit_tanpa_fct'])} tidak punya hasil FCT ({P(dq['unit_tanpa_fct'] / dq['unit_baris_mentah'], 1)}; dikeluarkan dari NG rate, {I(dq['unit_ict_tanpa_fct'])} di antaranya sudah di-ICT). Baris ICT ganda {I(clog.set_index('kode').loc['C3', 'baris'])} (satu dipertahankan), baris FCT yatim {I(clog.set_index('kode').loc['C1', 'baris'])} (dibuang), "
          f"dan {I(clog.set_index('kode').loc['C6', 'baris'])} tanggal FCT sebelum reflow (hasil dipakai, dikeluarkan dari hitungan harian). Tidak ada ID ganda pada FCT dan tidak ada ICT yang lebih akhir dari FCT. Setiap unit bisa ditelusuri dari SMT Reflow sampai FCT lewat <code>v_unit</code>."),
    Q(14, f"Ya. {I(cc_n)} pemeriksaan ({I(cc_v)} nilai) NG rate per jalur, per kondisi, mode NG, tabel silang ICT × FCT, dan OK rate harian dari SQL sama dengan hitungan pandas (selisih terbesar di bawah 1E-9). "
          "Rancangan menyebut Excel (opsional) dengan PivotTable; cek silang dikerjakan dengan pandas, jadi cek silang ke Excel belum dilakukan.", warn=True),
    '<h4>Tabel 2.5a. Checklist anonimisasi</h4>',
    table(["Pemeriksaan", "Hasil", "Detail"], [[cs(r.pemeriksaan), OK("Lulus") if r.lulus else NO("Gagal"), cs(r.detail)] for r in ck.itertuples()]),
    '<h4>Tabel 2.5b. Verdict lima hipotesis</h4>',
    table(["No", "Hipotesis", "Verdict", "Bukti"], [[r.id[1:], r.hipotesis, (OK if r.verdict == "Terbukti" else PART)(r.verdict), cs(r.bukti)] for r in hyp.itertuples()]),
    '<h4>Tabel 2.5c. Efek yang ditanam di simulasi vs temuan analisis</h4>',
    table(["Kondisi", "Nilai", "Risiko relatif ditanam", "Unit di-skip", "Late NG rate", "Hasil"],
          [[CN[r.kondisi], r.nilai, D(r.risiko_relatif_ditanam, 1), I(r.n_skip), P(r.ng_rate_skip, 1), r.hasil] for r in tr[(tr.risiko_relatif_ditanam > 1) | (tr.hasil == "positif palsu")].itertuples()]),
    '<p>Kebenaran simulasi hanya dipakai untuk memeriksa analisis (<code>07_validate.py</code>), bukan untuk menganalisis.</p></div>')
rp2_body = mk(sec21, sec22, sec23, sec24, sec25)
SEC = {1: "21", 2: "21", 3: "21", 4: "22", 5: "22", 6: "22", 7: "23", 8: "23", 9: "24", 10: "24", 11: "24", 12: "25", 13: "25", 14: "25"}
qn_uniq = sorted(set(int(x) for x in re.findall(r'<span class="qn">Q(\d+)</span>', rp2_body)))
assert qn_uniq == list(range(1, 15)), qn_uniq
nw = len(WARN)
wtxt = ", ".join(f"Q{n}" for n in sorted(WARN))
chips = '<div class="qchips">' + "".join(f'<a class="qc{" w" if n in WARN else ""}" href="#sec{SEC[n]}" title="{esc(QT[n])}">Q{n}</a>' for n in range(1, 15)) + "</div>"
rp2 = mk(f'<div class="card"><p><b>Jawaban singkat:</b> semua {len(QT)} pertanyaan terjawab ({npr["Utama"]} Utama, {npr["Pendukung"]} Pendukung, {npr["Tambahan"]} Tambahan). '
         f'{nw} jawaban dengan catatan (kuning): {wtxt}. Klik nomor pertanyaan untuk melompat ke pembahasannya. Semua angka berasal dari data simulasi; dampak memakai asumsi rancangan.</p>',
         chips, '<p class="report-note">Q hijau = terjawab, Q kuning = terjawab dengan catatan. Pembahasan dikelompokkan per tema (2.1 sampai 2.5).</p></div>', rp2_body)

# ---------------------------------------------------------------- 3-5. dataset, tools, alur
CODE_REL = "project/code/"
allcode = list((REPO / CODE_REL).rglob("*.py"))
npy, loc = len(allcode), sum(len(p.read_text(encoding="utf-8").splitlines()) for p in allcode)
nsql = len(list((REPO / CODE_REL).rglob("*.sql")))
hv = hyp.set_index("id")
rp3 = mk(f'<div class="card"><p><b>Jawaban singkat:</b> dataset berubah dari rancangan: <b>data kerja asli diganti data simulasi</b> karena data kerja tidak tersedia. Struktur empat tabel, kondisi produksi, dan alur anonimisasi mengikuti rancangan, tetapi seluruh angka adalah simulasi. '
         'Dua hipotesis terbukti dan tiga sebagian.</p></div>',
         table(["Aspek", "Rancangan", "Realisasi", "Verdict"], [
             ["Sumber data", "Data kerja lini PCBA 8-layer dari file Excel kerja, dianonimkan", f"<b>Data simulasi</b> bersemi ({I(dbc['units'])} unit, 8 minggu) dalam format file kerja dengan identitas karangan, lalu dianonimkan dengan alur yang sama. Parameter di <code>project/docs/simulation_spec.md</code>; kebenaran simulasi dipakai untuk memeriksa temuan", PART("Berubah")],
             ["Izin penggunaan data kerja", "Dipastikan dengan atasan atau perusahaan sebelum dipublikasikan", "Tidak berlaku pada data simulasi; harus dipastikan bila data asli dipakai nanti", PART("Tidak berlaku")],
             ["Ukuran", "±60 unit NG, diperluas ke semua board 8-layer termasuk OK", f"{I(dq['unit_baris_mentah'])} unit termasuk OK, {I(dq['fct_ng'])} unit NG FCT; cukup untuk perbandingan per kondisi", OK("Sesuai")],
             ["Tabel", "units, ict, fct, daily_summary", f"Keempatnya dengan constraint; {I(dbc['units'])}, {I(dbc['ict'])}, {I(dbc['fct'])}, {I(dbc['daily_summary'])} baris", OK("Sesuai")],
             ["Aturan anonimisasi", "Kode U-0001, Op_01, Lot_A, tanggal digeser, mapping key terpisah", f"Sesuai; {I(ck.lulus.sum())} dari {I(len(ck))} pemeriksaan otomatis lulus; nama net, pelanggan, model, dan stasiun juga diganti atau dihapus", OK("Sesuai")],
             ["Data tidak lengkap", "Diaudit (Q13)", f"{I(dq['unit_tanpa_fct'])} unit tanpa FCT, baris ICT ganda, FCT yatim, tanggal salah: dibuat di simulasi supaya prosedur cleaning teruji", PART("Sesuai + penyesuaian")],
             ["Hipotesis 1: unit di-skip lebih sering NG di FCT", "Belum terbukti", cs(hv.loc["H1", "bukti"]), OK("Terbukti")],
             ["Hipotesis 2: NG terkumpul di lot tertentu", "Belum terbukti", cs(hv.loc["H2", "bukti"]), OK("Terbukti")],
             ["Hipotesis 3: ada kondisi NG rendah yang aman di-skip", "Belum terbukti", cs(hv.loc["H3", "bukti"]), PART("Sebagian")],
             ["Hipotesis 4: OK rate harian ICT tidak bisa menebak FCT hari yang sama", "Belum terbukti", cs(hv.loc["H4", "bukti"]), PART("Sebagian")],
             ["Hipotesis 5: sampel NG saja tidak cukup", "Belum terbukti", cs(hv.loc["H5", "bukti"]), PART("Sebagian")],
             ["Angka asumsi", f"ICT {D(ICT_MIN_PER_UNIT, 0)} menit per unit, {I(UNITS_PER_MONTH)} unit per bulan, minimal {I(MIN_UNITS)} unit", "Dipakai apa adanya sebagai asumsi; dapat diubah di <code>common.py</code> dan di dashboard", OK("Sesuai")]]))
rp4 = mk('<div class="card"><p><b>Jawaban singkat:</b> semua tools rancangan dipakai kecuali Excel (opsional, diganti pandas). Streamlit dibuat dan diuji lokal tetapi belum di-deploy.</p></div>',
         table(["Tool", "Rancangan", "Realisasi", "Verdict"], [
             ["Python (pandas, SciPy)", "Anonimisasi, cleaning, uji Fisher dan CI", f"{I(npy)} skrip dan modul, {I(loc)} baris; SciPy untuk uji Fisher dan chi-kuadrat, interval Wilson dihitung sendiri; ditambah simulator data", OK("Sesuai")],
             ["DuckDB + SQL", "Menggabungkan riwayat unit, NG rate per jalur dan kondisi, ringkasan harian sebagai view", f"<code>ict.duckdb</code> dengan constraint dan FK; {I(nsql)} file SQL; 6 view KPI", OK("Sesuai")],
             ["Excel (opsional)", "Cek silang PivotTable (Q14)", f"Diganti cek silang pandas ({I(cc_n)} pemeriksaan); Excel juga format asal data kerja, tidak relevan pada data simulasi", PART("Diganti pandas")],
             ["Streamlit + Plotly", "Dashboard 4 halaman dengan filter dan slider batas NG rate", "<code>streamlit/app.py</code> 4 halaman (Ringkasan, Jalur uji, Kondisi produksi, Simulasi aturan skip), diuji dengan <code>AppTest</code>; belum di-deploy", PART("Sebagian")],
             ["GitHub", "Kode, query, README; data mentah dan mapping key tidak diunggah", "Struktur dan README siap di branch <code>project-7-build</code>, belum digabung ke <code>main</code>; data mentah dan mapping key diabaikan Git", PART("Sebagian")],
             ["Markdown", "README", "README dan dokumen dibuat dari CSV hasil", OK("Sesuai")],
             ["matplotlib dan nbformat", "Tidak ada di rancangan", "Infografis dan notebook otomatis", PART("Tambahan")]]))
steps = [("1", "Menyepakati definisi KPI dan aturan", "<code>project/docs/definitions.md</code>", PART("Sesuai + penyesuaian"), "Aturan skip dibuat walk-forward (bukti hanya dari hari sebelumnya); belum disepakati dengan tim lini."),
         ("2", "Merancang struktur tabel", "<code>01_schema.sql</code>, <code>data_dictionary.md</code>, <code>anonymization_checklist.md</code>", OK("Sesuai"), "Ditambah constraint kode anonim."),
         ("3", "Mengumpulkan dan menganonimkan data", "<code>00_simulate_raw.py</code>, <code>01_anonymize_load.py</code>", PART("Berubah"), "Data kerja asli tidak tersedia: data mentah disimulasikan, anonimisasi dijalankan seperti pada data nyata."),
         ("4", "Membersihkan dan mencocokkan unit", "<code>01_anonymize_load.py</code>", OK("Sesuai"), "Log C1 sampai C8."),
         ("5", "Memasukkan data ke database", "<code>02_build_db.py</code>, <code>02_load.sql</code>", PART("Sesuai + tambahan"), "Ditambah uji penolakan dan pemeriksaan konsistensi."),
         ("6", "Menulis query KPI per jalur", "<code>03_views.sql</code>, <code>03_run_queries.py</code>", OK("Sesuai"), ""),
         ("7", "Cek silang", "<code>04_crosscheck.py</code>", PART("Sesuai + penyesuaian"), "Dengan pandas, bukan Excel."),
         ("8", "Menganalisis per jalur dan kondisi", "<code>05_analysis.py</code>", OK("Sesuai"), "Fisher, Wilson, Bonferroni."),
         ("9", "Menghitung skenario aturan skip", "<code>06_scenarios.py</code>, <code>rule_lib.py</code>", PART("Sesuai + tambahan"), "Tiga keluarga aturan, empat batas, evaluasi walk-forward."),
         ("10", "Menguji kewajaran temuan", "<code>07_validate.py</code>", PART("Sesuai + tambahan"), "Ditambah pemulihan efek ditanam, cek perancu, pindai kebocoran identitas."),
         ("11", "Membuat dashboard", "<code>08_build_dashboard_data.py</code>, <code>streamlit/app.py</code>", PART("Sebagian"), "Belum di-deploy ke Streamlit Community Cloud."),
         ("12", "Menulis README dan finalisasi", "<code>11_build_readme.py</code>, halaman ini", PART("Sebagian"), "Siap; digabung ke main setelah ditinjau.")]
renames = [("docs/kpi_definitions.md", "project/docs/definitions.md"), ("docs/data_dictionary.md", "project/docs/data_dictionary.md"), ("docs/anonymization_checklist.md", "project/docs/anonymization_checklist.md"),
           ("data/raw/", "project/data/raw/ (tidak di-commit; hasil simulasi)"), ("data/mapping_key.csv", "project/data/mapping_key.csv (tidak di-commit)"), ("data/sample/", "project/data/sample/"),
           ("scripts/anonymize_load.py", CODE_REL + "1-data-preparation/python/01_anonymize_load.py, " + CODE_REL + "1-data-preparation/python/02_build_db.py"), ("outputs/cleaning_log.csv", "project/results/1-data-preparation/cleaning_log.csv"),
           ("sql/", CODE_REL + "1-data-preparation/sql/01_schema.sql, " + CODE_REL + "2-analysis/sql/03_views.sql"), ("ict.duckdb", "project/ict.duckdb (tidak di-commit)"),
           ("notebooks/analysis.ipynb", "project/results/3-presentation/analysis.ipynb"), ("outputs/skip_scenarios.csv", "project/results/2-analysis/skip_scenarios.csv"),
           ("outputs/crosscheck.xlsx", "project/results/2-analysis/crosscheck_pandas.csv"), ("dashboard/app.py", CODE_REL + "3-presentation/streamlit/app.py"),
           ("outputs/one_sheet.pdf / .png", "project/results/3-presentation/infographic.pdf, project/results/3-presentation/infographic.png"), ("requirements.txt", "project/requirements.txt"),
           ("(tidak ada)", "project/docs/simulation_spec.md, " + CODE_REL + "1-data-preparation/python/00_simulate_raw.py, " + CODE_REL + "2-analysis/python/07_validate.py")]
for a, b in renames:
    for part in b.split(", "):
        part = part.split(" (")[0]
        if "tidak di-commit" in b and ("raw" in part or "mapping" in part or "duckdb" in part):
            continue
        assert (REPO / part).exists(), part
rp5 = mk('<div class="card"><p><b>Jawaban singkat:</b> 12 langkah dijalankan sesuai urutan, dengan satu perubahan besar: langkah 3 memakai data simulasi karena data kerja tidak tersedia. Cek silang memakai pandas, dan dua langkah (11 dan 12) belum sepenuhnya selesai.</p></div>',
         table(["Langkah", "Rancangan", "Realisasi", "Verdict", "Catatan"], [[a, b, c, d, e] for a, b, c, d, e in steps]),
         '<div class="card"><h4>Penyesuaian dan improvisasi yang tidak ada di rancangan</h4><ul class="tight">',
         '<li><b>Simulasi data.</b> Atas keputusan pemilik project, dataset dibuat dari simulasi bersemi (efek ditanam: lot IC buruk, operator, shift, perancu antar lot) dan dicatat di Report dan README. Efek yang ditanam dipakai untuk memeriksa analisis, bukan untuk analisis.</li>',
         '<li>Evaluasi aturan skip memakai walk-forward (bukti hanya dari hari sebelumnya) karena lot berganti tiap beberapa hari; pembagian latih dan uji menurut minggu menghasilkan nol unit aman sehingga ditinggalkan.</li>',
         f'<li>Lot baru tanpa bukti cukup (kurang dari {I(MIN_UNITS)} unit di-skip) dianggap berisiko; hari awal ({I(WARMUP_DAYS)} hari) hanya mengumpulkan bukti.</li>',
         '<li>Uji Fisher ditambah koreksi Bonferroni untuk banyak kondisi, dan cek perancu antar lot.</li>',
         '<li>Cek silang memakai pandas (rancangan mengizinkan pengganti Excel).</li>',
         '<li>Notebook, README, infografis, dan angka halaman ini dibuat otomatis dari hasil, dan angka halaman ini diaudit terhadap file hasil.</li></ul></div>',
         '<div class="card"><h4>Perubahan nama dan lokasi file terhadap rancangan</h4>',
         table(["Rancangan", "Realisasi"], [[f"<code>{a}</code>" if a != "(tidak ada)" else "(tidak ada di rancangan)", ", ".join(f"<code>{x}</code>" if "(" not in x else x for x in b.split(", "))] for a, b in renames]) + '</div>')

# ---------------------------------------------------------------- 6. output
chk = lambda rel: (REPO / rel).exists()
outs = [("Dashboard interaktif", "Utama", PART("Sebagian"), "<code>streamlit/app.py</code> (4 halaman) diuji lokal dengan AppTest. Link publik belum ada"),
        ("One-sheet infografik", "Utama", OK("Tercapai"), "<code>infographic.png</code> dan <code>infographic.pdf</code>"),
        ("Database & query SQL", "Utama", OK("Tercapai"), f"<code>ict.duckdb</code> (dibuat ulang, tidak di-commit) dan {I(nsql)} file SQL"),
        ("Skrip anonimisasi & pemuat data", "Utama", OK("Tercapai"), "<code>01_anonymize_load.py</code> dengan checklist anonimisasi; mapping key dibuat terpisah dan dikecualikan dari repositori. Dijalankan pada data simulasi"),
        ("Notebook analisis", "Utama", OK("Tercapai"), "<code>analysis.ipynb</code> dieksekusi tanpa error, mencakup Q1 sampai Q14"),
        ("Laporan temuan & rekomendasi", "Utama", OK("Tercapai"), "<code>README.md</code> dan halaman ini"),
        ("Repositori GitHub", "Utama", PART("Sebagian"), "Struktur, cara menjalankan ulang, dan sampel data anonim siap; berada di branch <code>project-7-build</code>, belum digabung ke <code>main</code>"),
        ("Slide presentasi", "Opsional", NO("Tidak dibuat"), "Opsional, tidak dibuat")]
nU = [o for o in outs if o[1] == "Utama"]
cnt = lambda s: sum(1 for o in nU if s in o[2])
docs = [("index.html", "Halaman rancangan", "index.html"), ("docs/kpi_definitions.md", "Definisi KPI dan aturan skip", "project/docs/definitions.md"), ("docs/data_dictionary.md", "Kamus data 4 tabel", "project/docs/data_dictionary.md"),
        ("docs/anonymization_checklist.md", "Kolom yang dianonimkan", "project/docs/anonymization_checklist.md"), ("data/raw/", "Data mentah (tidak di-commit)", "project/data/raw"), ("data/mapping_key.csv", "Kunci penerjemah (tidak di-commit)", "project/data/mapping_key.csv"),
        ("data/sample/", "Contoh data anonim kecil", "project/data/sample/units.csv"), ("scripts/anonymize_load.py", "Anonimisasi, cleaning, pemuat DuckDB", "project/code/1-data-preparation/python/01_anonymize_load.py"),
        ("outputs/cleaning_log.csv", "Catatan koreksi", "project/results/1-data-preparation/cleaning_log.csv"), ("ict.duckdb", "File database (tidak di-commit)", "project/ict.duckdb"), ("requirements.txt", "Paket Python", "project/requirements.txt"),
        ("sql/", "Query dan view KPI", "project/code/2-analysis/sql/03_views.sql"), ("notebooks/analysis.ipynb", "Analisis Q1 sampai Q14", "project/results/3-presentation/analysis.ipynb"),
        ("outputs/crosscheck.xlsx", "Cek silang (opsional)", "project/results/2-analysis/crosscheck_pandas.csv"), ("outputs/skip_scenarios.csv", "Skenario aturan skip", "project/results/2-analysis/skip_scenarios.csv"),
        ("dashboard/app.py", "Dashboard Streamlit", "project/code/3-presentation/streamlit/app.py"), ("outputs/one_sheet.pdf / .png", "One-sheet infografik", "project/results/3-presentation/infographic.pdf"),
        ("README.md", "Laporan temuan", "README.md"), ("slides/", "Slide (opsional)", "slides")]
stat_doc = lambda rel: PART("Tidak di-commit") if ("duckdb" in rel or "raw" in rel or "mapping" in rel) else (OK("Ada") if chk(rel) else NO("Belum ada"))
rp6 = mk(f'<div class="card"><p><b>Jawaban singkat:</b> {I(cnt("Tercapai"))} dari {I(len(nU))} output Utama tercapai penuh dan {I(cnt("Sebagian"))} sebagian (dashboard belum punya link publik, repositori belum digabung ke main). Slide Opsional tidak dibuat. Semua output dibuat dari data simulasi.</p></div>',
         table(["Output", "Label", "Status", "Bukti"], [[f"<b>{a}</b>", b, c, d] for a, b, c, d in outs]),
         '<div class="card"><h4>Daftar dokumen pada rancangan vs repositori</h4>',
         table(["Dokumen (rancangan)", "Isi", "Lokasi sekarang", "Status"], [[f"<code>{a}</code>", b, f"<code>{c}</code>", stat_doc(c)] for a, b, c in docs]),
         '<p>Data mentah, mapping key, data bersih, dan <code>ict.duckdb</code> tidak di-commit; semuanya dibuat ulang oleh skrip.</p></div>')

# ---------------------------------------------------------------- 7. kesimpulan
crit = [("1. Kesembilan pertanyaan Utama terjawab dengan angka", OK("Tercapai"), "Q1, Q2, Q4, Q5, Q7, Q9, Q10, Q12, Q13 terjawab (bagian 2); empat dengan catatan"),
        ("2. Tidak ada nama, nomor seri asli, atau info pelanggan di repositori; checklist lengkap", OK("Tercapai"), f"{I(ck.lulus.sum())} dari {I(len(ck))} pemeriksaan lulus, {I(leak.kecocokan)} kecocokan di {I(leak.file_dipindai)} file; pada data simulasi, bukan data pabrik"),
        ("3. Angka KPI dari SQL sama dengan hitungan PivotTable Excel", PART("Sesuai + penyesuaian"), f"Sama dengan pandas ({I(cc_n)} pemeriksaan PASS); Excel tidak dipakai"),
        ("4. Setiap unit bisa ditelusuri dari SMT Reflow sampai FCT; unit tidak cocok tercatat", OK("Tercapai"), f"View <code>v_unit</code>; {I(clog.baris.sum())} baris bermasalah di {I(len(clog))} kode log cleaning"),
        ("5. Orang awam membuka dashboard dan menyebut kondisi aman di-skip dalam &lt; 1 menit", PART("Belum diuji"), "Dashboard dibuat tetapi belum di-deploy dan belum diuji ke pembaca sebenarnya"),
        ("6. Checklist standar (pertanyaan bisnis, cleaning, SQL, dashboard ter-deploy, README)", PART("Sebagian"), "Semua ada kecuali dashboard ter-deploy")]
ncr = sum(1 for c in crit if ">Tercapai<" in c[1])
rp7 = mk(
    '<div class="card"><h4>7.1 Hasil analisis: jawaban atas pertanyaan utama</h4>',
    '<p><i>Untuk kondisi produksi apa ICT board 8-layer aman dilewati, dan berapa waktu uji yang bisa dihemat tanpa menambah NG yang baru ketahuan di FCT?</i></p><ul class="tight">',
    f'<li><b>Unit di-skip memang lebih berisiko:</b> NG rate FCT {P(pt.loc["Skip", "ng_rate"], 1)} vs {P(pt.loc["ICT", "ng_rate"], 1)} (risiko relatif {D(pt.loc["Skip", "relative_risk"], 2)}).</li>',
    f'<li><b>Risiko terkumpul di sedikit kondisi:</b> lot IC {worst.nilai} ({P(worst.ng_rate_skip, 1)}) jauh di atas lot lain; beberapa lot punya late NG rate di bawah {P(0.03, 0)} dengan unit cukup.</li>',
    f'<li><b>Aturan skip per kondisi:</b> tiga lot material, batas {P(0.03, 0)}: {P(H.porsi_unit_aman, 0)} unit memenuhi aturan, {D(H.jam_ict_dihemat_per_bulan, 1)} jam ICT dihemat per bulan dengan tambahan {D(H.tambahan_late_ng_per_bulan, 1)} late NG (estimated, simulasi).</li>',
    f'<li><b>Batasan statistik:</b> hanya efek besar yang terdeteksi ({I(n_found)} dari {I(n_planted)} efek ditanam yang cukup datanya); lot yang berdekatan waktu saling memengaruhi.</li></ul></div>',
    '<div class="card"><h4>7.2 Impact</h4><ul class="tight">',
    f'<li><b>Nilai praktis (estimated, simulasi):</b> {D(H.jam_ict_dihemat_per_bulan, 1)} jam ICT dihemat per bulan dapat dialihkan ke unit berisiko; {D(H.late_ng_dihindari_per_bulan, 1)} late NG dihindari bila kapasitas itu dipakai di kondisi berisiko, efek bersih sekitar {D(H.net_late_ng_per_bulan, 1)} late NG lebih sedikit per bulan.</li>',
    '<li><b>Nilai analitis:</b> perbandingan per unit (bukan OK rate harian), CI dan jumlah unit minimum, koreksi untuk banyak perbandingan, dan evaluasi walk-forward mencegah kesimpulan berlebihan dari sampel kecil.</li>',
    '<li><b>Nilai portofolio:</b> prosedur anonimisasi dengan checklist otomatis, database dengan constraint, simulasi dengan kebenaran yang diketahui untuk memeriksa analisis, dan dashboard simulasi aturan skip.</li>',
    '<li><b>Belum terukur:</b> data lini sebenarnya, waktu ICT nyata, dan penerimaan tim lini atas aturan skip.</li></ul></div>')
rp7 += ('<div class="card"><h4>7.3 Success criteria</h4>' + table(["Kriteria (Design Project, bagian 8)", "Status", "Bukti"], [[a, b, c] for a, b, c in crit])
        + f'<p><b>Hasil:</b> {I(ncr)} dari {I(len(crit))} kriteria tercapai, {I(len(crit) - ncr)} sebagian atau belum diuji.</p></div>')
rp7 += mk('<div class="card"><h4>7.4 Rekomendasi</h4><ul class="tight">',
          f'<li>Uji aturan skip hanya untuk lot dengan bukti cukup (minimal {I(MIN_UNITS)} unit di-skip) dan late NG rate rendah; perlakukan lot baru sebagai berisiko sampai bukti terkumpul.</li>',
          f'<li>Mulai dengan aturan yang paling konservatif (batas {P(0.03, 0)}, tiga lot material), pantau late NG rate nyata tiap hari, dan hentikan skip untuk lot yang rate-nya naik.</li>',
          f'<li>Alihkan kapasitas ICT yang dibebaskan ke lot atau kondisi berisiko, terutama lot IC dengan late NG rate tertinggi ({worst.nilai}).</li>',
          '<li>Ulangi seluruh analisis dengan data lini sebenarnya setelah izin penggunaan data dipastikan.</li></ul></div>')
rp7 += mk('<div class="card"><h4>7.5 Saran perbaikan</h4><ul class="tight">',
          '<li>Ganti data simulasi dengan data kerja yang dianonimkan (alur dan checklist sudah siap) dan pastikan izin perusahaan.</li>',
          '<li>Ganti waktu ICT per unit dan volume per bulan dengan angka nyata; tambahkan cek silang ke Excel bila format asal data memakainya.</li>',
          '<li>Pisahkan efek lot dari efek waktu (regresi atau stratifikasi) untuk mengurangi perancu; lanjutkan di analisis penyebab (Project 29).</li>',
          '<li>Deploy dashboard ke Streamlit Community Cloud dan uji ke satu pembaca awam untuk mengisi kriteria 5 dan 6.</li></ul></div>')
rp7 += mk('<div class="card"><h4>7.6 Batasan</h4><ul class="tight">',
          '<li><b>Data adalah simulasi.</b> Angka NG rate, kondisi berisiko, dan dampak menggambarkan simulasi, bukan lini produksi; yang dibuktikan adalah metodenya. Efek yang ditanam dibuat sendiri, jadi temuan tidak boleh dikutip sebagai fakta pabrik.</li>',
          f'<li>Waktu ICT {D(ICT_MIN_PER_UNIT, 0)} menit per unit dan volume {I(UNITS_PER_MONTH)} unit per bulan adalah asumsi rancangan; dampak berlabel estimated.</li>',
          '<li>Pola belum tentu penyebab: lot yang dipakai bersamaan saling menutupi, dan efek kecil tidak terdeteksi pada ukuran data ini.</li>',
          '<li>Unit di-skip dipilih karena kapasitas, bukan acak; selisih NG rate jalur bisa sebagian berasal dari kondisi yang berbeda.</li>',
          '<li>Dashboard belum di-deploy dan kriteria 5 dan 6 belum terpenuhi. Slide presentasi (Opsional) tidak dibuat.</li></ul></div>')

evq = [("1", "rp1", "Data yang didapat", PART("Simulasi"), f"{I(dbc['units'])} unit simulasi, {I(dbc['ict'])} hasil ICT, {I(dbc['fct'])} hasil FCT, 4 tabel, {I(len(resfiles))} CSV hasil"),
       ("2", "rp2", "Business question terjawab?", OK(f"{len(QT)} dari {len(QT)}"), f"Semua terjawab ({npr['Utama']} Utama, {npr['Pendukung']} Pendukung, {npr['Tambahan']} Tambahan); {nw} dengan catatan ({wtxt})"),
       ("3", "rp3", "Dataset sesuai?", PART("Berubah"), "Data kerja asli diganti simulasi; struktur tabel dan anonimisasi sesuai; dua hipotesis terbukti, tiga sebagian"),
       ("4", "rp4", "Tools sesuai?", PART("Sesuai + penyesuaian"), "Excel diganti pandas; Streamlit belum di-deploy"),
       ("5", "rp5", "Alur sesuai?", PART("Sesuai + penyesuaian"), "12 langkah dijalankan; langkah 3 memakai data simulasi"),
       ("6", "rp6", "Output tercapai?", PART(f"{cnt('Tercapai')} penuh, {cnt('Sebagian')} sebagian"), f"{cnt('Tercapai')} dari {len(nU)} output Utama penuh"),
       ("7", "rp7", "Kesimpulan", OK("Tersedia"), f"Hasil analisis, Impact, {len(crit)} kriteria sukses, rekomendasi, saran perbaikan, batasan")]
evq_html = '<div class="scroll"><table class="evq"><tr><th>No</th><th>Pertanyaan evaluasi</th><th>Verdict</th><th>Ringkasan</th></tr>' + "".join(
    f'<tr><td><span class="en">{n}</span></td><td><a href="#{h}">{t}</a></td><td>{v}</td><td>{s}</td></tr>' for n, h, t, v, s in evq) + "</table></div>"
H_ = lambda i, t, sm, body: f'\n<h2 id="rp{i}">{i}. {t}<small>{sm}</small></h2>\n{body}\n'
report = mk(
    '<div class="pane" id="report" data-tab="report" hidden>\n',
    '<div class="callout g"><h4>Report Project versi 2: evaluasi hasil terhadap Design Project</h4><p><b>Catatan penting: data pada project ini adalah simulasi</b> (data kerja asli tidak tersedia); angka menggambarkan simulasi, bukan lini produksi. '
    'Halaman ini disusun sebagai 7 jawaban atas pertanyaan evaluasi. Tabel dan grafik dibuat otomatis dari hasil query SQL (DuckDB) dan analisis statistik. '
    f'Hasil SQL dicek silang dengan pandas ({I(cc_n)} pemeriksaan). Angka pada teks diaudit terhadap file di <code>project/results/</code>: @@AUDIT@@ angka diperiksa tanpa selisih. '
    'Rancangan lengkap ada di tab <a href="#design">Design Project</a>.</p></div>\n',
    evq_html,
    H_(1, "Data yang berhasil didapatkan", "Isi data mentah, tabel di database, dan data hasil analisis", rp1),
    H_(2, "Apakah business question terjawab?", f"{len(QT)} pertanyaan pada Design Project, dijawab dengan data", rp2),
    H_(3, "Apakah dataset sesuai dengan Design Project?", "Perbandingan rancangan dengan realisasi", rp3),
    H_(4, "Apakah tools yang digunakan sesuai?", "Perbandingan rancangan dengan eksekusi", rp4),
    H_(5, "Apakah alur pengerjaan sesuai dengan Design Project?", f"{len(steps)} langkah rancangan vs yang dijalankan", rp5),
    H_(6, "Apakah project output tercapai?", "Output pada Design Project, bagian 7", rp6),
    H_(7, "Kesimpulan", "Hasil analisis, Impact, success criteria, rekomendasi, saran perbaikan, dan batasan", rp7),
    '</div>\n')

# ---------------------------------------------------------------- audit angka
STATIC = {str(i) for i in range(0, 21)} | {f"{i:02d}" for i in range(0, 13)} | {"30", "100", "50", "25", "24", "1E-9", "8", "2026", "29", "95", "60", "12", "22", "1,2", "2,2", "6", "4", "3", "5", "1", "2"}
STATIC |= {f"{a}.{b}" for a in range(1, 10) for b in range(1, 10)}
n_tok, bad = audit(report, STATIC)
manual = [("seluruh CSV hasil terdokumentasi", not miss), ("crosscheck semua PASS", (cc.status == "PASS").all()), ("semua uji constraint ditolak", (ctest.outcome == "ditolak").all()),
          ("semua pemeriksaan konsistensi 0 pelanggaran", (cons.violations == 0).all()), ("checklist anonimisasi lulus semua", bool(ck.lulus.all())), ("pindai kebocoran identitas 0 kecocokan", int(leak.kecocokan) == 0),
          ("jumlah pertanyaan = 14 (9 Utama, 4 Pendukung, 1 Tambahan)", len(QT) == 14 and npr == {"Utama": 9, "Pendukung": 4, "Tambahan": 1}), ("catatan hanya Q4, Q9, Q10, Q11, Q12, Q14", WARN == {4, 9, 10, 11, 12, 14}),
          ("langkah rancangan = 12", len(steps) == 12), ("jumlah pertanyaan unik pada bagian 2 = 14", qn_uniq == list(range(1, 15))), ("NG rate di-skip di atas lolos ICT, Fisher p < 0,001", pt.loc["Skip", "p_fisher"] < 0.001),
          ("efek bersih aturan tiga lot batas 3% positif", H.net_late_ng_per_bulan > 0), ("jumlah unit v_unit = unit bersih", dbc["units"] == dq["unit_setelah_cleaning"]), ("cek perancu: rate turun tanpa lot IC terburuk", confp.ng_rate_tanpa_lot_ic_terburuk < confp.ng_rate_semua)]
assert all(v for _, v in manual), [k for k, v in manual if not v]
if bad:
    print("TOKEN TIDAK TERDAFTAR:", bad)
    sys.exit(1)
report = report.replace("@@AUDIT@@", I(n_tok) + f" (ditambah {I(len(manual))} klaim manual)")

# ---------------------------------------------------------------- pindai identitas asli pada halaman (bila kunci tersedia)
if C.MAPPING_KEY.exists():
    key = pd.read_csv(C.MAPPING_KEY)
    raw_vals = {str(v) for v in key.nilai_asli if len(str(v)) >= 3}
    hits = [v for v in raw_vals if v in report]
    assert not hits, f"identitas asli muncul di Report: {hits[:3]}"

# ---------------------------------------------------------------- rakit halaman
v1 = (HERE / "page_v1.html").read_text(encoding="utf-8")
a = v1.index('<div class="pane" id="report"')
b = v1.index("</main>")
design_pane = v1[v1.index('<div class="pane" id="design"'):a]
nav_old = re.search(r'<nav aria-label="Project navigation">.*?</nav>', v1, re.S).group(0)
btn = lambda t: re.search(rf'<button type="button" class="tab[^"]*" data-t="{t}".*?</button>', nav_old, re.S).group(0)
design_links = re.search(r'<div class="links" data-tab="design">.*?</div>', nav_old, re.S).group(0)
report_links = ('<div class="links" data-tab="report" hidden>' + "".join(f'<a href="#rp{i}">{t}</a>' for i, t in
               enumerate(["Data", "Business Questions", "Dataset", "Tools", "Alur Kerja", "Project Output", "Kesimpulan"], 1)) + "</div>")
nav_new = f'<nav aria-label="Project navigation">{btn("design")}{btn("report")}{design_links}{report_links}</nav>'
css = (HERE / "report.css").read_text(encoding="utf-8")
html = v1[:a] + report + v1[b:]
html = html.replace(nav_old, nav_new)
i = html.rindex("</style>")
html = html[:i] + css + html[i:]
out = REPO / "design-and-report" / "index.html"
out.write_text(html, encoding="utf-8")
assert design_pane == html[html.index('<div class="pane" id="design"'):html.index('<div class="pane" id="report"')], "pane Design berubah"
print(f"index.html {len(html) / 1024:.0f} KB; {n_tok} angka diaudit; {len(manual)} klaim manual; pane Design identik")
