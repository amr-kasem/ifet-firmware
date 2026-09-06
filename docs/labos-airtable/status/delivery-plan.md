# LabOS ↔ Airtable — delivery plan

**Living document — update in place, do not date it or fork it.** Epic IFET-32.
**Authority split:** `../contract/write-contract-v0.4.md` governs *meaning* (identity, envelope, semantics,
concurrency guarantees). This file governs *delivery* (state, sequence, gaps, ownership, asks). On a conflict
about what a field or a guarantee means, the contract wins; on a conflict about what is built or scheduled,
this file wins. Machine-readable mapping: `../contract/field-register.csv` (73 rows).

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
| `ifet-management` | `feature/labos-airtable` @ `2e535e6` — all integration code, unmerged, **unwired** (`main.py` imports nothing from `app.sync`). `d61f6f5` plus the schema-apply and interface-schema tools |
| `ifet-firmware` | `feature/labos-firmware-p3` — docs, **plus the MF firmware change and the isolated simulation harness** (`simulation/mf_harness/`, `src/fake_sick_service/`). Not deployed to any rig |
| Committed envelope code | `app/airtable/contract.py` pins `CONTRACT_VERSION = "0.3"` — **stale, rewrite to v0.4, do not extend** |
| **Testing Base schema** | **M1 applied 2026-09-06** — 14 fields added, 142 → 156. Evidence and reasons: `../evidence/testing-base-changes-2026-09-06/` |
| Production Base schema | Unchanged, 142 fields. The 14 above are exactly the production delta (M5) |

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
| 4 | run → work order the rig can execute | **decided + firmware landed**; backend half open | LabOS + firmware | gap **G1** |
| 5 | rig → `/trials` → stage trial bound to a run | **decided + firmware landed**; backend half open | LabOS + firmware | gap **G2** |
| 6 | manual capture — Impact, Forced Entry, ANSI Z97.1 | **one sentence for 3 of 5 types** | LabOS | gap **G3** |
| 7 | terminal → first review → verdict, corrections | **Full** | LabOS | contract §4 |
| 8 | run → outbox → worker → Airtable upsert | **Full — strongest part** | LabOS | contract §7.1 |
| 9 | original photo → persisted preview → attachment | **Full** | LabOS | contract §6 |
| 10 | raw-results row → their automation → operational views | **Full (theirs)** | Airtable | contract §1 |

**Six legs solid, one partial, three holes — and all three holes are on the rig side of a run.** The design
is a complete specification of the Airtable boundary and an incomplete specification of LabOS internals.

**Legs 4 and 5 now have an agreed wire contract and a working firmware implementation** (§5 G1/G2), proven
against an isolated simulated rig. What is left on both is the backend half: minting the binding on the two
GETs, and keying the trials route on `event_id`. Leg 6 (G3) is untouched.

---

## 2. The operator's journey — and what delivers it

§1 is the system view. This is the same integration seen by the person holding the wrench, and it is the view
IFET's 2026-09-06 workflow message is written in. **Every requirement in that message maps to a milestone
here, or to a gap in §5 — nothing is left implicit.** Keep it that way: when they send a new workflow
statement, it gets a row, not a new document.

