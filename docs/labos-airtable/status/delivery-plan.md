# LabOS ↔ Airtable — delivery plan

**Living document — update in place, do not date it or fork it.** Epic IFET-32.
**Authority split:** `../contract/write-contract-v0.4.md` governs *meaning* (identity, envelope, semantics,
concurrency guarantees). This file governs *delivery* (state, sequence, gaps, ownership, asks). On a conflict
about what a field or a guarantee means, the contract wins; on a conflict about what is built or scheduled,
this file wins. Machine-readable mapping: `../contract/field-register.csv` (66 rows).

Dated files belong in `evidence/` and `correspondence/` only — those are point-in-time artifacts. Status,
design and roadmap are one document, this one. Superseded snapshots live in git history, not in the tree.

---

## 0. State — probed 2026-09-06, not asserted

| | |
|---|---|
| **Deployed** | **Nothing of this integration.** `management` runs branch `latest` @ `90f9595` |
| Live alembic head | `3a65a83e0463` — **P1 (`b7c2e9a41d38`) not applied** |
| Live tables | 13, all legacy. No `sync_outbox`, `sync_state`, `test_programmes`, `test_programme_runs`, `at_mirror_*` |
| Live columns matching `airtable\|labos\|attempt` | **zero** |
| Code in the running `report-api` image | `app/{data,domain,utils}` only — **no `app/airtable/`, no `app/sync/`** |
| Live routes | 25; **none** for airtable, sync, runs or import |
| `test_results` rows | 640 |
| `ifet-management` | `feature/labos-airtable` @ `d61f6f5` — all integration code, unmerged, **unwired** (`main.py` imports nothing from `app.sync`) |
| `ifet-firmware` | `feature/labos-firmware-p3` — **docs only**; `git diff --stat dev...HEAD` shows `CLAUDE.md` alone |
| Committed envelope code | `app/airtable/contract.py` pins `CONTRACT_VERSION = "0.3"` — **stale, rewrite to v0.4, do not extend** |

Nothing above is a blocker on its own. Together they mean: **every leg of this integration is greenfield
against production, and no code has ever carried a result end to end.**

---

## 1. The whole data path

```
  Airtable                    LabOS (management)                      Rig (firmware)
  ────────                    ──────────────────                      ──────────────
  4 read tables ──[1]──> at_mirror_* ──[2]──> programme ──[3]──> run (frozen snapshot)
                            60s full read                              │
                                                                       ├──[4]──> work order ──> state_machine
                                                                       │                            │
                                                                       │<─[5]──  stage trial  <─────┤
                                                                       │<─[6]──  manual observation (Impact/FE/ANSI)
                                                                       │
                                                       [7] terminal ──> first review ──> verdict
                                                                       │
  LabOS Raw Data <─[8]── worker <── sync_outbox <────────────────────---┘
        │          [9] photo preview / attachment channel
        └──[10]──> their automation ──> operational views
```

| # | Leg | Spec state | Owner | Where |
|---|---|---|---|---|
| 1 | Airtable → mirror, 60 s full paginated read, staged then atomically published | **Full** | LabOS | contract §7 |
| 2 | mirror → import by permanent IDs → programme / specimen | **Full** | LabOS | contract §2 |
| 3 | requirement → independently verified snapshot → run create | data ✔ · **no capture surface** | LabOS | contract §3.3 · gap **G5** |
| 4 | run → work order the rig can execute | **ABSENT** | LabOS + firmware | gap **G1** |
| 5 | rig → `/trials` → stage trial bound to a run | named, **not designed** | LabOS + firmware | gap **G2** |
| 6 | manual capture — Impact, Forced Entry, ANSI Z97.1 | **one sentence for 3 of 5 types** | LabOS | gap **G3** |
| 7 | terminal → first review → verdict, corrections | **Full** | LabOS | contract §4 |
| 8 | run → outbox → worker → Airtable upsert | **Full — strongest part** | LabOS | contract §7.1 |
| 9 | original photo → persisted preview → attachment | **Full** | LabOS | contract §6 |
| 10 | raw-results row → their automation → operational views | **Full (theirs)** | Airtable | contract §1 |

