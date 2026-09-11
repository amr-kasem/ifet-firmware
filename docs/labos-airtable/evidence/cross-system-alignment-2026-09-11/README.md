# Cross-system alignment pass — 2026-09-11

**Type:** evidence (read-only). **Scope:** the final contract ↔ production-runtime alignment before the
Airtable package is sent and before any deployment work begins.

**Nothing was mutated.** No Airtable write, no schema write, no deployment, no production data change. Every
node command was a read; every Airtable call was a Meta-API or record read through the read-only path.

Each fact below carries how it was established:

| Tag | Meaning |
|---|---|
| **LIVE** | read from the running system today |
| **PROD DATA** | read from current production data today |
| **CONFIG** | read from deployed configuration today |
| **HISTORICAL** | evidence from an earlier session, not re-read today |
| **UNVERIFIED** | not established; the check that would establish it is named |

---

## 1. The one finding that changes a deployment step

### The live Alembic head has moved: `3a65a83e0463` → `7ed2a670841e` — **LIVE**

Every document in this repository records the live head as `3a65a83e0463`. It is not that any more.

```
SELECT version_num FROM alembic_version;   ->  7ed2a670841e
```

`7ed2a670841e_auto_generated_migration.py` on the node — **CONFIG**:

```
Revision ID: 7ed2a670841e
Revises: 3a65a83e0463
Create Date: 2026-09-09 12:30:32.551799
def upgrade() -> None: pass
```

An empty no-op, minted on the node on 2026-09-09 by the **deployed** `startup.sh`, which still calls
`command.revision(..., autogenerate=True)` at every container start (line 25 of the deployed copy —
**CONFIG**). The repository's `startup.sh` stopped doing that on 2026-08-23; the node is on `latest`
@ `90f9595`, which predates the fix.

It is `.gitignore`d on the node (`.gitignore:17 **/alembic/versions/*`) — **CONFIG** — so it exists nowhere
in git.

**Why it matters.** The release chain's first migration `b7c2e9a41d38` also declares
`down_revision = '3a65a83e0463'`. With both files present, Alembic sees **two heads branching from
`3a65a83e0463`**, `alembic upgrade head` refuses, and `startup.sh` treats a migration failure as fatal — so
`report-api` would never serve. This is exactly Case B of `runbooks/p0-p1-deploy-2026-08-28.md` §2, and the
2026-09-11 runbook did not carry it. It does now (§1.2a).

Revision-file inventory — **LIVE**:

| | |
|---|---|
| On the node | 30 files |
| Tracked in the repo | 39 files |
| **Node-only** | **`7ed2a670841e`** — exactly one |
| Repo-only | the 10 release migrations `b7c2e9a41d38` … `e2b9d4c70a15` |

**This is not a contract or implementation defect.** It is a deployment prerequisite, and it will recur:
every restart of the currently deployed stack mints another one. Re-read the head at the window, not from
this file.

---

## 2. Deployed production state

### 2.1 `management` — **LIVE**, 2026-09-11 14:27–14:32 UTC

| | |
|---|---|
| Branch / HEAD | `latest` @ `90f9595` — worktree clean |
| Containers | 7, up 2 days |
| Alembic head | **`7ed2a670841e`** (§1) |
| Tables | **13**, all legacy. No `at_mirror_*`, no `sync_outbox`, no `sync_state` |
| `test_results` columns | **5** — `id`, `trial_number`, `result`, `note`, `image_path`. **None** of the P1 attempt columns |
| `projects` columns | **6** — `id`, `name`, `parent_id`, `device_id`, `inward_design_pressure`, `outward_design_pressure`. No `airtable_*`, no `gauge_count`/`impact_count`, no `requirement_verified_*` |
| Code in the running image | `app/{data,domain,utils}` + `main.py`. **No `app/airtable/`, no `app/sync/`** |
| Routes served | **25** paths, read from the running app's own `/openapi.json`. None for airtable, sync, import, manual tests, impact tests, corrections, verdicts or photographs |

**So: nothing of this integration is deployed, confirmed from the running system rather than asserted.**

### 2.2 Current production data — **PROD DATA**

