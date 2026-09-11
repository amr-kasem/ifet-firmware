# Five-workflow end-to-end acceptance — Testing environment

**Date:** 2026-09-11 · **Environment:** **Testing only** · **Base:** `app4oXS3Kd5IKWgJ7`

**This is the run that signs off the integration once the UI screens exist.** It requires **no Production
access of any kind** — not write, not schema, not records. Production is read only to prove it was not
touched, through the read-only PAT.

## The path under test

```
Operator -> UI -> ifet-management API -> PostgreSQL -> local lifecycle/result
         -> sync/outbox -> Testing Airtable Raw Data -> read-back verification
```

## Two kinds of step, and the difference is the whole point

| | |
|---|---|
| **AUTOMATED BACKEND ASSERTION** | Runs today, unattended, and asserts what reached PostgreSQL and the Testing base. Already green |
| **HUMAN / UI ACCEPTANCE STEP** | A person driving the real screens. **Cannot run until the UI exists and is not simulated here** |

**Nothing in this document fakes the UI half.** Where a scenario says a person clicks something, that step
is marked and is pending. The assertions beneath it are the same either way — that is the design: when the
UI lands, the human performs the action and the harness asserts the outcome, unchanged.

## Baseline — the backend half is already green

```bash
docker compose -f src/management_service/tests/postgres_harness/docker-compose.yaml up -d
cd src/management_service
M2_DATABASE_URL=postgresql+psycopg2://m2:m2-throwaway-not-a-secret@127.0.0.1:15432/m2 \
python3 -m tests.e2e_acceptance --destroy-db m2 \
    --evidence <dir> --live --run-tag 2026-09-11-A \
    --approved-by "name, date"
```

**Result 2026-09-11: 60/60 assertions passed**, all five workflows in one run —
`baseline-2026-09-11/acceptance-results-20260911T013330Z.json`.

`tests/e2e_acceptance.py` is an **orchestrator, not a framework**: `Report`, the disposable-database
guard, the stack builder, the hierarchy snapshot and every production-safety rule are imported from
`ta7_probe_live`, the same way `ta6_probe_live` imports them. Dry run is the default; `--approved-by` is
mandatory with `--live`; `--destroy-db` must name the database in the URL; the production base is refused
unconditionally.

### Run tagging and data hygiene

Every run takes a **deterministic `--run-tag`** which appears in the job number (`IFET-E2E-<tag>`), every
section name and the operator name (`LABOS-E2E-<tag>`). So one run's records can always be selected
exactly, and a scenario can never pass on a previous run's evidence — the per-type assertions are scoped to
**this run's `Airtable Project ID`**, never to the operator tag alone.

**Nothing is ever deleted.** The probe and the harness only create. Existing synthetic records are
inventoried in `../evidence/ta6-live-probe-2026-09-11/probe-records-inventory.txt`, and whether they are
retained as acceptance evidence or removed after sign-off is a question to the Airtable team (§8 of the
schema requirements document). **It is not a blocker for anything.**

---

## Already covered, and deliberately not repeated on the wire

These run against every commit, in seconds, on PostgreSQL 13. They are **AUTOMATED BACKEND ASSERTIONS** and
this document cites them rather than reproducing them live — none involves Airtable beyond the local
mirror, so a live run would cost a minute each and prove nothing further.

| Requirement | Test |
|---|---|
| Malformed requirement cannot execute | `test_requirement_release.py::TheChainRefusesEveryBrokenShape::test_a_requirement_made_malformed_after_import_stops_the_rig` |
| Missing inward/outward value | `…::test_a_missing_direction_cannot_execute` · `test_inbound_import.py::test_a_blank_design_pressure_is_refused_not_zero` |
| Invalid unit | `…::test_a_unit_mismatch_cannot_execute` · `test_inbound_import.py::test_a_unit_that_contradicts_its_kind_is_refused` |
| Unknown requirement code | `…::test_an_unknown_code_cannot_execute` · `test_inbound_import.py::test_an_unknown_code_routes_nowhere_and_says_so` |
| Kind contradicting its code | `…::test_a_kind_that_contradicts_its_code_cannot_execute` |
| **Unsupported Static Programme** | `test_inbound_import.py::test_an_unsupported_programme_makes_static_load_non_executable` — refused, **not silently run as Full** |
| Blank applicability is Unconfirmed | `test_inbound_import.py::test_blank_applicability_means_unconfirmed_never_not_required` |
| Two disagreeing design pairs | `test_inbound_import.py::test_two_disagreeing_design_pairs_are_refused_not_averaged` |
| A shifted pair is well-formed and still cannot run | `test_requirement_release.py::TheShiftedValueIsCaughtByDisagreementNotByInspection` (4 tests) |
| Asymmetric inward/outward still executes | `…::AsymmetricPairsStillWork` (3 tests) |
| Verification is frozen and immutable | `…::TheVerificationIsAnAssertionSomebodySigned` (6 tests) |