**Six legs solid, one partial, three holes — and all three holes are on the rig side of a run.** The design
is a complete specification of the Airtable boundary and an incomplete specification of LabOS internals.

---

## 2. Scope and decisions

Five test types: Static Load, Cycles, Impact, Forced Entry, ANSI Z97.1. Backend first. **UI and water
infiltration deferred.** Existing local water behaviour unchanged. Historical attempts excluded from sync;
no name-based backfill.

| | Decision |
|---|---|
| **A1** | One programme run = one Airtable attempt; stages and shots are children. Programme identity is stable across reruns, run identity is always new. `test_programmes` owns the unique tuple; **never put it on the run table** |
| **A2** | Rig `Measured Value` and `Max Pressure Achieved` omitted until sourced and validated. Genuine manual quantities allowed with unit + provenance. **A target is never an achieved value** |
| **A3** | All uncalibrated deflection evidence stays local; outbound `data_quality` explains the omission |
| **A4** | Evidence freezes on termination; first verdict recorded once; a correction is a new immutable row referring to the original |
| **A5** | Incomplete requirements warn at selection; execution requires actual verified values + verifier + time + source reference. **A provenance tag alone cannot release a rig** |
| **A6** | Unsupported codes/shapes/applicability stay visible but non-executable. Codes route work, not names. Legacy `Value` is never parsed |
| **A7** | Keep `ProjectParent` / `Project` in the DB; expose projects/specimens at the API boundary |
| **A8** | Water infiltration excluded from this release |

Settled defaults: `Test Date` = completion; explicit UTC `Testing Start/End Date`; declared operator and
reviewer identity stored separately; originals local, previews in Airtable; no mandatory report link before a
reachable origin exists; a not-required section receives no fabricated passing attempt.

**Standing caution — do not drive a rig from Airtable requirement values.** Their PDF extractor drops blank
cells, so a 60 PSF requirement reads as 9. LabOS cannot detect it; every shifted value is individually
plausible. Contract §10.19.

---

## 3. The build

### 3.1 Local entities

| Entity | Holds |
|---|---|
| `test_programmes` | UUID `labos_test_id`, specimen, primary section + type, active procedure identity |
| `test_programme_runs` | UUID `labos_attempt_id`, programme FK, atomic ordinal, frozen requirement/procedure snapshot, execution + first-review state, source/verification facts, correction FK + reason, `data_quality`, **`completion_source`**, **`identity_assurance`** |
| stage trials | existing static/cyclic trials linked to runs; frozen ordered stage plan; all trials retained, completion trial explicit |
| observations / shots | same run parent; typed common columns (ordinal, location, declared outcome, notes) + versioned detail |
| `at_mirror_{projects,specimens,protocols,sections}` | base + record ID, allowlisted fields, content hash, last successful acquisition, relationship IDs, availability |
| `sync_outbox` | immutable payload, `attempt_seq`, eligible time, lease, `owner_epoch`, delivery state/error |
| `sync_state` | heartbeat, pull/push outcomes, mirror revision |
| `sync_attachments` | artifact ID, full content hash, persisted preview, remote ID/state |

DB checks: run UUID and `(programme_id, attempt_number)` unique; `(base_id, external_project_id)` and
`(base_id, external_specimen_id)` unique on imports; `(specimen_id, primary_section_id, test_type)` unique on
linked programmes; evidence and first review immutable; correction chains acyclic. Parent references and
section references **repeat by design**. New local-only runs default to Excluded until explicitly linked;
historical rows stay Excluded dynamically, never by a hard-coded count such as 640.

### 3.2 API surface

Logical routes; use the existing application's prefix consistently.