| | 2026-09-07 (recorded) | **2026-09-11 (read today)** |
|---|---|---|
| `test_results` | 640 | **655** |
| `static_test_results` | — | 305 |
| `cyclic_test_results` | — | 350 |
| `missile_impact_tests` | 39 | **39** |
| `shots` | 114 | **114** |
| `deflections` | 1082 | **1124** |
| `projects` · `project_parents` | 79 · 32 | **80 · 33** |
| `infiltration_tests` | 37 | **37** |

- **Production is still running tests.** 15 new attempts since 2026-09-07, all static/cyclic. Impact has not
  moved. The P1 backfill is not row-count-bound — it is
  `UPDATE test_results SET airtable_sync_state='Excluded' WHERE airtable_sync_state IS NULL` — so growth is
  harmless to it.
- `result`: 380 NULL · 191 true · 84 false.
- `deflections`: **473** seed rows (`Gauge N`) · **651** firmware rows (`1-1`…`2-8`).
- `recovery` is **60 on 651 rows** — the `recovery_time` config constant, not a measurement. The remaining
  distinct values (1.14, 1.22, 7.07, 7.93, 2.35 …) are seed data.
- `missile_impact_tests.missile` holds free text: `2x4 Lumber`, `Large Missile`, `Steel Ball`. Nothing may
  infer an impact classification from these — the runbook's `backfilled = 0` assertion is what enforces it.

### 2.3 The rigs — **LIVE**

| | `system-1` | `system-2` |
|---|---|---|
| Branch / HEAD | `dev` @ **`b009bca`** (= `dev` head) | `dev` @ **`5048d9a`** (4 behind) |
| Worktree | one untracked backup dir | clean |
| Containers | 3, up 23 h | 4, up 5 h (incl. the standalone turbo controller) |
| `states/idle.py` in the running container | `010df207669c17b525d363065496753b` | `74ac7969d211024abf5a0754065df5fa` |

The two md5s match `git show b009bca:src/state_machine/states/idle.py` and
`git show 5048d9a:…` exactly. **The valve-3 RELIEF fix is on `system-1` only** — unchanged since the
2026-08-31 audit.

`system-1`'s split config is also unchanged — **CONFIG**:

```
state_machine_service -> deployment/config/config1-site-b.json
valves_service        -> deployment/config/config1-site-b.json
serial_service        -> deployment/config/config1.json
```

`system-2` mounts `config2.json` on all three, plus `ifet-turbo-controller/deployment/config/config.json`.

**Neither rig carries `feature/labos-firmware-p3`.** The MF run-binding change is not deployed, which is
what the release identity says: no rig code changes in this release.

### 2.4 Deflection acquisition is still down fleet-wide — **LIVE**

Both SICK masters unreachable **right now**, 2026-09-11 14:32 UTC:

```
sick_gateway-1 -> 10.1.10.229  : [Errno 113] No route to host, every port
sick_gateway-2 -> 10.1.10.85   : [Errno 113] No route to host, every port
```

Agreeing from the data side — **PROD DATA**: attempts 647–655 have **zero** deflection rows; 641–646 have
five each; 35 of the 55 attempts above id 600 have none.

It changes nothing this release publishes — deflections are withheld by decision — but a static or cyclic
test run today produces almost no local measurement evidence.

### 2.5 The `test` node — **LIVE**

`ssh … testnode-ssh.at.remote.it:33003` → **Connection refused.** Still offline. There is no non-production
rig to rehearse a rig-affecting change on. This release changes no rig code.

---

## 3. Airtable — both bases, read-only

`python -m app.airtable.preflight --env ../../.env`, 2026-09-11 — **LIVE**:

```
1.  The 19 added fields, in Testing        19 of 19 present and correctly typed
1a. The withdrawn three                    3 withdrawn, 10 fields on the read allowlist
1b. Decided but not yet created            none owed
2.  Production still has none of them      none of the 22 guarded fields are in production
    production 142 fields · testing 164 fields · delta 22
3.  the generated CSV against both bases   164 rows checked, 0 disagree
4.  the fixture                            present · 75 protocol sections · 7 requirement codes
5.  the document's counts                  164 = 17 read + 40 write-bound + 107 ignored
    33 always · 4 conditional · 3 withheld (Deflection Unit, Deflection Value, Max Pressure Achieved)

All claims in the change document hold against both live bases.  Safe to send.
```