| Step | What the operator does | Delivered by | Watch out |
|---|---|---|---|
| 1 · Pick the work | Selects Project → Mock-up → Protocol → Section, **from the local cache** — never a live Airtable call, so a network blip cannot block them. Sections show Required/Not Required/Unconfirmed, supported or not, complete or not | M2 read cache · M3 pickers · **MU** screens | Names are display only; permanent record IDs route everything |
| 2 · **Verify the numbers** | Enters the actual inward/outward pair from the trusted proposal, the proposal reference, who verified, and when. Airtable's values are shown alongside for comparison but **cannot start a rig** | M3 backend gate · **MU** form | **This step adds operator work, and is the one thing we cannot remove from our side.** It relaxes to a one-click confirm the day the extractor is fixed. Contradicts their "no double entry" rule — say so explicitly, do not let them discover it |
| 3 · Set up the run | Picks attached gauges, reviews the derived loading sequence, starts. Requirement snapshot, procedure version, stage plan and identity all **freeze** here | M3 run create · **MU** | A later Airtable edit never mutates a live run — it means a new run. Gauge selection vs `GAUGE_COUNT` is unreconciled (§5 G6) |
| 4a · Static Load / Cycles | Watches the rig execute; stages and trials record themselves | **MF** + M3 | Until MF lands, the verified pair from step 2 sits on the run while the rig reads the old `static_tests` row (§5 G1, G2) |
| 4b · Impact / Forced Entry / ANSI | Presses the test button and types results, notes and photos into a form that **already knows** project, mock-up, protocol, system, operator and attempt number | M3 entities/routes · **MU** screens | No model, no route, no table exists today (§5 G3). Impact *requirements* are not in the register either (§5 G7) |
| 5 · Finish | Explicitly completes, or aborts with a reason. Evidence freezes | M3 | Never infer completion from a timeout or a disconnect; missing telemetry is not a pass |
| 6 · Review | A **named reviewer** records Pass/Fail/Inconclusive and Retest Required, once, with reasoning | M3 verdict route · **MU** | Nothing writes pass/fail today — this step is new. Operator and reviewer are stored separately even when the same person |
| 7 · It reaches Airtable | Sees a status chip: Synced / Pending / Sync Failed / Retry Required | M2 outbox + worker · **MU** chip | Their four words are our four contractual values. A correction is a new attempt, never an edit of the old |

### Their operating rules — already ours

Airtable never controls equipment (write allowlist is one table) · an outage never stops testing
(transactional outbox) · LabOS keeps the detail, Airtable gets the summary · never duplicate records
(upsert on `LabOS Attempt ID`) · permanent IDs for sync, names for display · every attempt retained ·
the four sync-status words · no billing, pricing, invoice or scheduling data crosses the boundary.

### Where the benefit actually lands

Worth stating plainly, because it drives priority and it affects adoption:

| | Gains |
|---|---|
| PM / office | **The big one.** Live project status without chasing the lab; results stop being retyped |
| Lab manager | Real attempt and retest history, which does not exist today |
| Reviewer | A defined pass/fail step with a name and a timestamp on it |
| Operator | **The least — and initially a net cost**, because of step 2 |

**The outbound half of the sync pays off immediately; the inbound half does not pay off until the extractor
is fixed.** Until then, pre-filled requirements are a display convenience and a cross-check, not a time
saver. If anything has to slip, slip inbound polish, not the outbound queue.

---

## 3. Scope and decisions

Five test types: Static Load, Cycles, Impact, Forced Entry, ANSI Z97.1. Backend first. Water infiltration
deferred; existing local water behaviour unchanged. Historical attempts excluded from sync; no name-based
backfill.

**The UI is no longer "deferred" — it is scoped as MU and owned.** A8 deferred it when this was an internal
engineering plan. IFET's 2026-09-06 workflow message is written entirely in screens, buttons and forms, and
§2 step 2 only exists if there is somewhere to type it. Deferring it by omission would have meant delivering
an API with no consumer and calling it done. MU may still be scheduled after M3 — that is a sequencing
decision — but it is no longer absent from the plan.

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

## 4. The build

### 4.1 Local entities

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

### 4.2 API surface

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

### 4.3 Concurrency — named mechanisms, not properties to assume

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

### 4.4 Outbound envelope

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

## 5. Open gaps — close before M3 can be demonstrated

### G1 · The work order never reaches the rig — **DECIDED; firmware half landed**

`grep -niE 'mqtt|state.?machine|test_index|device'` over contract v0.4 **and** the design returns zero hits.
The real path (`ifet-firmware/src/state_machine/state_machine.py:337-372`):

```
UI ──MQTT──> {command:'start', mode:'manual'|'cyclic', project_id, test_index, sensor_id, selectedSensors[]}
           ──> GET /projects/{pid}/static-tests/{idx}  ──>  setpoint = data['pressure'] * ±1
```

The rig's pressure comes from a **`static_tests` row addressed by `project_id` + `test_index`**. A run has no
such address. So §3.3 stores the verified pair on the run and the rig still reads the old
`static_tests.pressure` — the verified-values requirement is enforced on a path the rig never touches.

**Decided: the binding is resolved server-side and handed back on the GET the rig already makes.**
`GET /projects/{pid}/static-tests/{idx}` and `GET /projects/{pid}/next-cyclic-test` gain an optional `run`
object — `labos_attempt_id`, `programme_id`, `stage_id`, `stage_ordinal`. Consequences, and why this option:

- **The MQTT `start` payload does not change**, so MF needs no UI release and no operator retraining.
- **`test_index` allocation and `static_tests` materialisation stay exactly where they are.** MF adds
  identity to an existing exchange rather than replacing the addressing scheme, which is what kept the
  change additive enough to be safe on production rigs.
- **Cyclic works the same way for free.** G1/G2 were written around static's `(project_id, test_index)`, but
  cyclic never had a `test_index` at start — it calls `GET /projects/{pid}/next-cyclic-test` and the server
  already chooses. That made cyclic the *easier* binding, not a second problem.

Landed in firmware on `feature/labos-firmware-p3`: `StateMachine.bind_run()` takes the identity off the test
payload at every start and mints one stage event ID. **Still open — the backend half:** minting the object on
those two GETs. Until then a real rig gets no binding and every callback is unmapped, which is the designed
degradation, not a failure.

### G2 · Two incompatible callback shapes — **DECIDED; firmware half landed**

Firmware posts to `/projects/{pid}/static_tests/{idx}/trials` (`api/api.py:28-45`):

```json
{"deflections": [{"deflection_gauge": 1, "max_deflection": …, "permanent_deflection": …, "recovery": 60}]}
```

No run ID, no stage ID, **no event ID** — so §4.2's "duplicates replay safely" is unachievable through it.
That makes this a firmware change, not a backend adaptation.

**Decided: the existing route keeps its shape and gains two optional keys.** No new route, no transition
period, no dual-write. The rig echoes the `run` object back and adds an `event_id` it minted at start:

```json
{"deflections": [{"deflection_gauge": "1", "max_deflection": "12.34",
                  "permanent_deflection": "1.20", "recovery": 60}],
 "event_id": "…", "run": {"labos_attempt_id": "…", "stage_id": "stg-static-0", …}}
```

Both keys are **omitted entirely** when absent, so a pre-MF backend receives byte-for-byte the body it
receives today. Three rules, all three now covered by tests:

1. **`event_id` is minted per stage attempt and reused across POST retries** — that is what makes a retry a
   replay the backend can dedupe rather than a second trial. A rerun of the same stage is a new attempt and
   gets a new ID. The trial POST previously had **no retry at all**, so a network blip lost the trial
   silently; it now retries three times with an unchanged body and re-raises if the attempts are spent,
   because a lost trial has to stay loud.
2. **An unbound callback still carries an `event_id`**, or a retry of an unmapped callback would duplicate it.
3. **No binding means unmapped, never guessed.** `bind_run()` reassigns on every start, so a start whose
   response carries no `run` clears the previous one and a stale attempt ID cannot ride along.

**Still open — the backend half:** keying the trials route on `event_id`, and recording an unbound callback as
unmapped rather than attaching it to a guessed run.

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

**Item 53 is now delivered on the firmware side, in W2 as originally scheduled** — `bind_run()`, the echoed
binding and the stage event ID. Gap H's remaining half is the backend. Item 51 stays M7, still hardware-bound.

### G5 · No operator surface — now scoped as MU, not closed

Contract §3.3 requires the operator to enter the verified pair, its reference, verifier and time. A8 deferred
the UI, and M3 is "all five backend workflows" — so the release was an API with no consumer, and **no rig
could lawfully start.** IFET's 2026-09-06 message is written entirely from the operator's seat, which settles
it: the UI is a deliverable, tracked as **MU**.

Still true and still worth writing down: **M1–M5 acceptance is API-level**, and "cannot drive a rig from
Airtable values" persists past M5 regardless of MU, because that constraint belongs to the extractor, not to
the interface.

### G7 · Impact requirements are not in the register

Their message asks LabOS to receive "impact requirements" so the operator stops retyping them. The register
carries only a **count** of impacts (`IMPACT_LMI` / `IMPACT_SMI` as Count/impacts). Missile type, missile
weight and target velocity — the values our own `missile_impact_tests` and `shots` tables hold — appear
nowhere in it, so an LMI operator would still type them by hand.

Four rows are now in the register as `OPEN`/`PROPOSED`. **The open question is whether they belong in Airtable
at all**: the protocol normally fixes the missile and velocity, so Airtable may only need to carry per-job
deviations, plus `Impact Locations`, whose relationship to the total-impacts count is itself unsettled.
Decide with them before creating the fields.