| Route | Behaviour |
|---|---|
| `GET /airtable/projects` · `/{rec}/specimens` · `/specimens/{rec}/protocols` · `/protocols/{rec}/sections` | Cached hierarchy reads, including not-yet-imported records; sections carry applicability/support/completeness |
| `POST /airtable/refresh` | Coalesced background refresh — **never a synchronous Airtable dependency** |
| `POST /projects/import` | Import a consistent hierarchy by base + record IDs; idempotent; rejects conflicting parents |
| `POST /specimens/{id}/programmes` | Create or reuse a programme from a supported primary section + type |
| `POST /programmes/{id}/runs` | Create a run after verifying required inputs; idempotency key |
| `GET /runs/{id}` | Snapshot, children, review and delivery status |
| `POST /runs/{id}/stage-trials` | Stage trial with a stable child-event ID; duplicates replay safely |
| `POST /runs/{id}/observations` | Manual observation / impact shot, before termination |
| `POST /runs/{id}/finish` | Terminate on explicit stage completion or abort reason; idempotent |
| `POST /runs/{id}/verdict` | First review once — reviewer, time, rationale; no measurement edits |
| `POST /runs/{id}/corrections` | New attempt copying execution reference, recording corrected facts + reason |
| `POST /runs/{id}/photos` | Persist original + preview before review; later evidence requires a correction |
| `GET /sync/status` · `/sync/queue` · `POST /sync/queue/{id}/retry` | Local state and counts computed at read time, never an Airtable call; retry only re-enables eligibility on the same FIFO worker |

All repeated creates use **persisted** request/event IDs — never a freshly minted attempt ID per HTTP retry.

### 3.3 Concurrency — named mechanisms, not properties to assume

Each fails silently without its mechanism, and **none is observable in a SQLite test**. Contract §7.1.

| Guarantee | Mechanism |
|---|---|
| Sequence allocation | Per-attempt DB sequence or `INSERT … ON CONFLICT` with bounded retry. **`max(seq)+1` fails the operator's save** — inverting the reason the outbox exists |
| Exclusive claim | `SELECT … FOR UPDATE SKIP LOCKED`. One owner is enforced, not a deployment convention |
| Lease at send time | Re-assert immediately before **each** send, not once per batch; skip the entry if lost |
| Fencing token | Monotonic `owner_epoch` per claim; verify before recording an outcome, else **discard**. Without it a stale `terminal` silently overwrites a reviewed verdict — upsert prevents a duplicate *row*, never a stale last write |
| Client deadline | Airtable retry wall-clock bounded well below the lease. Lease and retry budget are **one decision** |

`is_superseded` is evaluated before a request is issued and sees nothing in flight. Wire timestamps are audit
data, never remote compare-and-swap.

### 3.4 Outbound envelope

Upsert on `LabOS Attempt ID` only. Phases: create → terminal → first review, plus a separately tracked
attachment channel. Never `typecast`; never create select options; never clear a cell with `null`; never
substitute `""`/`0`/`false` for unknown. `Schema Version = 0.4`. Canonical pressure **PSF**; length `in`/`mm`;
time `s`; counts `cycles`/`impacts`. `Aborted` goes on the wire as their spelling **`Abborted`**.

**What a completed Static Load or Cycles row actually carries.** A2 omits `Measured Value` and
`Max Pressure Achieved`; A3 quarantines deflection; the rig sends only `deflections[]` plus `recovery`, and
`recovery` is the `recovery_time` config constant (60 s), **not a measurement**. So the published row is
identity, type, status, dates, operator, `Test Result`, notes and JSON — **and no number describing what
physically happened.** That is the decided initial behaviour, and it is the first thing the Airtable team will
ask about when they see M3.

---

## 4. Open gaps — close before M3 can be demonstrated

### G1 · The work order never reaches the rig — **critical**

