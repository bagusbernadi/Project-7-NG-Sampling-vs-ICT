-- Skema ict.duckdb: 4 tabel (units, ict, fct, daily_summary) dihubungkan oleh unit_id. Dijalankan dari folder project/.
DROP VIEW IF EXISTS v_unit;
DROP TABLE IF EXISTS daily_summary;
DROP TABLE IF EXISTS fct;
DROP TABLE IF EXISTS ict;
DROP TABLE IF EXISTS units;

CREATE TABLE units (
    unit_id        VARCHAR PRIMARY KEY CHECK (regexp_matches(unit_id, '^U-[0-9]{4}$')),   -- unit tanpa kode anonim tidak bisa masuk
    reflow_date    DATE NOT NULL,
    shift          VARCHAR NOT NULL CHECK (shift IN ('Shift_1', 'Shift_2', 'Shift_3')),
    smt_op         VARCHAR NOT NULL CHECK (regexp_matches(smt_op, '^Op_[0-9]{2}$')),
    smt_line       VARCHAR NOT NULL CHECK (regexp_matches(smt_line, '^Line_[0-9]$')),
    ic_lot         VARCHAR NOT NULL CHECK (regexp_matches(ic_lot, '^Lot_[A-Z]$')),
    pcb_lot        VARCHAR NOT NULL CHECK (regexp_matches(pcb_lot, '^Lot_[A-Z]$')),
    conn_lot       VARCHAR NOT NULL CHECK (regexp_matches(conn_lot, '^Lot_[A-Z]$')),
    fct_available  BOOLEAN NOT NULL
);
CREATE TABLE ict (                                   -- tidak ada baris = unit di-skip
    unit_id    VARCHAR PRIMARY KEY REFERENCES units (unit_id),
    test_date  DATE NOT NULL,
    result     VARCHAR NOT NULL CHECK (result IN ('OK', 'NG')),
    fail_net   VARCHAR CHECK (fail_net IS NULL OR regexp_matches(fail_net, '^NET_[0-9]{2}$')),
    CHECK ((result = 'NG') = (fail_net IS NOT NULL))
);
CREATE TABLE fct (
    unit_id       VARCHAR PRIMARY KEY REFERENCES units (unit_id),
    test_date     DATE NOT NULL,
    result        VARCHAR NOT NULL CHECK (result IN ('OK', 'NG')),
    vdrop_max_mv  DOUBLE NOT NULL CHECK (vdrop_max_mv >= 0),
    leak_max_ua   DOUBLE NOT NULL CHECK (leak_max_ua >= 0),
    fail_mode     VARCHAR CHECK (fail_mode IS NULL OR fail_mode IN ('VD', 'LC')),
    date_flag     VARCHAR NOT NULL CHECK (date_flag IN ('ok', 'tanggal_sebelum_reflow')),
    CHECK ((result = 'NG') = (fail_mode IS NOT NULL))
);
CREATE TABLE daily_summary (
    date            DATE PRIMARY KEY,
    units_reflowed  INTEGER NOT NULL,
    ict_tested      INTEGER NOT NULL,           -- hasil ICT bertanggal hari itu
    ict_ok_rate     DOUBLE,
    fct_tested      INTEGER NOT NULL,           -- hasil FCT bertanggal hari itu (tanpa date_flag)
    fct_ok_rate     DOUBLE,
    skip_rate       DOUBLE NOT NULL CHECK (skip_rate BETWEEN 0 AND 1)   -- unit di-skip ÷ unit SMT Reflow pada hari itu
);