**The one negative case that does belong on the live wire** is the DG14 disagreement (S2b below), because
the value it disagrees with is mirrored from a real Airtable row.

---

## S1 — Import and release ⚠️ prerequisite for Static Load and Cycles

### S1a Import an Airtable job

**Setup:** a job in the Testing base with a protocol carrying all five requirement codes. The harness seeds
its own; a human run can use the fixture or a seeded job.

| | |
|---|---|
| **HUMAN / UI** | Screen 1: pick job → specimen → protocol; choose the rig; review the plan; import |
| **API expected** | `GET /airtable/projects` → `/…/specimens` → `/…/protocols` → `/…/sections`; `POST /airtable/import/plan`; `POST /airtable/import` |
| **DB expected** | one `projects` row with the pair from the section; **6** `static_tests`, **8** `cyclic_tests`, impact and manual tests per code |
| **Airtable expected** | **nothing.** Import writes no Airtable record |
| **PASS** | refused sections are visible with their reasons; a second import of the same mock-up returns the same project |

### S1b Starting before verifying is refused

| | |
|---|---|
| **HUMAN / UI** | Try to start the first static stage without verifying |
| **API expected** | `PUT /projects/{pid}/static_tests/0/start` → **409** |
| **PASS** | refused, and the §3.3 reason is shown to the operator, not swallowed |

### S1c ⚠️ Independent source verification — the disagreement case

| | |
|---|---|
| **HUMAN / UI** | Screen 2. The operator reads the pair **off the proposal** and types it. **Not pre-filled, and the imported pair is not on screen.** Here they deliberately enter a pair that does not match |
| **API expected** | `POST /projects/{pid}/requirement-verification` → **409** |
| **DB expected** | **nothing written** — all six `requirement_verified_*` columns still NULL |
| **PASS** | refused; the message shows **both** pairs; the job is still not executable; **no affordance offered to accept the Airtable value** |

### S1d Verification succeeds and releases the job

| | |
|---|---|
| **HUMAN / UI** | Enter the correct pair, the proposal reference and the verifier's name |
| **API expected** | `POST …/requirement-verification` → **200**, `executable: true`, `code: "released"` |
| **DB expected** | the six columns populated, including `requirement_verified_at` |
| **PASS** | `GET /projects/{pid}/requirement-release` returns `executable: true`; static and cyclic stages now start |

---

## S2 — Static Load (W1)

| | |
|---|---|
| **Setup** | S1 complete and released |
| **HUMAN / UI** | Declare the operator, run stage 0, submit the completed stage with its deflections |
| **API expected** | `PUT /projects/{pid}/static_tests/0/start` `{operator_name}` · `POST /projects/{pid}/static_tests/0/trials` `{operator_name, result, testing_continued, deflections[]}` |
| **DB expected** | one `static_test_results` row, `status = Completed`, with a `requirement_snapshot` containing **`source_verification`** |
| **Airtable expected** | one Raw Data row, `Test Type = "Static Load"`, `Test Result = "Pending"`; **no** `Forced Entry Result`, **no** `ANSI Result`; no deflection data anywhere |
| **PASS** | the row exists with the right type; neither dedicated result field appears; the three withheld measurements are absent |

## S3 — Cycles (W2)

| | |
|---|---|
| **Setup** | as S2 |
| **HUMAN / UI** | Report progress during the run, then submit the completed stage |
| **API expected** | `PUT /projects/{pid}/cyclic_tests/0/update_status` `{current_cycle}` **first** · then `POST /projects/{pid}/cyclic-tests/0/trials` |
| **DB expected** | one `cyclic_test_results` row with `cycles_completed` snapshotted from the reported count |
| **Airtable expected** | one row, `Test Type = "Cycles"`; neither dedicated result field |
| **PASS** | as S2. ⚠️ **Closing the stage without a reported count is correctly refused** — `Cycles Completed` is required at terminal and §6 forbids substituting zero for unknown |

## S4 — Impact (W3) — SMI, LMI D, LMI E

| | |
|---|---|
| **Setup** | a protocol with `IMPACT_SMI` (1 impact) and `IMPACT_LMI` (2 impacts) |
| **HUMAN / UI** | Screen 4. On the SMI test **no family control is offered**; on LMI the operator picks D or E. The operator enters the target velocity. Then one attempt per physical impact: start, record the impact, photograph it, finish, review |
| **API expected** | `PATCH /projects/{pid}/impact-tests/{id}` `{impact_level?, target_velocity}` · `POST …/trials` · `POST /test-results/{aid}/shots` · `POST /shots/{sid}/photos` · `PUT /test-results/{aid}/finish` · `PUT …/verdict` |
| **DB expected** | one attempt per impact; `impact_family` frozen from the requirement code; `impact_level` and `target_velocity` as entered |
| **Airtable expected** | **one row per physical impact.** `Impact Classification` ∈ {`SMI`, `LMI Level D`, `LMI Level E`}; `Target Impact Velocity` a **number** (50.25 stays 50.25); `Impact Number` populated; `Impact Result` present; neither dedicated result field |
| **PASS** | three impacts → three rows, three distinct `LabOS Attempt ID`s; classification correct per test; velocity not truncated |