`grep -niE 'mqtt|state.?machine|test_index|device'` over contract v0.4 **and** the design returns zero hits.
The real path (`ifet-firmware/src/state_machine/state_machine.py:337-372`):

```
UI ──MQTT──> {command:'start', mode:'manual'|'cyclic', project_id, test_index, sensor_id, selectedSensors[]}
           ──> GET /projects/{pid}/static-tests/{idx}  ──>  setpoint = data['pressure'] * ±1
```

The rig's pressure comes from a **`static_tests` row addressed by `project_id` + `test_index`**. A run has no
such address. So §3.3 stores the verified pair on the run and the rig still reads the old
`static_tests.pressure` — the verified-values requirement is enforced on a path the rig never touches.

**Decide:** does run creation materialise/refresh `static_tests`/`cyclic_tests` from the frozen snapshot; who
allocates `test_index`; does the MQTT start payload carry a run ID, or is the binding resolved server-side.

### G2 · Two incompatible callback shapes — **critical**

Firmware posts to `/projects/{pid}/static_tests/{idx}/trials` (`api/api.py:28-45`):

```json
{"deflections": [{"deflection_gauge": 1, "max_deflection": …, "permanent_deflection": …, "recovery": 60}]}
```

No run ID, no stage ID, **no event ID** — so §3.2's "duplicates replay safely" is unachievable through it.
That makes this a firmware change, not a backend adaptation.

**Decide:** firmware calls the new route · backend resolves `(project_id, test_index)` → active run · or both
coexist during transition. An unmapped callback is preserved locally and excluded, never guessed into a run.

### G3 · Three of five test types have no backend at all — **critical**

| Type | Model | Route | Table |
|---|---|---|---|
| Static Load, Cycles | ✔ | ✔ | ✔ |
| Impact | `MissileImpactTest` / `Shot` exist — **read-only, report generation only** (`main.py:992-1009`) | ✗ | ✔ |
| Forced Entry | ✗ | ✗ | ✗ |
| ANSI Z97.1 | ✗ | ✗ | ✗ |

`grep -rniE 'forced.?entry|ansi' app/` hits only the unwired v0.3 `contract.py` and the LaTeX template.
Against that, the plan gives Static/Cycles a full identity design and gives these three one sentence.
Neither Forced Entry nor ANSI appears in any acceptance check as a **capture** case.

### G4 · The firmware leg has no milestone — and this is a regression

The July internal plan — retired into this file, recoverable from git history — tracked it as **gap H** and off-dashboard
items **51** (capture actual & max pressure) and **53** (thread IDs through `start` + result POST), scheduled
for **W2** — which is now. The September design's M0–M7 are entirely backend, Airtable and metrology. Item 51
survived as **M7** under a new name; **item 53 and gap H were lost.** They are G1 and G2 above.

### G5 · No operator surface is in scope

§3.3 requires the operator to enter the verified pair, its reference, verifier and time; the UI is deferred
(A8); M3 is "all five backend workflows". The release is therefore an API with no consumer, and **no rig can
lawfully start until a UI exists**. Acceptable as sequencing — but M5 currently reads as though testing could
begin. State that acceptance is API-level and that "cannot drive a rig" persists past M5.

### G6 · Register and entity drift — small, mechanical

| Item | Problem |
|---|---|
| `completion_source` | Required by contract §2; absent from the register **and** from §3.1's run columns (now added above) |
| `identity_assurance = declared` | Required by contract §4; same absence (now added above) |
| Sync service deployment | Contract §7 says "one container, no public port" and stops — no compose service, env var names, credential source or health policy, in a design that specifies fencing semantics to the sentence |
| Gauge selection | `GAUGE_COUNT` is a snapshotted programme parameter (contract §3.2); firmware takes `selectedSensors[]` live at MQTT start. Never reconciled; a mismatch at start has no defined behaviour |
| `Test Name`, `Abort Reason` | JSON-only by contract §6 — correct, but they have no register row, so a register-vs-JSON diff reports them missing. Note it in the register header |

