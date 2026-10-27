"""Anonimisasi data mentah (simulasi), cleaning, pencocokan unit antar tabel (Q12, Q13), dan penulisan data bersih."""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

for f in ("raw_units.csv", "raw_ict.csv", "raw_fct.csv"):
    if not (C.RAW_DIR / f).exists():
        sys.exit(f"File tidak ada: {C.RAW_DIR / f}\nJalankan dulu 00_simulate_raw.py (data kerja asli tidak ada; project memakai simulasi).")
U, I, F = (pd.read_csv(C.RAW_DIR / f"raw_{n}.csv") for n in ("units", "ict", "fct"))
rng = np.random.default_rng(C.SEED + 1)
n_u0, n_i0, n_f0 = len(U), len(I), len(F)

# ---------------------------------------------------------------- anonimisasi: kode acak, mapping key terpisah
keys = []


def code_map(values, fmt, kind):
    vals = sorted(set(values))
    order = rng.permutation(len(vals))                       # urutan kode acak: tidak bisa ditebak dari urutan nilai asli
    m = {v: fmt(int(o)) for v, o in zip(vals, order)}
    keys.extend((kind, k, c) for k, c in m.items())
    return m


m_unit = code_map(U.serial_no, lambda i: f"U-{i + 1:04d}", "serial_no")
m_op = code_map(U.smt_operator, lambda i: f"Op_{i + 1:02d}", "operator")
letters = iter("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
lot_vals = sorted(set(U.ic_lot) | set(U.pcb_lot) | set(U.conn_lot))
perm = rng.permutation(len(lot_vals))
m_lot = {v: f"Lot_{chr(65 + int(p))}" for v, p in zip(lot_vals, perm)}
keys.extend(("lot", k, c) for k, c in m_lot.items())
m_line = code_map(U.smt_line, lambda i: f"Line_{i + 1}", "line")
m_shift = {"Day": "Shift_1", "Evening": "Shift_2", "Night": "Shift_3"}
keys.extend(("shift", k, c) for k, c in m_shift.items())
m_net = code_map(I.fail_net.dropna(), lambda i: f"NET_{i + 1:02d}", "net")
shift = pd.Timedelta(days=C.DATE_SHIFT_DAYS)
sd = lambda s: (pd.to_datetime(s) + shift).dt.strftime("%Y-%m-%d")

units = pd.DataFrame({"unit_id": U.serial_no.map(m_unit), "reflow_date": sd(U.reflow_date), "shift": U["shift"].map(m_shift), "smt_op": U.smt_operator.map(m_op),
                      "smt_line": U.smt_line.map(m_line), "ic_lot": U.ic_lot.map(m_lot), "pcb_lot": U.pcb_lot.map(m_lot), "conn_lot": U.conn_lot.map(m_lot)})
ict = pd.DataFrame({"unit_id": I.serial_no.map(m_unit), "test_date": sd(I.test_date), "result": I.result, "fail_net": I.fail_net.map(m_net)})
fct = pd.DataFrame({"unit_id": F.serial_no.map(m_unit), "test_date": sd(F.test_date), "result": F.result, "vdrop_max_mv": F.vdrop_max_mv, "leak_max_ua": F.leak_max_ua, "fail_mode": F.fail_mode.replace("", np.nan)})
assert units.unit_id.notna().all() and units.unit_id.is_unique
orph_i, orph_f = int(ict.unit_id.isna().sum()), int(fct.unit_id.isna().sum())

# ---------------------------------------------------------------- cleaning dan pencocokan (log)
log = []
fct = fct.dropna(subset=["unit_id"])
log.append(("C1", "Baris FCT dengan nomor seri yang tidak ada di tabel unit (yatim)", orph_f, "dibuang", "Tidak bisa ditelusuri ke SMT Reflow"))
ict = ict.dropna(subset=["unit_id"])
log.append(("C2", "Baris ICT dengan nomor seri yang tidak ada di tabel unit (yatim)", orph_i, "dibuang", "Tidak ada"))
dup = ict.duplicated(["unit_id"], keep="first")
log.append(("C3", "Unit dengan lebih dari satu baris ICT (uji ulang tercatat dua kali, hasil sama)", int(dup.sum()), "dipertahankan satu baris (pertama)", "Satu unit satu hasil ICT"))
ict = ict[~dup]
dupf = fct.duplicated(["unit_id"], keep="first")
log.append(("C4", "Unit dengan lebih dari satu baris FCT", int(dupf.sum()), "tidak ada" if dupf.sum() == 0 else "dipertahankan satu baris", "-"))
fct = fct[~dupf]
nofct = ~units.unit_id.isin(fct.unit_id)
log.append(("C5", "Unit tanpa hasil FCT (belum diuji atau data hilang)", int(nofct.sum()), "unit dipertahankan, dikeluarkan dari perhitungan NG rate", "Dihitung terpisah (bukan OK dan bukan NG)"))
rd = units.set_index("unit_id").reflow_date
bad = pd.to_datetime(fct.test_date).values < pd.to_datetime(fct.unit_id.map(rd)).values
fct["date_flag"] = np.where(bad, "tanggal_sebelum_reflow", "ok")
log.append(("C6", "Tanggal FCT lebih awal dari tanggal SMT Reflow (tidak mungkin)", int(bad.sum()), "hasil dipakai, ditandai di date_flag, dikeluarkan dari hitungan harian", "Tanggal salah ketik; hasil unit tetap valid"))
bi = pd.to_datetime(ict.test_date).values < pd.to_datetime(ict.unit_id.map(rd)).values
log.append(("C7", "Tanggal ICT lebih awal dari tanggal SMT Reflow", int(bi.sum()), "tidak ada" if bi.sum() == 0 else "ditandai", "-"))
m = ict.merge(fct, on="unit_id", suffixes=("_ict", "_fct"))
inc = int((pd.to_datetime(m.test_date_ict) > pd.to_datetime(m.test_date_fct)).sum() - (m.date_flag == "tanggal_sebelum_reflow").sum())
log.append(("C8", "Tanggal ICT lebih akhir dari tanggal FCT pada unit yang sama (di luar C6)", inc, "tidak ada" if inc == 0 else "ditandai", "Unit melewati ICT sebelum FCT"))
cl = pd.DataFrame(log, columns=["kode", "masalah", "baris", "keputusan", "catatan"])
cl.to_csv(C.RES_PREP / "cleaning_log.csv", index=False)
assert inc == 0 and int(dupf.sum()) == 0 and int(bi.sum()) == 0

units["fct_available"] = units.unit_id.isin(fct.unit_id)
units = units.sort_values("unit_id").reset_index(drop=True)
units.to_csv(C.CLEAN_DIR / "units.csv", index=False)
ict.sort_values("unit_id").to_csv(C.CLEAN_DIR / "ict.csv", index=False)
fct.sort_values("unit_id").to_csv(C.CLEAN_DIR / "fct.csv", index=False)
pd.DataFrame(keys, columns=["jenis", "nilai_asli", "kode"]).to_csv(C.MAPPING_KEY, index=False)   # TIDAK di-commit (.gitignore)

# sampel kecil anonim yang di-commit (300 unit pertama menurut tanggal SMT Reflow)
samp = units.sort_values(["reflow_date", "unit_id"]).head(300)
samp.to_csv(C.SAMPLE_DIR / "units.csv", index=False)
ict[ict.unit_id.isin(samp.unit_id)].sort_values("unit_id").to_csv(C.SAMPLE_DIR / "ict.csv", index=False)
fct[fct.unit_id.isin(samp.unit_id)].sort_values("unit_id").to_csv(C.SAMPLE_DIR / "fct.csv", index=False)

# ---------------------------------------------------------------- checklist anonimisasi (Q12)
raw_vals = {str(v) for v in (set(U.serial_no) | set(U.smt_operator) | set(U.smt_line) | set(U.ic_lot) | set(U.pcb_lot) | set(U.conn_lot) | set(I.fail_net.dropna())
                              | {U.customer[0], U.board_model[0], U.station_ict[0], U.station_fct[0]}) if str(v)}


def leaks(paths):
    n = 0
    for p in paths:
        t = Path(p).read_text(encoding="utf-8", errors="ignore")
        n += sum(1 for v in raw_vals if v in t)
    return n


outs = [*C.CLEAN_DIR.glob("*.csv"), *C.SAMPLE_DIR.glob("*.csv")]
mapping_ignored = "project/data/mapping_key.csv" in (C.ROOT.parent / ".gitignore").read_text()
raw_ignored = "project/data/raw/" in (C.ROOT.parent / ".gitignore").read_text()
chk = [("Nomor seri diganti kode acak U-0001 dan seterusnya", bool(units.unit_id.str.fullmatch(r"U-\d{4}").all()), f"{len(units)} unit, kode unik"),
       ("Operator diganti Op_01 dan seterusnya", bool(units.smt_op.str.fullmatch(r"Op_\d{2}").all()), f"{units.smt_op.nunique()} operator"),
       ("Lot (IC, PCB, konektor) diganti Lot_A dan seterusnya", bool(pd.concat([units.ic_lot, units.pcb_lot, units.conn_lot]).str.fullmatch(r"Lot_[A-Z]").all()), f"{len(set(pd.concat([units.ic_lot, units.pcb_lot, units.conn_lot])))} lot"),
       ("Lini dan shift diganti kode netral (Line_n, Shift_n)", bool(units.smt_line.str.fullmatch(r"Line_\d").all() and units["shift"].str.fullmatch(r"Shift_\d").all()), "tanpa nama mesin"),
       ("Nama net ICT diganti NET_nn", bool(ict.fail_net.dropna().str.fullmatch(r"NET_\d{2}").all()), f"{ict.fail_net.nunique()} net"),
       ("Kolom pelanggan, model produk, dan nama stasiun dihapus", not ({"customer", "board_model", "station_ict", "station_fct"} & (set(units) | set(ict) | set(fct))), "kolom dihapus dari tabel bersih"),
       ("Tanggal digeser dengan selisih tetap", (pd.to_datetime(units.reflow_date).min() - pd.to_datetime(U.reflow_date).min()).days == C.DATE_SHIFT_DAYS and units.reflow_date.min() != U.reflow_date.min(), f"selisih tetap {abs(C.DATE_SHIFT_DAYS)} hari"),
       ("Nilai asli tidak muncul di data bersih dan sampel (pindai teks)", leaks(outs) == 0, f"{len(raw_vals)} nilai asli dipindai di {len(outs)} file, {leaks(outs)} kecocokan"),
       ("Mapping key tidak masuk repositori (.gitignore)", mapping_ignored, "<code>project/data/mapping_key.csv</code> diabaikan Git"),
       ("Data mentah tidak masuk repositori (.gitignore)", raw_ignored, "<code>project/data/raw/</code> diabaikan Git")]
pd.DataFrame(chk, columns=["pemeriksaan", "lulus", "detail"]).to_csv(C.RES_PREP / "anonymization_checklist.csv", index=False)
assert all(c[1] for c in chk), [c[0] for c in chk if not c[1]]

# ---------------------------------------------------------------- profil dan kualitas data
tested = units.unit_id.isin(ict.unit_id)
dq = {"unit_baris_mentah": n_u0, "ict_baris_mentah": n_i0, "fct_baris_mentah": n_f0, "unit_setelah_cleaning": len(units), "unit_di_ict": int(tested.sum()), "unit_di_skip": int((~tested).sum()),
      "unit_dengan_fct": int(units.fct_available.sum()), "unit_tanpa_fct": int(nofct.sum()), "hari_produksi": int(units.reflow_date.nunique()),
      "tanggal_awal_anonim": units.reflow_date.min(), "tanggal_akhir_anonim": units.reflow_date.max(),
      "unit_ict_tanpa_fct": int((tested & nofct).sum()), "ict_ng": int((ict.result == "NG").sum()), "fct_ng": int((fct.result == "NG").sum()),
      "fct_ng_tanpa_mode": int(((fct.result == "NG") & fct.fail_mode.isna()).sum()), "fct_ok_dengan_mode": int(((fct.result == "OK") & fct.fail_mode.notna()).sum())}
pd.DataFrame({"ukuran": dq.keys(), "nilai": dq.values()}).to_csv(C.RES_PREP / "data_quality.csv", index=False)
prof = []
for name, t in (("units", units), ("ict", ict), ("fct", fct)):
    for c in t.columns:
        prof.append((name, c, str(t[c].dtype), int(t[c].isna().sum()), int(t[c].nunique())))
pd.DataFrame(prof, columns=["tabel", "kolom", "tipe", "kosong", "unik"]).to_csv(C.RES_PREP / "profile_columns.csv", index=False)
print({k: v for k, v in dq.items() if "unit" in k or "fct" in k}, "| checklist", sum(c[1] for c in chk), "/", len(chk))