**Also assert:** finishing an impact attempt with **no photograph** is refused, and an `IMPACT_SMI` test
offers no family control.

## S5 — Forced Entry (W4)

| | |
|---|---|
| **Setup** | a `FORCED_ENTRY` section with `Required Option = "ASTM F588 Grade 40"` |
| **HUMAN / UI** | Screen 3. The grade is **shown, not typed**. Start, add a note and a photograph, finish, then review with a verdict |
| **API expected** | `POST /projects/{pid}/manual-tests/{id}/trials` · `POST /test-results/{id}/photos` · `PUT …/finish` · `PUT …/verdict` |
| **Airtable — at terminal** | `Test Result = "Pending"` **and** `Forced Entry Result = "Pending"`; **`ANSI Result` absent, not blank** |
| **Airtable — at verdict** | `Test Result == Forced Entry Result ==` the verdict in the wire spelling (`Passed`); `ANSI Result` still absent |
| **PASS** | exactly one row throughout; both columns agree at every phase; the other type's column never appears; the photograph is delivered |

## S6 — ANSI Z97.1 (W5)

Identical to S5, mirrored: `Required Option = "Class A"`, `ANSI Result` carries the value, **`Forced Entry
Result` absent at every phase.** Use a `Fail` verdict so `Failed` is exercised on the wire alongside S5's
`Passed`.

## S7 — Abort

| | |
|---|---|
| **HUMAN / UI** | Start an attempt of each of Impact, Forced Entry and ANSI, then abort with a reason |
| **API expected** | `PUT /test-results/{id}/finish` `{abort_reason}` |
| **Airtable expected** | `Test Status = "Abborted"` — **their spelling, sent verbatim** — with the reason in the JSON |
| **PASS** | accepted with **no evidence requirement**; an aborted impact attempt needs no photograph, no classification and no target velocity |

## S8 — Retry and idempotency

| | |
|---|---|
| **Setup** | any completed and reviewed attempt |
| **API expected** | re-send the same verdict payload through the real client |
| **Airtable expected** | the **same record id**, `createdRecords` empty |
| **PASS** | still exactly one row for that `LabOS Attempt ID`; the dedicated result value survives the re-send |

## S9 — Worker outage

| | |
|---|---|
| **HUMAN / UI** | Stop the worker; complete a test through the UI; restart the worker |
| **API expected** | `GET /sync/status` throughout |
| **PASS** | the result is saved locally with the worker down; the queue grows; on restart it drains and the row appears **once**. ⚠️ While the worker is down the headline reads `Sync Failed` with `worker_alive: false` — correct, and not a data problem |

## S10 — Correction

| | |
|---|---|
| **HUMAN / UI** | On a reviewed attempt, choose **Correct** and give a reason |
| **API expected** | `POST /test-results/{id}/correct` `{reason}` → a new, open attempt |
| **Airtable expected** | a **new** row carrying `Corrects Attempt ID` and `Correction Reason`; **the original row is unchanged** |
| **PASS** | both rows present; the original untouched; a retest carries neither field |

## S11 — Write boundary and Production isolation

**AUTOMATED — runs in every harness execution, no human step.**

| | |
|---|---|
| **PASS** | all four hierarchy tables snapshotted before and after: **no writes**. Production schema read before and after and compared **byte for byte**: unchanged, 142 fields, record count unchanged |

---

## Coverage map

| Workflow | Automated today | Awaiting UI |
|---|---|---|
| Static Load | S1b–S1d, S2, S8, S11 | S1a, S2 operator steps |
| Cycles | S1, S3, S8, S11 | S3 operator steps |
| Impact | S4 (all three classifications), S8, S11 | S4 operator steps, S7 abort |
| Forced Entry | S5, S8, S11 | S5 operator steps, S7 abort, S10 correction |
| ANSI Z97.1 | S6, S8, S11 | S6 operator steps, S7 abort |
| Cross-cutting | negative requirement cases (table above), retry, boundary, isolation | S9 worker outage, S10 correction |

**Sign-off is both halves.** The automated column is green today at 60/60. The UI column is
`tc5-ui-developer-handoff-2026-09-11.md` §8, and neither half alone closes TC5.