---

## 5. Milestones

| M | Deliverable | Owner | Exit evidence | Depends on |
|---|---|---|---|---|
| **M1** | Testing Base additions (14 fields) + synthetic linked fixture | LabOS | Schema diff, field IDs per base, asymmetric pair, blank/N-A/unknown examples | — |
| **M2** | **Disposable PostgreSQL harness first**, then local migration and the first vertical flow | LabOS | Two independent worker processes on separate connections; concurrent-enqueue, competing-worker, slow-send, stale-owner green; import → run → finish → worker restart → one Testing Base attempt | — |
| **MF** | **Firmware run/stage association — G1 + G2** | LabOS + firmware | A rig start carries a run identity; a `/trials` callback lands on a known run and stage with a stable event ID; replay is safe; an unmapped callback is excluded, not guessed | M2 identity |
| **M3** | All five backend workflows, review, corrections, evidence — **including G3 capture for Impact / Forced Entry / ANSI** | LabOS | §6 acceptance cases | M2, MF |
| **M4** | Change document with actual implementation results | LabOS | Every planned change marked applied/verified or outstanding | M1–M3 |
| **M5** | Production cutover, separately scheduled | LabOS + IFET | Schema/automation acceptance, migration rehearsal, preflight, agreed window | M4 · window |
| **M6** | Deflection calibration (legacy item 27) | LabOS | Known displacement applied to a gauge, transform identified end to end; `Deflection Value`/`Unit` unquarantined **or** the omission reconfirmed with evidence | bench/rig hardware |
| **M7** | Achieved-pressure acquisition (G4 legacy, off-board item 51) | LabOS | A validated measurement source for `Max Pressure Achieved`, **or** the omission reconfirmed with evidence | bench/rig hardware |

**M2 is one unit** — fixing sequence allocation alone leaves ordering unsafe. **MF is new and gates M3**;
it is the July commitment being re-entered, not new scope. **M6 and M7 are tracked, not blocking**: omission
is the initial-release behaviour, so M1–M5 do not wait for them. Their dependency is bench/rig hardware —
the same dependency the offline `test` node represents, so **one hardware ask covers both**.

P1 is a migration dependency, not a separate prior deployment: since production is still at `3a65a83e0463`,
P1 and the new revision rehearse as **one ordered upgrade** on local PostgreSQL.

---

## 6. Acceptance checks

Grouped; all must pass on **PostgreSQL** — SQLite-only tests are not accepted as proof of any guarantee here.

**Identity (1–4)** · one Attempt ID per run and a new UUID/ordinal on rerun, across six static or eight cyclic
stages · shared job/section IDs repeat and duplicate imports reuse IDs · concurrent creates give distinct
ordinals while replayed creates return the same run · domain save and enqueue are atomic under rollback, and
unlinked/historical attempts never auto-sync.

**Offline and ordering (5–7, 22–25)** · outage, bad token and stopped worker never block a local save ·
lost write response, process kill, lease expiry and concurrent retry preserve per-attempt phase order · a
failed attempt A does not stop unrelated B · **concurrent enqueue** yields distinct `attempt_seq` and neither
domain save fails · **competing workers** never hold the same entry · **slow send** does not release later
entries mid-batch · **stale owner** has its outcome *discarded, not recorded* — verified specifically against
a reviewed verdict, where a late `terminal` must not reset it.

**Review and corrections (8–9)** · first review records identity and time once · a correction is a new row
leaving the original evidence unchanged, is not counted as a physical retest, and never overtakes an
unresolved original identity · roll-ups pick the non-superseded result.

**Evidence (10)** · lost attachment response reconciled without blind append · uncertain presence parked ·
previews and originals carry stable IDs and hashes · a missing preview keeps the attempt visibly Pending/Failed.

**Read cache (11–12)** · >100 records, mid-page error, changed links and concurrent upstream edits cannot
publish a partial hierarchy or erase history · unchanged full reads do not move the mirror revision · only
allowlisted fields enter the mirror, and a renamed field cannot reroute work.