### G8 · Forced Entry, ANSI and failure notes — output shape reopened

Their message lists "forced-entry results", "ANSI Z97.1 results" and "failure notes" as things LabOS sends
back. §7 decided sub-detail lives in JSON with `Test Result` carrying pass/fail, and to add a dedicated scalar
**only when a named operational report requires one**. Their message may be exactly that request — or it may
be a description of what they want visible, which the JSON plus `Test Result` already satisfies.

Three rows are in the register as `OPEN`/`PROPOSED`. **Ask which report needs them before creating them**, and
decide Forced Entry and ANSI together or not at all. `Failure Notes` is the easiest of the three and the most
likely to be genuinely wanted: today one `Notes` field carries both meanings.

### G9 · Loading sequences — ownership never agreed

Their message lists loading sequences as flowing **from** Airtable into LabOS. Nothing in Airtable holds
them; LabOS derives 14+ stages from the verified inward/outward pair, and that derivation is validated to
full precision against production data.

**Recommendation: LabOS keeps deriving them**, and Airtable supplies only the pair. It works today, it is
already proven, and it removes a thing that would otherwise have to stay in sync between two systems. But
that is currently an assumption on our side and a different assumption on theirs — settle it in writing
before M3, because it changes what a Protocol Section has to carry.

### G10 · The simulation harness existed, was undocumented, and pointed at production — **closed**

`grep -rniE 'simulat|fake_serial|device_node' docs/` returned **zero hits** before 2026-09-06, so the plan
treated a rig as the only way to exercise the firmware legs, and §10 called the offline `test` node "the
largest unmanaged risk". A simulated device node had been in the repo all along
(`simulation/ifet_device_node/`, with `src/fake_serial_service` and `src/fake_valves_node`).

It could not be used as it stood, for two independent reasons:

1. **It had no deflection gauges.** The two fakes cover pressure sensor 1 and VFD feedback; nothing published
   `sick/sensors/{n}`, so no simulated rig could complete a static or cyclic test. `src/fake_sick_service`
   now does, mirroring the real gateway's payload field for field.
2. **On a workstation running `ifet-management-tunnel.service`, `localhost:1883` and `localhost:8000` are the
   production broker and API.** That compose uses `network_mode: "host"` with `config1-d.json`, whose
   `device_id` is **`device1`** — production system-1's identity. Bringing it up would have attached a fake
   rig impersonating system-1 to the production broker and let it POST trials into the production database.

`simulation/mf_harness/` replaces it for this work: a private bridge network with no host networking, host
ports on 11883/18000, rig identity `device901`, and a stub backend. Config schema parity against
`config{1,2}.json` is checked and differs only in identity, endpoints, the `sick` block and the deliberately
omitted `turbo` block. Operating rule now in §11.

### G11 · Two latent firmware crashes, found by running the harness — **fixed**

Neither is MF, and neither is theoretical:

| Where | Fault |
|---|---|
| `state_machine.py` `__init__` | `turbo_id`/`turbo_valves` were only assigned when the config had a `turbo` block, but five states read `machine.turbo_id` on **every** test. Any config without `turbo` raises `AttributeError` inside the state-loop thread on the first start and the rig stops responding. Latent only because every production config happens to define `turbo` |
| `states/start_vfd.py:29` | `self.turbo_id` where `self.machine.turbo_id` was meant — `State` has only `.machine`. Short-circuit evaluation hides it unless `vdf_feedback == 0` **and** `turbo_vdf_feedback != 0`, i.e. on the turbo rig (**system-2**) with the slave reporting a non-zero frequency at that moment. Then it kills the state loop in `StartVDFState.on_exit` |

Both are one-line fixes on `feature/labos-firmware-p3`. **Neither is deployed**, and the second one is a
live-rig fault on system-2's turbo path, so it wants a deploy decision of its own rather than riding along
with MF.

### G6 · Register and entity drift — small, mechanical

| Item | Problem |
|---|---|
| `completion_source` | Required by contract §2; absent from the register **and** from §4.1's run columns (now added above) |
| `identity_assurance = declared` | Required by contract §4; same absence (now added above) |
| Sync service deployment | Contract §7 says "one container, no public port" and stops — no compose service, env var names, credential source or health policy, in a design that specifies fencing semantics to the sentence |
| Gauge selection | `GAUGE_COUNT` is a snapshotted programme parameter (contract §3.2); firmware takes `selectedSensors[]` live at MQTT start. Never reconciled; a mismatch at start has no defined behaviour |
| `Test Name`, `Abort Reason` | JSON-only by contract §6 — correct, but they have no register row, so a register-vs-JSON diff reports them missing. Note it in the register header |

