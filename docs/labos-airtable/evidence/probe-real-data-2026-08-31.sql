\pset pager off
\echo === 0. alembic head + row counts ===
SELECT (SELECT version_num FROM alembic_version)      AS alembic_head,
       (SELECT count(*) FROM projects)                AS projects,
       (SELECT count(*) FROM static_tests)            AS static_tests,
       (SELECT count(*) FROM cyclic_tests)            AS cyclic_tests,
       (SELECT count(*) FROM test_results)            AS test_results,
       (SELECT count(*) FROM deflections)             AS deflections,
       (SELECT count(*) FROM infiltration_tests)      AS infiltration,
       (SELECT count(*) FROM missile_impact_tests)    AS missile_tests,
       (SELECT count(*) FROM shots)                   AS shots;

\echo === 1. design pressure — is it really two independent numbers? ===
SELECT count(*)                                            AS projects,
       min(inward_design_pressure)                         AS min_inward_psf,
       max(inward_design_pressure)                         AS max_inward_psf,
       min(outward_design_pressure)                        AS min_outward_psf,
       max(outward_design_pressure)                        AS max_outward_psf,
       count(*) FILTER (WHERE inward_design_pressure
                           <> outward_design_pressure)     AS asymmetric_pairs
FROM projects;

\echo === 2. static tests — pressure factors, real pressures, hold durations ===
SELECT pressure_factor, type, count(*) AS n,
       min(pressure) AS min_psf, max(pressure) AS max_psf,
       min(duration) AS min_hold_s, max(duration) AS max_hold_s
FROM static_tests GROUP BY pressure_factor, type ORDER BY 1,2;

\echo === 3. cyclic tests — the real low/high range and cycle counts ===
SELECT type, cycles, count(*) AS n,
       min(low_pressure) AS min_low_psf, max(high_pressure) AS max_high_psf
FROM cyclic_tests GROUP BY type, cycles ORDER BY 1, 2 DESC;

\echo === 4. deflections — three measurements per gauge, real inch ranges ===
SELECT count(*) AS rows, count(DISTINCT deflection_gauge) AS distinct_gauges,
       min(max_deflection) AS min_max_defl_in, max(max_deflection) AS max_max_defl_in,
       min(permanent_deflection) AS min_perm_in, max(permanent_deflection) AS max_perm_in,
       min(recovery) AS min_recovery_in, max(recovery) AS max_recovery_in
FROM deflections;
SELECT DISTINCT deflection_gauge FROM deflections ORDER BY 1;

\echo === 5. infiltration — units that are NOT in our vocabulary ===
SELECT type, count(*) AS n,
       min(pressure) AS min_psf, max(pressure) AS max_psf,
       min(duration) AS min_dur, max(duration) AS max_dur,
       min(leakage) AS min_leak, max(leakage) AS max_leak
FROM infiltration_tests GROUP BY type ORDER BY 1;

\echo === 6. missile impact — kg, m/s, m2 ===
SELECT missile, count(*) AS n, min(missile_weight) AS min_kg, max(missile_weight) AS max_kg
FROM missile_impact_tests GROUP BY missile ORDER BY 1;
SELECT count(*) AS shots, min(velocity) AS min_mps, max(velocity) AS max_mps,
       min(area) AS min_area, max(area) AS max_area,
       count(*) FILTER (WHERE result) AS passed
FROM shots;

\echo === 7. retests — how often does one test have more than one attempt? ===
SELECT 'static' AS kind, count(*) AS tests_with_attempts,
       count(*) FILTER (WHERE n > 1) AS tests_retested, max(n) AS max_attempts
FROM (SELECT static_test_id, count(*) AS n FROM static_test_results GROUP BY 1) s
UNION ALL
SELECT 'cyclic', count(*), count(*) FILTER (WHERE n > 1), max(n)
FROM (SELECT cyclic_test_id, count(*) AS n FROM cyclic_test_results GROUP BY 1) c;

\echo === 8. test_results — pass/fail shape as actually stored ===
SELECT result, count(*) AS n, min(trial_number) AS min_trial, max(trial_number) AS max_trial
FROM test_results GROUP BY result ORDER BY 1;

\echo === 9. live column types of test_results (what P1 will extend) ===
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'test_results' ORDER BY ordinal_position;