Choices and precision are asserted, not just types: `Impact Classification` = `SMI · LMI Level D ·
LMI Level E`; `Forced Entry Result` / `ANSI Result` = `Pending · Passed · Failed · Inconclusive` (**their**
spelling); `Target Impact Velocity` precision **2**.

---

## 4. Generated artifacts — regenerated, byte-identical

| Artifact | Generator | Result |
|---|---|---|
| `contract/interface-schema.csv` | `app/airtable/interface_schema.py`, from both live bases + the register | **171 rows, identical** |
| `correspondence/LabOS-Airtable-Production-Schema-Changes-2026-09-11.csv` and `evidence/testing-base-changes-2026-09-06/production-change-spec.csv` | `make-production-change-spec.py` — one generator, two paths | **164 rows, both identical** |

Field-level cross-check of the requirements document against the generated CSV — type, options/precision and
direction, per field: **19/19 ADD and 3/3 DO-NOT-PROMOTE agree, no mismatches.** The register's 19 `APPLIED`
rows are exactly the CSV's 19 `ADD` rows, and its 3 `DEPRECATED` rows exactly the 3 withheld.

Per-table arithmetic, recomputed from the CSV:

| Table | production today | ADD | withheld | production after | LabOS reads | LabOS writes |
|---|---|---|---|---|---|---|
| Protocol Sections | 16 | 8 | 3 | 24 | 10 | 0 |
| LabOS Raw Data Table | 30 | 11 | 0 | 41 | 1 | 40 |
| IFET Projects | 35 | — | — | 35 | 2 | 0 |
| Mock-Ups/Specimens | 13 | — | — | 13 | 2 | 0 |
| Tests Protocols | 8 | — | — | 8 | 2 | 0 |
| Walls & Positions · Wall Scheduling · Back Charges | 8 · 19 · 13 | — | — | same | 0 | 0 |
| **Total** | **142** | **19** | **3** | **161** | **17** | **40** |

Every count in §1 of the requirements document reproduces exactly.

---

## 5. Gates

| Gate | Result |
|---|---|
| `app/airtable/check_register.py` | **PASS** — 76 register rows; 16 IN rows = 16 allowlisted; 9 forbidden fields unread; 69 fields correctly typed against the captured schema; **19 APPLIED rows = 19 preflight assertions**; 55 local sources resolve; 62 business-I/O traces resolve; the approval document matches the code it is generated from |
| `app/airtable/preflight.py` | **PASS**, both live bases (§3) |
| `interface_schema.py` regeneration | **identical** |
| `make-production-change-spec.py` regeneration | **identical** |
| Management suite, PostgreSQL 13 harness | **433 passed · 108 subtests · 0 failed**, run per file |
| `TheCommittedApiContractIsCurrent` | **PASS** — `openapi.json` matches the running app |
| Five-workflow acceptance baseline | **60/60**, `../../testing/baseline-2026-09-11/` — production schema byte-identical before and after |

### The harness needs more connections than it has

Running the whole suite in **one** pytest process fails 112 tests with

```
psycopg2.OperationalError: FATAL: sorry, too many clients already
```

Every one of them passes when its file is run on its own, and one of them passes when run alone. It is
PostgreSQL's default `max_connections = 100` against a suite that has grown, **not** a code regression.
Run the suite per file, or raise `max_connections` on the disposable harness, until that is addressed.

---

## 6. Fields with no producer — checked, not assumed

`grep` over `app/` for an assignment to each attempt column, excluding the model declaration:

**Nothing in the application writes** `measured_value`, `unit`, `max_pressure_achieved`, `deflection_value`,
`deflection_unit`, `impact_result`, `photo_links`, `excel_file_link`, `report_link`, `test_rig`,
`labos_version`, `required_value` or `required_unit` on an attempt.

Consequences, and each is a decision rather than an oversight:

