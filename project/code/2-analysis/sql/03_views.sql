-- View KPI (satu rumus untuk semua halaman). Jalur: ICT = ada baris ICT, Skip = tidak ada. Late NG = di-skip lalu NG di FCT.
CREATE OR REPLACE VIEW v_unit AS
SELECT u.*, CASE WHEN i.unit_id IS NULL THEN 'Skip' ELSE 'ICT' END AS path, i.result AS ict_result, i.fail_net,
       f.result AS fct_result, f.fail_mode, f.vdrop_max_mv, f.leak_max_ua, f.test_date AS fct_date, i.test_date AS ict_date, f.date_flag,
       (f.result = 'NG') AS fct_ng, (i.unit_id IS NULL AND f.result = 'NG') AS late_ng
FROM units u LEFT JOIN ict i USING (unit_id) LEFT JOIN fct f USING (unit_id);

CREATE OR REPLACE VIEW v_path AS                       -- Q2, Q7: NG rate FCT per jalur (hanya unit dengan hasil FCT)
SELECT path, count(*) AS n_fct, sum(fct_ng::INT) AS n_ng, avg(fct_ng::INT) AS ng_rate
FROM v_unit WHERE fct_result IS NOT NULL GROUP BY path;

CREATE OR REPLACE VIEW v_mode AS                       -- Q3: mode NG per jalur
SELECT path, fail_mode, count(*) AS n FROM v_unit WHERE fct_result = 'NG' GROUP BY ALL;

CREATE OR REPLACE VIEW v_cross AS                      -- Q6: hasil ICT x hasil FCT (unit yang di-ICT)
SELECT ict_result, fct_result, count(*) AS n FROM v_unit WHERE path = 'ICT' AND fct_result IS NOT NULL GROUP BY ALL;

CREATE OR REPLACE VIEW v_cond AS                       -- Q4, Q5: n dan NG per kondisi, nilai, jalur
WITH l AS (
    SELECT 'ic_lot' AS cond, ic_lot AS val, path, fct_ng FROM v_unit WHERE fct_result IS NOT NULL
    UNION ALL SELECT 'pcb_lot', pcb_lot, path, fct_ng FROM v_unit WHERE fct_result IS NOT NULL
    UNION ALL SELECT 'conn_lot', conn_lot, path, fct_ng FROM v_unit WHERE fct_result IS NOT NULL
    UNION ALL SELECT 'smt_op', smt_op, path, fct_ng FROM v_unit WHERE fct_result IS NOT NULL
    UNION ALL SELECT 'smt_line', smt_line, path, fct_ng FROM v_unit WHERE fct_result IS NOT NULL
    UNION ALL SELECT 'shift', shift, path, fct_ng FROM v_unit WHERE fct_result IS NOT NULL)
SELECT cond, val, path, count(*) AS n, sum(fct_ng::INT) AS n_ng FROM l GROUP BY ALL;

CREATE OR REPLACE VIEW v_daily AS                      -- Q1: sumber tabel daily_summary
WITH d AS (SELECT DISTINCT reflow_date AS date FROM units UNION SELECT test_date FROM ict UNION SELECT test_date FROM fct WHERE date_flag = 'ok')
SELECT d.date,
       (SELECT count(*) FROM units u WHERE u.reflow_date = d.date) AS units_reflowed,
       (SELECT count(*) FROM ict i WHERE i.test_date = d.date) AS ict_tested,
       (SELECT avg((result = 'OK')::INT) FROM ict i WHERE i.test_date = d.date) AS ict_ok_rate,
       (SELECT count(*) FROM fct f WHERE f.test_date = d.date AND f.date_flag = 'ok') AS fct_tested,
       (SELECT avg((result = 'OK')::INT) FROM fct f WHERE f.test_date = d.date AND f.date_flag = 'ok') AS fct_ok_rate,
       coalesce((SELECT avg((path = 'Skip')::INT) FROM v_unit v WHERE v.reflow_date = d.date), 0) AS skip_rate
FROM d;
