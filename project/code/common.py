"""Pengaturan bersama untuk semua skrip. Semua jalur relatif terhadap folder project/."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # folder project/
DATA = ROOT / "data"
RAW_DIR = DATA / "raw"                                 # data mentah SIMULASI dengan identitas palsu (tidak di-commit)
CLEAN_DIR = DATA / "clean"                             # data anonim bersih (tidak di-commit)
SAMPLE_DIR = DATA / "sample"                           # contoh kecil data anonim (di-commit)
MAPPING_KEY = DATA / "mapping_key.csv"                 # kunci penerjemah (tidak pernah di-commit)
DB_PATH = ROOT / "ict.duckdb"
CODE = ROOT / "code"
SQL_PREP = CODE / "1-data-preparation" / "sql"
SQL_ANALYSIS = CODE / "2-analysis" / "sql"
RES_PREP = ROOT / "results" / "1-data-preparation"
RES_ANALYSIS = ROOT / "results" / "2-analysis"
RES_PRESENT = ROOT / "results" / "3-presentation"
DOCS_DIR = ROOT / "docs"
for _d in (RAW_DIR, CLEAN_DIR, SAMPLE_DIR, RES_PREP, RES_ANALYSIS, RES_PRESENT):   # dibuat otomatis pada repo bersih
    _d.mkdir(parents=True, exist_ok=True)

# Sumber data: SIMULASI (data kerja asli tidak tersedia). Lihat docs/simulation_spec.md
DATA_VERSION = "sim-1"
ACCESS_DATE = "25 Oktober 2026"                        # tanggal pembuatan data simulasi

# Simulasi
SEED = 20261027
N_WEEKS = 8                                            # 8 minggu, Senin sampai Sabtu
UNITS_PER_DAY = 154                                    # rata-rata (asumsi: setara 4.000 unit per bulan)
START_DATE = "2026-03-02"                              # tanggal "asli" simulasi (digeser saat anonimisasi)
DATE_SHIFT_DAYS = -137                                 # selisih tetap pada anonimisasi (bagian dari kunci, tidak dipakai analisis)

# Parameter simulasi (ground truth; dipakai 00_simulate_raw.py dan ditampilkan di Report)
BASE_P_SMT = 0.012                       # peluang unit punya cacat SMT pada kondisi acuan
RR = {"ic_lot": {"IC-24-C03": 6.0, "IC-24-G07": 2.2, "IC-24-J10": 6.0},
      "pcb_lot": {"PCB-M-312": 2.0},
      "conn_lot": {"CN-U-0204": 1.3},
      "smt_op": {"Budi Santoso": 2.2},          # operator fiktif
      "smt_line": {"SMT-LINE-2": 1.3},
      "shift": {"Night": 1.2}}
P_SKIP = {"Day": 0.30, "Evening": 0.45, "Night": 0.70}   # peluang skip per shift (keterbatasan kapasitas)
ICT_DETECT = 0.85                        # peluang ICT menangkap cacat SMT
ICT_FALSE_NG = 0.012                     # unit baik yang NG di ICT (lalu dicek ulang)
DEFECT_FCT_NG = 0.90                     # cacat SMT yang tidak tertangkap berujung NG di FCT
REPAIR_FAIL = 0.08                       # unit NG-ICT yang masih NG di FCT setelah perbaikan
BG_FCT_NG = 0.008                        # NG FCT dari penyebab di luar SMT (tidak terkait ICT)
P_VD_SMT, P_VD_BG = 0.60, 0.30           # proporsi mode NG voltage drop


# Definisi analisis (lihat docs/definitions.md)
MIN_UNITS = 30                                         # kondisi < 30 unit tidak dijadikan dasar aturan skip
WARMUP_DAYS = 6                                        # hari awal hanya mengumpulkan bukti; aturan dievaluasi mulai hari berikutnya (walk-forward)
THRESHOLDS = [0.02, 0.03, 0.04, 0.05]                  # batas late NG rate yang diterima untuk aturan skip
ICT_MIN_PER_UNIT = 3.0                                 # menit ICT per unit (ASUMSI, angka contoh rancangan)
UNITS_PER_MONTH = 4000                                 # volume per bulan (ASUMSI, angka contoh rancangan)
CONDITIONS = ["ic_lot", "pcb_lot", "conn_lot", "smt_op", "smt_line", "shift"]


def result(name):
    for d in (RES_PREP, RES_ANALYSIS, RES_PRESENT):
        p = d / name
        if p.exists():
            return p
    raise FileNotFoundError(name)


def chdir_root():
    os.chdir(ROOT)