| Field | Airtable state | What actually happens |
|---|---|---|
| `Max Pressure Achieved`, `Deflection Value`, `Deflection Unit` | exist in production | **`envelope.build` refuses them outright**, in the JSON as well as the columns. Withheld by A2/A3 |
| `Measured Value`, `Unit` | exist in production | columns exist, **no writer**, so the key is never emitted. `Unit` is required *whenever* `Measured Value` is sent, which never happens |
| `Photos`, `Excel File Link`, `LabOS Report Link` | exist in production | same: CONDITIONAL, no writer, never emitted |
| `Impact Result` | exists in production | **produced** — `mapping._impact_result` derives it from the shot when the column is empty |
| `Cycles Completed`, `Test Rig` | no column; ride in the JSON | `Cycles Completed` **is** produced (`attempts.capture_cycles_completed`); `test_rig` is not, but `result_detail` puts `project.device_id` in `test.rig` |

**None of the 19 fields being requested is in that list.** Every one of them has a real producer or a real
consumer — §7.

---

## 7. The 19 requested fields, producer by producer — code-verified

### Protocol Sections — 8 IN fields, all with a real consumer

| Field | Consumer |
|---|---|
| `Requirement Code` | `mirror.SECTION_FIELDS` → `requirements.KIND_BY_CODE` · `importer.LOCAL_TYPE_BY_CODE` · `release.PAIR_CODES` |
| `Requirement Kind` | `requirements.validate` — must agree with the code |
| `Applicability` | `requirements.applicability_of` — blank is `Unconfirmed`, never `Not Required` |
| `Required Unit` | `requirements.UNITS_BY_KIND` · `release.typed_pair` refuses anything but PSF for a pair |
| `Required Value` | `importer.plan` — `gauge_count`; impact counts **accumulated**, not assigned |
| `Required Value Inward` / `Outward` | `importer.prefill_values` → the 14 derived stages · `release.evaluate` |
| `Required Option` | `importer` — the manual test's grade/class, and the static programme gate |

### LabOS Raw Data Table — 11 OUT fields, all with a real producer

| Field | Producer | Phase |
|---|---|---|
| `Testing Start Date` | `attempts.begin` | create |
| `Testing End Date` | `attempts.mark_terminal` / `complete_rig_trial` | terminal |
| `LabOS Verdict By` · `LabOS Verdict At` | `PUT /test-results/{id}/verdict` | verdict |
| `Corrects Attempt ID` | `POST /test-results/{id}/correct` → `attempts.as_correction` | create |
| `Impact Number` | `attempt.trial_number`, Impact only | create |
| `Impact Classification` | `MissileImpactTest.impact_classification`, a property over the stored family and level — **no column and no API field sets the string** | terminal |
| `Target Impact Velocity` | `missile_impact_tests.target_velocity`, operator-entered | terminal |
| `Forced Entry Result` · `ANSI Result` | `test_results.test_result`, projected and gated by `Test Type` | terminal + verdict |
| `LabOS Photos` | `POST …/photos` → `sync/artifacts.py`, its own FIFO channel | attachment |

`Impact Classification` and `Target Impact Velocity` are both in
`contract.REQUIRED_BY_TEST_TYPE[IMPACT]`, so a completed Impact attempt cannot be published without them.
`Forced Entry Result` and `ANSI Result` are likewise required on their own types, on `Completed` only, so an
aborted attempt is never stranded by them.

---

## 8. Management ↔ firmware, as the two repositories actually stand

| | |
|---|---|
| Deployed callback body | `{"deflections":[{deflection_gauge, max_deflection, permanent_deflection, recovery}]}` — four fields, nothing else |
| `feature/labos-firmware-p3` adds | `run` and `event_id`, **omitted entirely when absent**, plus a 3× retry with an unchanged body and the `turbo_id` crash fix |
| Management's `Static/CyclicTestResultCreateSchema` | `deflections` (+ optional `operator_name`, `result`, `testing_continued`, `note`). **No `run`, no `event_id`** — `grep` for them over `app/main.py` returns zero |
| Net effect today | `bind_run` finds no `run` on the GET response, so the binding is `None` and the body is byte-identical to production's. **Compatible in both directions, by design** |