**Requirement safety (13–17)** · unknown code/kind/option, unsupported water or Unconfirmed applicability is
visible but non-executable · missing ≠ zero ≠ N/A, asymmetric magnitudes stay independent, no legacy `Value`
parsing · Airtable-only or merely tagged operator values cannot release a rig · Cycles uses its own verified
pair without a duplicate Static Load row, and parameter rows create no test rows · quarantined deflection and
unavailable rig pressure are rejected in **both** scalars and JSON; targets are never reported as achieved.

**Time (18)** · `Test Date` absent at create, equal to completion at terminal · start/end UTC · corrections
preserve original execution times · Airtable-derived local dates cross midnight and DST correctly.

**Safety and legacy (19–21)** · runtime writes to any hierarchy table or unapproved production target are
refused and schema drift fails loudly · existing legacy reports and local static/cyclic/water behaviour remain
intact, run/stage association is explicit, duplicate stage events replay safely, and missing telemetry can
never imply a passing test · migration rehearsal covers constraints, leases, P1 ancestry and restart.

**Forced Entry and ANSI Z97.1 outcome visibility — decided, not deferred by accident.** `Test Type` and
`Test Result` are both `singleSelect`, so Airtable filters and groups both workflows natively; sub-detail
lives in the JSON. **No dedicated scalar fields are added** — add one only when a named operational report
requires it, not because `Impact Result` happens to exist.

---

## 7. Known deviations in the committed groundwork

`ifet-management` `app/sync/{outbox,state,worker}.py` @ `d61f6f5` predates the contract and is **unwired**, so
every item is latent — nothing has ever passed through it. Listed so nobody mistakes "committed and green"
for "contract-compliant".

| Deviation | Contract |
|---|---|
| `enqueue()` allocates `max(seq)+1` read-then-insert; a collision fails the caller's transaction | §7.1 sequence allocation |
| `claim()` leases without row locking | §7.1 exclusive claim |
| One `leased_until` stamped per batch, then sequential sends | §7.1 lease at send time |
| No `owner_epoch` — a late lander's outcome is recorded | §7.1 fencing token |
| Lease (120 s) unrelated to the client's retry budget | §7.1 client deadline |
| `/sync/status` returns `green/amber/red`, no attachment backlog | §7 status vocabulary |
| 23 tests are SQLite-only | §8 step 5 · acceptance 21–25 |
| `app/airtable/contract.py` pins `CONTRACT_VERSION = "0.3"`, still lists retired Wall/`Test Name`/`Abort Reason` fields and treats `Test Type` as one-option-blocking | v0.4 §§3–6 |

**Closing these is the M2 package.**

---

## 8. Airtable team — what we need, what we owe

**Environments.** Testing `app4oXS3Kd5IKWgJ7` · Production `app0OCunbmuXl7Hc9`.
Read: `IFET Projects` `tblLYcRC7q6Srjfk3` · `Mock-Ups/Specimens` `tblcrGv0WJn6FTTGO` ·
`Tests Protocols` `tblutO1Q8TNC4BLk0` · `Protocol Sections` `tblqpvuJlSdkeS9PS`.
Write: `LabOS Raw Data Table` `tblnc9SsbXU0C0FWh` — **the runtime write allowlist is this table alone.**
Schema-write credentials belong to setup, never to the runtime worker. Tokens stay server-side, out of git and
out of browser-served config.

**Schema is no longer a permission question.** LabOS is authorized to define and add the required fields in
the Testing Base with a documented change register. 66 register rows: 44 BASELINE, 15 PLANNED, 4 CONDITIONAL,
3 OMITTED → **14 actual field additions**.

