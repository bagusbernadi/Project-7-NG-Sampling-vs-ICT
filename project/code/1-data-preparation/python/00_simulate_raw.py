"""Membuat DATA SIMULASI berformat 'file kerja mentah' (dengan identitas palsu) untuk board 8-layer.

Data kerja asli tidak tersedia, jadi project ini memakai simulasi bersemi (seed) dengan efek yang diketahui.
Parameter ada di bawah dan di docs/simulation_spec.md. Semua nama, nomor seri, dan pelanggan di sini adalah karangan.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

rng = np.random.default_rng(C.SEED)

from common import (BASE_P_SMT, BG_FCT_NG, DEFECT_FCT_NG, ICT_DETECT, ICT_FALSE_NG, P_SKIP, P_VD_BG, P_VD_SMT, REPAIR_FAIL, RR)  # noqa: E402  (parameter ground truth ada di common.py)

IC_LOTS = [f"IC-24-{x}{i + 1:02d}" for i, x in enumerate("ABCDEFGHIJ")]
PCB_LOTS = [f"PCB-{x}-{n}" for x, n in zip("KLMNOPQR", (301, 305, 312, 318, 322, 327, 331, 336))]
CONN_LOTS = [f"CN-{x}-{n}" for x, n in zip("STUVW", ("0198", "0201", "0204", "0209", "0215"))]
OPS = {"Day": ["Agus Pratama", "Siti Rahma"], "Evening": ["Budi Santoso", "Dewi Lestari"], "Night": ["Eko Wijaya", "Fajar Nugroho"]}
SHIFT_ORDER = ["Day", "Evening", "Night"]
CUSTOMER, MODEL = "PT Contoh Elektronik Nusantara", "MB-8L-REV3"
assert "IC-24-C03" in IC_LOTS and "PCB-M-312" in PCB_LOTS and "CN-U-0204" in CONN_LOTS


def blocks(lots, days, lo, hi, weights=None):
    """Urutan lot per hari: lot berganti setiap lo..hi hari."""
    out, d = [], 0
    while d < days:
        L = int(rng.integers(lo, hi + 1))
        lot = rng.choice(lots, p=weights)
        out += [lot] * L
        d += L
    return out[:days]


dates = [d for d in pd.date_range(C.START_DATE, periods=C.N_WEEKS * 7) if d.dayofweek != 6]
nd = len(dates)
w_ic = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 0.0]); w_ic /= w_ic.sum()         # lot J hanya muncul sebagai uji coba kecil (di bawah)
ic_day, pcb_day, cn_day = blocks(IC_LOTS, nd, 3, 6, w_ic), blocks(PCB_LOTS, nd, 4, 8), blocks(CONN_LOTS, nd, 6, 10)
ic_day = [x for x in ic_day]
trial_day = int(rng.integers(8, nd - 8))                                          # satu hari ada uji coba lot J (~25 unit)

units = []
uid = 0
for di, d in enumerate(dates):
    n = int(rng.poisson(C.UNITS_PER_DAY))
    for k in range(n):
        shift = SHIFT_ORDER[min(2, int(3 * k / max(n, 1)))] if rng.random() < 0.9 else str(rng.choice(SHIFT_ORDER))
        op = rng.choice(OPS[shift])
        line = rng.choice(["SMT-LINE-1", "SMT-LINE-2"], p=[0.55, 0.45])
        ic = ic_day[di]
        if di == trial_day and k < 25:
            ic = "IC-24-J10"
        pcb, cn = pcb_day[di], cn_day[di]
        p = BASE_P_SMT
        for key, val in (("ic_lot", ic), ("pcb_lot", pcb), ("conn_lot", cn), ("smt_op", op), ("smt_line", line), ("shift", shift)):
            p *= RR[key].get(val, 1.0)
        units.append((uid, d, shift, op, line, ic, pcb, cn, min(p, 0.9)))
        uid += 1
U = pd.DataFrame(units, columns=["uid", "reflow_date", "shift", "smt_op", "smt_line", "ic_lot", "pcb_lot", "conn_lot", "p_smt"])
N = len(U)
defect = rng.random(N) < U.p_smt.values
skipped = rng.random(N) < U["shift"].map(P_SKIP).values
tested = ~skipped
ict_ng = np.zeros(N, bool)
ict_ng[tested & defect] = rng.random((tested & defect).sum()) < ICT_DETECT
ict_ng[tested & ~defect] = rng.random((tested & ~defect).sum()) < ICT_FALSE_NG
caught = tested & defect & ict_ng
fct_ng = np.zeros(N, bool)
smt_fail = defect & ~caught & (rng.random(N) < DEFECT_FCT_NG)                    # cacat lolos (di-skip atau lolos ICT) -> NG FCT
fct_ng |= smt_fail
fct_ng |= ict_ng & (rng.random(N) < REPAIR_FAIL)                                 # setelah perbaikan masih NG
bg = rng.random(N) < BG_FCT_NG
fct_ng |= bg
vd = np.where(smt_fail | (ict_ng & fct_ng & ~bg), rng.random(N) < P_VD_SMT, rng.random(N) < P_VD_BG)

# ---- tabel mentah dengan identitas palsu
nums = []
seen = set()
while len(nums) < N:
    v = int(rng.integers(10**7, 10**8))
    if v not in seen:
        seen.add(v)
        nums.append(v)
serial = [f"SN24{v}" for v in nums]
assert len(set(serial)) == N
raw_u = pd.DataFrame({"serial_no": serial, "customer": CUSTOMER, "board_model": MODEL, "reflow_date": U.reflow_date.dt.strftime("%Y-%m-%d"),
                      "shift": U["shift"], "smt_operator": U.smt_op, "smt_line": U.smt_line, "ic_lot": U.ic_lot, "pcb_lot": U.pcb_lot, "conn_lot": U.conn_lot,
                      "station_ict": "ICT-STN-04", "station_fct": "FCT-STN-11"})
ti = np.where(tested)[0]
ict_date = U.reflow_date.values[ti] + pd.to_timedelta(rng.choice([0, 1], p=[0.8, 0.2], size=len(ti)), unit="D").values
raw_i = pd.DataFrame({"serial_no": np.array(serial)[ti], "test_date": pd.to_datetime(ict_date).strftime("%Y-%m-%d"), "result": np.where(ict_ng[ti], "NG", "OK"),
                      "fail_net": np.where(ict_ng[ti], rng.choice(["NET_VCC_3V3", "NET_VDD_CORE", "NET_GND_L4", "NET_IO_12"], size=len(ti)), "")})
fct_date = U.reflow_date.values + pd.to_timedelta(rng.choice([1, 2, 3, 4], p=[0.25, 0.4, 0.25, 0.1], size=N), unit="D").values
vdm = np.where(fct_ng & vd, rng.normal(88, 12, N), rng.normal(36, 6, N)).clip(5)
lkm = np.where(fct_ng & ~vd, rng.normal(18, 4, N), rng.normal(4, 1.2, N)).clip(0.2)
raw_f = pd.DataFrame({"serial_no": serial, "test_date": pd.to_datetime(fct_date).strftime("%Y-%m-%d"), "result": np.where(fct_ng, "NG", "OK"),
                      "vdrop_max_mv": vdm.round(1), "leak_max_ua": lkm.round(2), "fail_mode": np.where(fct_ng, np.where(vd, "VD", "LC"), "")})
# pengotor yang realistis (untuk Q13)
miss = rng.choice(N, int(0.012 * N), replace=False)                                # unit belum/tidak punya hasil FCT
raw_f = raw_f[~raw_f.serial_no.isin(np.array(serial)[miss])]
dup = raw_i.sample(7, random_state=1)                                              # baris ICT ganda (uji ulang tercatat dua kali)
raw_i = pd.concat([raw_i, dup]).sort_values(["serial_no", "test_date"]).reset_index(drop=True)
bad_dates = raw_f.sample(6, random_state=2).index                                  # FCT bertanggal sebelum reflow (salah ketik)
raw_f.loc[bad_dates, "test_date"] = (pd.to_datetime(raw_f.loc[bad_dates, "test_date"]) - pd.Timedelta(days=12)).dt.strftime("%Y-%m-%d")
raw_f = pd.concat([raw_f, pd.DataFrame({"serial_no": ["SN24-ORPHAN-01", "SN24-ORPHAN-02"], "test_date": "2026-03-05", "result": "OK", "vdrop_max_mv": 35.0, "leak_max_ua": 4.0, "fail_mode": ""})])
raw_u.to_csv(C.RAW_DIR / "raw_units.csv", index=False)
raw_i.to_csv(C.RAW_DIR / "raw_ict.csv", index=False)
raw_f.to_csv(C.RAW_DIR / "raw_fct.csv", index=False)
truth = pd.DataFrame({"serial_no": serial, "defect_smt": defect, "p_smt": U.p_smt.values.round(5), "skipped": skipped})
truth.to_csv(C.RAW_DIR / "truth_hidden.csv", index=False)                           # kebenaran simulasi; hanya untuk validasi (tidak dipakai analisis)
print(f"unit {N}, skip {skipped.mean():.1%}, defect SMT {defect.mean():.2%}, FCT NG {fct_ng.mean():.2%}, hari {nd}")