DG1 and DG2 are therefore accurately described in the plan: firmware half landed, backend half open. The
backend half is not required by anything in this release.

### The rig types need an operator, and only a screen can give them one — **rollout limitation**

`attempts.complete_rig_trial` terminates a rig-posted stage only when an operator is known, from the callback
or from `test.operator_name` declared at run start. Firmware's `Api` class has **no** `start_static_test`
method at all, and its `start_cyclic_test` sends **no body**. So for Static Load and Cycles the operator can
only come from a UI call to one of:

```
PUT /projects/{project_id}/static_tests/{static_test_index}/start   body {"operator_name": "…"}
PUT /projects/{project_id}/cyclic_tests/{cyclic_test_index}/start   body {"operator_name": "…"}
```

Both take `RunStartSchema`, and the body is **optional** — omitting it starts the run and leaves the attempt
uncompletable. Both are `IMPLEMENTED ON FEATURE BRANCH` and `VERIFIED IN TESTING`; neither is
`DEPLOYED TO PRODUCTION`, and the static one does not exist in the deployed route set at all.

**This belongs to the existing Static Load and Cycles run screens, not to TC5.** TC5's five screens are job
picker · requirement release · manual test (Forced Entry + ANSI) · impact · sync status, and its §9 says in
terms that no second interface for Static Load and Cycles is to be built — screen 2 is the only *new* screen
those workflows need. What the existing screens need is one field on a call they already make.

Without it the attempt stays `In Progress`: the `create` phase publishes, the terminal phase never does, the
Airtable row sits at `In Progress` / `Pending`, and the refusal is visible in `GET /sync/failures` rather
than silent. That is the designed degradation, and it is why TC5 gates the *usable* release rather than the
deployable one.

`PUT /projects/{id}/static_tests/{idx}/start` does not exist in the 25 deployed routes, so nothing calls it
today — **LIVE**.

---

## 9. Still UNVERIFIED, and the exact check for each

| Item | Check |
|---|---|
| The live Alembic head **at the deployment window** | `SELECT * FROM alembic_version;` — it changes on every restart of the current stack. §1 |
| Whether any further node-only revision has appeared | `ls …/alembic/versions/*.py` on the node, diffed against `git ls-files` |
| Which production jobs the DG14 gate will stop | the runbook's §2.1 query. Not run here: it needs `projects.airtable_project_id`, a column the live database does not have yet |
| Whether an Airtable roll-up counts rows as tests | question §6 of the requirements document. Theirs to answer |
| Whether the SICK masters return | §2.4, re-read at the window |

---

## 10. Commands (all read-only)

```bash
# management
git rev-parse --abbrev-ref HEAD; git rev-parse HEAD; git status --short
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}'
docker exec ifet-management-db-1 sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "SELECT version_num FROM alembic_version;" -c "\dt" -c "\d test_results" -c "\d projects"'
ls ~/ifet-management/src/management_service/alembic/versions/*.py
cat ~/ifet-management/src/management_service/alembic/versions/7ed2a670841e_*.py
git check-ignore -v src/management_service/alembic/versions/7ed2a670841e_*.py
docker exec ifet-management-report-api-1 sh -c 'ls /app/app'
docker logs --tail 8 --timestamps ifet-management-sick_gateway-{1,2}-1

# rigs
git rev-parse --abbrev-ref HEAD; git rev-parse --short HEAD; git status --short
docker exec <state_machine> md5sum /app/states/idle.py
docker inspect --format '{{range .Mounts}}{{.Source}}=>{{.Destination}} {{end}}' <container>

# off-node
python3 app/airtable/check_register.py
python3 -m app.airtable.preflight --env ../../.env
python3 -m app.airtable.interface_schema --out <tmp> --register <register> --env ../../.env
python3 evidence/testing-base-changes-2026-09-06/make-production-change-spec.py
docker compose -f src/management_service/tests/postgres_harness/docker-compose.yaml run --rm tests \
  python -m pytest tests/<file>.py -q -p no:cacheprovider
```