---

## 6. Milestones

| M | Deliverable | Owner | Exit evidence | Depends on |
|---|---|---|---|---|
| ~~**M1**~~ | Testing Base additions — **14 fields applied 2026-09-06**; synthetic linked fixture still outstanding | LabOS | ✅ Schema diff, before/after, field IDs and per-field reasons captured. ⬜ Fixture: asymmetric pair, blank/N-A/unknown examples | — |
| **M2** | **Disposable PostgreSQL harness first**, then local migration and the first vertical flow | LabOS | Two independent worker processes on separate connections; concurrent-enqueue, competing-worker, slow-send, stale-owner green; import → run → finish → worker restart → one Testing Base attempt | — |
| **MF** | **Firmware run/stage association — G1 + G2.** Firmware half ✅ 2026-09-06; **backend half open** | LabOS + firmware | ✅ Firmware: 22 unit tests, plus both harness scenarios green — a start carries a run identity, the callback echoes it with a stable event ID, replay creates nothing, and a pre-MF response yields an UNMAPPED callback rather than a guessed run. ⬜ Backend: mint the binding on the two GETs, key the trials route on `event_id`, record unbound callbacks as unmapped. ⬜ Then re-run on a real rig | M2 identity (backend half only) |
| **M3** | All five backend workflows, review, corrections, evidence — **including G3 capture for Impact / Forced Entry / ANSI** | LabOS | §7 acceptance cases | M2, MF |
| **MU** | **Operator interface — the seven steps in §2.** Pickers, the verification form, run setup, the three manual-entry screens, review, and the sync-status chip | LabOS | An operator completes each of the five test types end to end without retyping anything Airtable already holds, and without a rig starting on unverified numbers | M3 · G7/G8 decided |
| **M4** | Change document with actual implementation results | LabOS | Every planned change marked applied/verified or outstanding | M1–M3 |
| **M5** | Production cutover, separately scheduled | LabOS + IFET | Schema/automation acceptance, migration rehearsal, preflight, agreed window | M4 · window |
| **M6** | Deflection calibration (legacy item 27) | LabOS | Known displacement applied to a gauge, transform identified end to end; `Deflection Value`/`Unit` unquarantined **or** the omission reconfirmed with evidence | bench/rig hardware |
| **M7** | Achieved-pressure acquisition (G4 legacy, off-board item 51) | LabOS | A validated measurement source for `Max Pressure Achieved`, **or** the omission reconfirmed with evidence | bench/rig hardware |

**M2 is one unit** — fixing sequence allocation alone leaves ordering unsafe. **MF is new and gates M3**;
it is the July commitment being re-entered, not new scope. **MF's firmware half no longer waits on M2 or on
rig hardware** — it is done and testable locally via `simulation/mf_harness/`; only its backend half sits
behind M2's identity work. **M6 and M7 are tracked, not blocking**: omission
is the initial-release behaviour, so M1–M5 do not wait for them. Their dependency is bench/rig hardware —
the same dependency the offline `test` node represents, so **one hardware ask covers both**.

P1 is a migration dependency, not a separate prior deployment: since production is still at `3a65a83e0463`,
P1 and the new revision rehearse as **one ordered upgrade** on local PostgreSQL.

---

## 7. Acceptance checks

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

## 8. Known deviations in the committed groundwork

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

## 9. Airtable team — what we need, what we owe

**Environments.** Testing `app4oXS3Kd5IKWgJ7` · Production `app0OCunbmuXl7Hc9`.
Read: `IFET Projects` `tblLYcRC7q6Srjfk3` · `Mock-Ups/Specimens` `tblcrGv0WJn6FTTGO` ·
`Tests Protocols` `tblutO1Q8TNC4BLk0` · `Protocol Sections` `tblqpvuJlSdkeS9PS`.
Write: `LabOS Raw Data Table` `tblnc9SsbXU0C0FWh` — **the runtime write allowlist is this table alone.**
Schema-write credentials belong to setup, never to the runtime worker. Tokens stay server-side, out of git and
out of browser-served config.