| Where | Fields |
|---|---|
| `Protocol Sections` (8) | `Requirement Code`, `Requirement Kind`, `Applicability`, `Required Value`, `Required Value Inward`, `Required Value Outward`, `Required Unit`, `Required Option` |
| `LabOS Raw Data Table` (6) | `Corrects Attempt ID`, `LabOS Verdict By`, `LabOS Verdict At`, `LabOS Photos`, `Testing Start Date`, `Testing End Date` |

3 fields stay **OMITTED** by decision — `Max Pressure Achieved`, `Deflection Value`, `Deflection Unit` (no
validated source; M6/M7). 4 URL fields are **CONDITIONAL** — publish only after the origin is validated
reachable. 1 row (`attempt_seq`) is local queue metadata and is **never created in Airtable**.

**What genuinely still needs them:**

1. **Automations** — test UUID linkage, completion dates, review-only verdicts, correction supersession,
   parameter-row exclusion. Production's existing automations are **not** assumed compatible merely because
   the fields exist; that is verified before cutover.
2. **The extractor defect** — unresolved on their side. Until fixed, execution uses independently verified
   values, and the 8 new `Protocol Sections` fields are what make that verification expressible.
3. **Blast-radius report** — including jobs already marked tested, since a shifted value already reached a
   Passed/Completed record.

**What we owe them:** `../correspondence/airtable-team-questions-2026-09-06.md` — a **planned-change notice,
not a permission request. Still NOT SENT.** Report what is designed, then actual changes with evidence after
implementation. `correspondence/sent/` is append-only; never edit an artifact they already hold.

---

## 9. Asks to IFET — operational

| Ask | Why | When |
|---|---|---|
| **Bench/rig hardware access** | The single dependency shared by M6 and M7. One ask covers both | Before M6/M7 scheduling |
| **The `test` node back online** (offline since ~2026-07-24) | The only non-production rig. Without it, MF and the sync path are first exercised on production — **the largest unmanaged risk in the plan** | Before MF |
| **A maintenance window** for the M5 cutover | Nothing is deployed; the change set grows with every milestone | M5 |
| **Weight behind the extractor fix** | A safety item, not a schedule item, and the only true gate on running from Airtable requirements | Now |
| **A decision on already-reported results** | A shifted value reached a Passed record. Quality/business call, not an engineering one | On the blast-radius report |

**Dates.** The original 2026-07-23 → 2026-08-27 window closed, and the 2026-10-09 pilot target has **not been
revalidated** against MF, G3 or the hardware dependency. No new date is committed here until M1 and M2 land;
quoting the October target as live would be a fabrication.

---

## 10. Operating rules

- **Nothing is deployed and nothing gets deployed as an experiment.** No rebuild, recreate or restart of a
  production container to try something out. No `docker cp` hot patches — deploy means rebuild from a clean
  checkout. Rehearse off-production, inform the deployment owner, agree a window.
  Runbook: `../runbooks/p0-p1-deploy-2026-08-28.md` — **its §2 is the decision point**; whether
  `alembic_version` has moved decides whether the deploy can happen that day.
- **The node is ground truth for migrations, not the repo.** Migrations were gitignored and the chain lived
  only on `management`. Check `SELECT * FROM alembic_version;` on the live database before any schema work.
- **On a node, only history/index-only git is safe** — `add`, `commit`, `update-index --skip-worktree`.
  Never `checkout`, `reset --hard`, `stash pop`, `clean`, `pull` or `merge`: those rewrite the live
  bind-mounted config a running container is reading.
- **Branch off `dev` in a clone; never edit on a device.** A dirty node worktree is an incident signal.
- **Secrets never enter git**, and never `deployment/config/config.json` or `src/ifet_ui_react/config.json` —
  both are served to the browser.
- **Docs:** this file is the delivery authority and is edited in place. New dated `.md` files belong in
  `evidence/` and `correspondence/` only. Close open items in the authoritative document first, then views.
- **Commits** are authored `gad <abdulrahmanashraf.gad@gmail.com>` with no assistant attribution.