**Schema is no longer a permission question.** LabOS is authorized to define and add the required fields in
the Testing Base with a documented change register. 73 register rows — **66 DECIDED** (44 BASELINE,
**14 APPLIED**, 4 CONDITIONAL, 3 OMITTED, 1 PLANNED local-only) plus **7 OPEN/PROPOSED** raised by their
2026-09-06 workflow message and held until §5 G7/G8 are settled with them.

**The 14 decided additions were applied to the Testing Base on 2026-09-06** — field IDs, before/after schema
and the reason for each are in `../evidence/testing-base-changes-2026-09-06/`. Production is unchanged and
those 14 are exactly its delta.

**Do not create a PROPOSED field.** `OPEN` means we have not agreed it — and now that the shared Airtable
view is to become the confirmed schema that production is built from, a speculative field would propagate
rather than sit harmlessly in a sandbox. An unwanted field is harder to remove than to add.

**Their automations run on this schema and we cannot see them** — the Meta API refuses
`/meta/bases/{base}/automations` with `403`. Every change we made was additive, which rules out the usual
breakages, but two things need their eyes: an unfiltered "when record updated" trigger will now fire more
often, and their `Protocol Sections` automation must keep exclusive ownership of `Result`, `Status` and
`Testing Date`. **Production's existing automations are not assumed compatible merely because fields exist.**

**Keep it small.** No new tables, no new relationships, no parsing or backfill of `Value`, no delta-cursor
field, one writable table, and no dedicated scalar per outcome. If the Airtable team wants fewer fields
still, `Requirement Kind` is the one to drop — contract §3.2 already implies it from `Requirement Code`.

**Authority, once their view is confirmed.** The Airtable schema becomes the shared source of truth for
**which fields exist**; `../contract/write-contract-v0.4.md` remains authoritative for **what they mean and
when LabOS writes them**, and `../contract/interface-schema.csv` is the generated join of the two. That split
already exists — confirming their view does not move it.

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

## 10. Asks to IFET — operational

| Ask | Why | When |
|---|---|---|
| **Bench/rig hardware access** | The single dependency shared by M6 and M7. One ask covers both | Before M6/M7 scheduling |
| **The `test` node back online** (offline since ~2026-07-24) — **a real rig is being connected to the fleet; confirm which node and when** | The only non-production rig. **No longer the largest unmanaged risk**: `simulation/mf_harness/` exercises the firmware legs locally, so MF's firmware half was proven without it. Still needed to validate MF against real sensors, real gauges and the real backend before M5. Note its config points at the **production** broker and API (`10.1.10.185`), so a rig on the fleet is not an isolated environment — its trials land in the production database unless the new route is gated | Before MF's backend half is exercised end to end |
| **A maintenance window** for the M5 cutover | Nothing is deployed; the change set grows with every milestone | M5 |
| **Weight behind the extractor fix** | A safety item, not a schedule item, and the only true gate on running from Airtable requirements | Now |
| **A decision on already-reported results** | A shifted value reached a Passed record. Quality/business call, not an engineering one | On the blast-radius report |

**Dates.** The original 2026-07-23 → 2026-08-27 window closed, and the 2026-10-09 pilot target has **not been
revalidated** against MF, G3 or the hardware dependency. No new date is committed here until M1 and M2 land;
quoting the October target as live would be a fabrication.

---

## 11. Operating rules

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
- **Never bring up `simulation/ifet_device_node/` on a workstation running the management tunnel.** With
  `ifet-management-tunnel.service` active, `127.0.0.1:1883` and `127.0.0.1:8000` are the **production**
  broker and API; that compose uses `network_mode: "host"` with `config1-d.json`, whose `device_id` is
  `device1` — system-1's identity. Use `simulation/mf_harness/` instead: private bridge network, ports
  11883/18000, identity `device901`. A simulated rig must never be able to reach a real broker. §5 G10.
- **Secrets never enter git**, and never `deployment/config/config.json` or `src/ifet_ui_react/config.json` —
  both are served to the browser.
- **Docs:** this file is the delivery authority and is edited in place. New dated `.md` files belong in
  `evidence/` and `correspondence/` only. Close open items in the authoritative document first, then views.
- **Commits** are authored `gad <abdulrahmanashraf.gad@gmail.com>` with no assistant attribution.
