# LabOS ↔ Airtable — delivery plan

**Living document — update in place, do not date it or fork it.** Epic IFET-32.
**Authority split:** `../contract/write-contract-v0.4.md` governs *meaning* (identity, envelope, semantics,
concurrency guarantees). This file governs *delivery* (state, sequence, gaps, ownership, asks). On a conflict
about what a field or a guarantee means, the contract wins; on a conflict about what is built or scheduled,
this file wins. Machine-readable mapping: `../contract/field-register.csv` (73 rows).

Dated files belong in `evidence/` and `correspondence/` only — those are point-in-time artifacts. Status,
design and roadmap are one document, this one. Superseded snapshots live in git history, not in the tree.

---

## 0. State — probed 2026-09-07, not asserted

### 0.1 "Production" means two different things — always say which

This bit us in review, and it is worth reading before any sentence in this file that uses the word.

| Term | What it is | Who owns it | Our access |
|---|---|---|---|
| **Airtable production base** `app0OCunbmuXl7Hc9` | IFET's live business base — jobs, specimens, protocols, **and** customer emails, proposal amounts, QuickBooks invoice IDs | IFET / the Airtable team | **Read-only.** `AIRTABLE_TOKEN_PRODUCTION` reads it; every write path refuses it unconditionally, even with `AIRTABLE_ALLOW_PRODUCTION_WRITE=true` |
| **Airtable Testing base** `app4oXS3Kd5IKWgJ7` | Our sandbox, where the 14 fields were applied | LabOS, by agreement | Read and write, one writable table |
| **LabOS production** — the `management` node | The Raspberry Pi running Postgres, `report-api`, the React UI and the MQTT broker, on branch `latest` | us | Full, and the reason for every rule in §11 |

So **"nothing is deployed"** is about the `management` node, and **"production is untouched at 142 fields"**
is about the Airtable base. Both are true at once and they are unrelated claims.

### 0.2 The shared base link, and how it relates to the token

`https://airtable.com/app0OCunbmuXl7Hc9/shr18UCpayz45a4D5` is a **shared *base* link**, not a single view.
It exposes **all 8 tables**, each pinned to a specific view. View IDs:
`../schema/shared-base-views-2026-09-06.csv`.

| Table | Table ID | Shared view | Fields | LabOS |
|---|---|---|---|---|
| IFET Projects | `tblLYcRC7q6Srjfk3` | `viw7cVqQeYicQZqI7` | 35 | reads 3 |
| Mock-Ups/Specimens | `tblcrGv0WJn6FTTGO` | `viwypQ3WBVCqzD64c` | 13 | reads 3 |
| Tests Protocols | `tblutO1Q8TNC4BLk0` | `viwoq2ZQlvNc281vF` | 8 | reads 3 |
| Protocol Sections | `tblqpvuJlSdkeS9PS` | `viwXxVYSTEX5FYtQv` | 16 | reads 5 · **8 of the 14 additions** |
| Walls & Positions | `tblVUvcSPAoneG26W` | `viwbOz5xPn61XZJuf` | 8 | — |
| Wall Scheduling/Reservation | `tblYjF1AApzmRDMrY` | `viwPBD0nZlNgGqLHl` | 19 | — scheduling is out of scope |
| Back Charges | `tbl0f2YxS3FHJ1dTD` | `viwWOk3vYATKLwJCb` | 13 | — billing never crosses the boundary |
| LabOS Raw Data Table | `tblnc9SsbXU0C0FWh` | `viweFgfWU8viu0d32` | 30 | **the only writable table** · 6 of the 14 additions |

**The cross-check that matters: the shared base and our token-derived baseline are the same 8 tables and the
same 142 fields, with nothing extra on either side.** So the read model they shared is exactly what
`../schema/baseline-2026-09-05/production/` already holds, and our field inventory is complete rather than
merely plausible.

**The token is still the grounding, for three reasons the browser cannot give:** it returns **field IDs**
(which is what the change register diffs against, and which cannot be read off a page), it returns types and
select options as metadata, and it returns **every field in a table regardless of whether a view hides it** —
a view is a projection, so what a shared view displays can be a subset of what the table holds. That is why
`production-change-spec.csv` is generated from the API and not transcribed from the link.

What the link is genuinely good for: anyone can open it without a token, so it is the right thing to point a
person at for a human cross-check — and it is how we know which view the Airtable team treats as canonical
per table.

---

### 0.3 Probed state

| | |
|---|---|
| **Deployed** | **Nothing of this integration.** `management` runs branch `latest` @ `90f9595` |
| Live alembic head | `3a65a83e0463` — **P1 (`b7c2e9a41d38`) not applied**, and M2 (`c4e1f8a92b07`) queued behind it |
| Live tables | 13, all legacy. No `sync_outbox`, `sync_state`, `test_programmes`, `test_programme_runs`, `at_mirror_*` |
| Live columns matching `airtable\|labos\|attempt` | **zero** |
| Code in the running `report-api` image | `app/{data,domain,utils}` only — **no `app/airtable/`, no `app/sync/`** |
| Live routes | 25 **on the node**; the branch now has 18 more for manual test capture. **None** for airtable, sync or import |
| `test_results` rows | 640 |
| `ifet-management` | `feature/labos-airtable` @ `e99c77b` — all integration code, unmerged, **still unwired** (`main.py` imports nothing from `app.sync`). Carries the sync migration, the §7.1 mechanisms, the enforced single-worker service and its compose entry, the v0.4 contract view with its omission guard, and the Postgres harness. **Eight §8 deviations closed; the ninth is partial** because the envelope/lifecycle behind `contract.py` still implements v0.3 timing and review phases |
| `ifet-firmware` | `feature/labos-firmware-p3` — docs, **plus the MF firmware change and the isolated simulation harness** (`simulation/mf_harness/`, `src/fake_sick_service/`). Not deployed to any rig |
| Committed envelope code | **v0.4 throughout.** `contract.py`, `envelope.py` and `mapping.py` now implement create → terminal → **first review** as three phases: create sends `Pending`, terminal stays `Pending`, `build_verdict()` writes the verdict with a named reviewer. `Test Date` is the completion instant. 238 tests + 84 subtests on `postgres:13` |
| **Testing Base schema** | **159 fields.** 14 applied 2026-09-06, 3 more 2026-09-08; the before/after chain is hash-verified and carries 0 removals and 0 retypes. **No longer empty** — the fixture `IFET-FIXTURE-0001` was seeded 2026-09-08. Evidence and reasons: `../evidence/testing-base-changes-2026-09-06/` |
| Production Base schema | Unchanged at 142 fields, **re-verified live 2026-09-08 by `app/airtable/preflight.py`**, which also confirms none of the 17 has leaked into it. The generated 168-row interface remains an exact match and the 14 above are exactly the production delta |

Nothing above is a blocker on its own. Together they mean: **every leg of this integration is greenfield
against production, and no code has ever carried a result end to end.**

### 0.3a Where the work actually stands — 2026-09-08

| | |
|---|---|
| **Track A** (Airtable) | TA1–TA4 ✅. **TA5 — send — is the only one left, and it is not ours.** Two documents are written and **NOT SENT**: the change document (which now also answers their three clarifications) and the product-owner update |
| **Track B** (the three manual tests) | TB1–TB3 ✅. Migration `d1a6b93f2e57`, 18 routes, `MANUAL_TESTS_API.md` + `openapi.json`. **TB4 is the deploy and needs a window** |
| **Track C** (the integration) | Untouched, except that TB1/TB2 closed most of TC1: reviewer columns and the verdict route exist now |
| **Pre-send check** | `python -m app.airtable.preflight` — read-only, both bases, verifies every claim the change document makes. Run it the morning it is sent |
| **Still true** | **Nothing is deployed.** The `management` node is unchanged |

### 0.4 Live verification, 2026-09-08 — read-only, both rigs and the node

Run before committing to a migration, because a migration written against `models.py` would have been wrong.

| | |
|---|---|
| `management` | 7 containers up 2 weeks; alembic head **`3a65a83e0463`** confirmed again; 13 legacy tables |
| **Live `projects` columns** | **six** — `id`, `name`, `parent_id`, `device_id`, `inward_design_pressure`, `outward_design_pressure`. **No `airtable_*` columns exist.** `models.py` declares three that the database does not have, because P1 is unapplied. `project_parents` is `id` + `name` only |
| Live row counts | 32 parents · 79 projects · 508 static · 634 cyclic · 640 results · **39 missile impact · 114 shots** · 37 water |
| **Impact is already in production use** | `missile_impact_tests` and `shots` hold real data, so §4.5 is **additive against live rows, not greenfield**. `missile`, `missile_weight`, `shots.area`, `shots.velocity` are all `NOT NULL` today and are widened, never dropped |
| system-1 | 3 containers up 7d · `config1-site-b.json` · `device1` · **VFD address 12** · 5 × `pressure2` + Flow |
| system-2 | 4 containers up 13h (incl. the standalone turbo controller) · `config2.json` · `device2` · **VFD address 5** · 5 × `pressure2`, scale 144 → PSF |
| **`CLAUDE.md` is wrong on the VFD address** | It says "12, not 5 on the production rigs". system-2 is genuinely on **5**. The address is **per-rig**, and that line has already cost time once |
| **Airtable Testing Base** | 8 tables, 156 fields — **0 records in all five tables.** A structural clone of production plus our 14 additions, with no data in it at all |
| **Airtable Production Base** | 1 project · 6 mock-ups · 24 protocols · **54 Protocol Sections** · 1 raw-data row |
| **The eight typed fields do not exist in production** | The `Protocol Sections` delta is exactly those eight. In production `Requirement Code` and `Applicability` are absent, and the legacy `Value` text field is populated on **24 of 54** rows — blank on `# Dials`, `Impact` and `Forced Entry (*)` |
| Source data that already exists and we do not read | `Product Type` (Projects) · `Height (Inches)`, `Width (Inches)`, `Service line` (Mock-Ups) — all populated. Four free fields that answer the product owner's "product information" |
| An empty field they made for us | `Read Project Info For LabOS` on IFET Projects, **never populated**. Ask what they intended before designing around it |

**The single most consequential line above:** pre-fill is not blocked by our code. It is blocked by data that
does not exist yet — in production the typed fields are absent, and in Testing there are no records at all.
That is why Track A's fixture (A3) comes before the document, and why the document's central ask is
*populate these fields, never from the extractor*.

**For what to do next, go straight to §6.0** — the ordered list of everything remaining, keyed to the
milestone and `DG` identifiers, plus the four items that must not be queued behind it.

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
| 3 | requirement → independently verified snapshot → run create | data ✔ · **no capture surface** | LabOS | contract §3.3 · gap **DG5** |
| 4 | run → work order the rig can execute | **decided + firmware landed**; backend half open | LabOS + firmware | gap **DG1** |
| 5 | rig → `/trials` → stage trial bound to a run | **decided + firmware landed**; backend half open | LabOS + firmware | gap **DG2** |
| 6 | manual capture — Impact, Forced Entry, ANSI Z97.1 | **one sentence for 3 of 5 types** | LabOS | gap **DG3** |
| 7 | terminal → first review → verdict, corrections | **Full** | LabOS | contract §4 |
| 8 | run → outbox → worker → Airtable upsert | **Full — strongest part** | LabOS | contract §7.1 |
| 9 | original photo → persisted preview → attachment | **Full** | LabOS | contract §6 |
| 10 | raw-results row → their automation → operational views | **Full (theirs)** | Airtable | contract §1 |

**Six legs solid, one partial, three holes — and all three holes are on the rig side of a run.** The design
is a complete specification of the Airtable boundary and an incomplete specification of LabOS internals.

**Legs 4 and 5 now have an agreed wire contract and a working firmware implementation** (§5 DG1/DG2), proven
against an isolated simulated rig. What is left on both is the backend half: minting the binding on the two
GETs, and keying the trials route on `event_id`. Leg 6 (DG3) is untouched.

---

## 2. The operator's journey — and what delivers it

§1 is the system view. This is the same integration seen by the person holding the wrench, and it is the view
IFET's 2026-09-06 workflow message is written in. **Every requirement in that message maps to a milestone
here, or to a gap in §5 — nothing is left implicit.** Keep it that way: when they send a new workflow
statement, it gets a row, not a new document.

| Step | What the operator does | Delivered by | Watch out |
|---|---|---|---|
| 1 · Pick the work | Selects Project → Mock-up → Protocol → Section, **from the local cache** — never a live Airtable call, so a network blip cannot block them. Sections show Required/Not Required/Unconfirmed, supported or not, complete or not | M2 read cache · M3 pickers · **MU** screens | Names are display only; permanent record IDs route everything |
| 2 · ~~Verify the numbers~~ **Removed by A9** | Nothing. The operator enters the test's parameters in LabOS exactly as they do today | — | **This step existed only because LabOS planned to execute from Airtable values.** Under A9 it reads none, so there is no verification burden, no contradiction with their "no double entry" rule, and no path for a shifted value to reach a rig. The single largest piece of operator cost in this design, removed by deciding not to consume the data |
| 3 · Set up the run | Picks attached gauges, reviews the derived loading sequence, starts. Requirement snapshot, procedure version, stage plan and identity all **freeze** here | M3 run create · **MU** | A later Airtable edit never mutates a live run — it means a new run. Gauge selection vs `GAUGE_COUNT` is unreconciled (§5 DG6) |
| 4a · Static Load / Cycles | Watches the rig execute; stages and trials record themselves | **MF** + M3 | Until MF lands, the verified pair from step 2 sits on the run while the rig reads the old `static_tests` row (§5 DG1, DG2) |
| 4b · Impact / Forced Entry / ANSI | Presses the test button and types results, notes and photos into a form that **already knows** project, mock-up, protocol, system, operator and attempt number | M3 entities/routes · **MU** screens | No model, no route, no table exists today (§5 DG3). Impact *requirements* are not in the register either (§5 DG7) |
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
| Operator | **Neutral.** Was a net cost while step 2 existed; A9 removed it, so the operator's workflow is unchanged from today |

**The outbound half of the sync is now the whole point.** A9 reduced the inbound half to identity — enough
to know which job a result belongs to — so there is no pre-filled-requirement payoff to wait for and nothing
inbound left to slip. If anything has to slip, it is not the outbound queue.

---


## 2a. Requirements traceability — the product owner's message, line by line

**This is the view the PM and the product owner read.** §6.0 is the engineering sequence and speaks in `DG`
and `M` identifiers; this section speaks in *his* words, so a requirement can be looked up the way it was
written rather than the way we filed it. Both describe the same work. When his requirements change, this
table gets a row — not a new document.

Source: the workflow message of 2026-09-06, restated 2026-09-08.

**Status vocabulary.** `LIVE` = running in production today · `BUILT` = code written and tested, not deployed
· `SPEC` = designed, not built · `GAP` = not yet designed · `DIVERGES` = we deliberately do something else,
and he needs telling.

### System responsibilities

| His requirement | Our deliverable | Status |
|---|---|---|
| HubSpot is the starting point | Out of scope. Contract §1 records that HubSpot supplies approved commercial scope | ✅ n/a |
| Airtable structure Project → Mock-Up → Protocol → Section | The read model is exactly this hierarchy | ✅ SPEC |
| A project may have multiple mock-ups, each with different tests | `ProjectParent` → `Project` is job → mock-up. Verified live: the production base has 1 project and 6 mock-ups | ✅ LIVE |
| All testing information stays connected to the correct mock-up | Every test table has a `project_id` FK to the mock-up | ✅ LIVE |
| Airtable manages the operational side | Their automations own `Result`, `Status`, `Testing Date`; LabOS never writes them | ✅ SPEC |
| LabOS controls VFDs, valves, sensors, gauges | Unchanged, and no Airtable code exists anywhere in firmware | ✅ LIVE |
| LabOS is used to manually enter Impact / Forced Entry / ANSI results | §4.5 below | ❌ GAP → build |

### Data flow into LabOS

| His requirement | Our deliverable | Status |
|---|---|---|
| Operator selects Project / Mock-up / Protocol / Section | `at_mirror_*` + picker routes (§4.2) | ❌ SPEC |
| Project number | `IFET job number` → `project_parents.name` | ❌ SPEC |
| Mock-up / specimen name | `Mock-up/specimen name` → `projects.name` | ❌ SPEC |
| Product information | `Product Type`, `Service line`, `Height/Width (Inches)` — **all four already exist and are populated in their base**; LabOS does not read them yet. Display-only, never executed from | ❌ SPEC |
| Required test | `Requirement Code` — the singleSelect already carries all nine codes | ❌ SPEC |
| Inward and outward design pressures | `Required Value Inward` / `Outward` → the `Project` DP pair | ❌ SPEC |
| **Loading sequences** | **DIVERGES — LabOS derives them and Airtable holds none.** Proven from the running code: 6 static factors `[0.75,0.75,1,1,1.5,1.5]`, 8 cyclic high/low factors and fixed cycle counts, all from the DP pair alone. Supplying them from Airtable would create a second copy to keep in sync for no gain | ⚠️ DIVERGES |
| Impact requirements | Count works via `Required Value` + `IMPACT_LMI/SMI`. **`Missile Type`, `Missile Weight`, `Impact Velocity` do not exist** — three fields to add | ⚠️ partial |
| Number of gauges or deflection points | `GAUGE_COUNT` → `Required Value`. **No LabOS column exists** — §4.5 adds `projects.gauge_count` | ❌ GAP → build |
| The operator should not manually recreate existing information | **Conditional, and this is the real blocker.** Our side is ready; the data is not. In the production base `Requirement Code` is empty on all 54 sections, and the eight typed fields do not exist there at all. Until someone populates them, the operator still types everything | ⚠️ blocked on data |
| LabOS does not need billing, pricing, invoices, payments or scheduling | 114 fields marked `ignore` in `interface-schema.csv`; the runtime read allowlist enforces it | ✅ BUILT |

### Testing inside LabOS

| His requirement | Our deliverable | Status |
|---|---|---|
| Static Load and Cycles run as hardware-controlled tests | Unchanged | ✅ LIVE |
| Impact / Forced Entry / ANSI entered manually via a button | §4.5 | ❌ GAP → build |
| Every result carries project, mock-up, protocol, section and attempt identifiers | The envelope requires all five on every phase | ⚠️ BUILT wire / GAP in DB — the live `projects` table has six columns and no `airtable_*` at all, because P1 is unapplied |
| The same test may be attempted more than once; keep every attempt | Static and cyclic already retain every trial. `attempt_number` per programme is specified in contract §2 | ⚠️ LIVE for rig tests · SPEC for the rest |

### Data flow back to Airtable

| His requirement | Our deliverable | Status |
|---|---|---|
| Test status | `Test Status` — In Progress / Completed / Abborted | ✅ BUILT |
| Pass or fail | `Test Result`, written by the first-review phase | ✅ BUILT |
| Test date | `Test Date` = execution completion | ✅ BUILT |
| Operator | `Operator Name`; reviewer stored separately | ✅ BUILT |
| **Actual pressure** | **GAP.** The value is published on `{device_id}/sensors/{addr}` and rendered live in the UI — nothing persists it. Not "no source"; not captured. Track C | ❌ GAP |
| **Maximum pressure achieved** | **GAP.** Same source, same fix. Formerly M7 | ❌ GAP |
| Impact results | `Impact Result` (free text) + per-shot detail in JSON | ✅ BUILT |
| Forced-entry results | `Test Result` + JSON detail. No dedicated column — both `Test Type` and `Test Result` are singleSelect, so Airtable filters and groups natively | ⚠️ DIVERGES, decided |
| ANSI Z97.1 results | As above, decided together with Forced Entry | ⚠️ DIVERGES, decided |
| **Deflection readings** | **DIVERGES, and deliberately.** They are uncalibrated raw IO-Link counts mislabelled as inches. Publishing them would publish a number we cannot stand behind. Needs bench hardware (M6). **This one should not be "fixed" to satisfy the requirement** | ⚠️ DIVERGES |
| Failure notes | Carried inside `Notes` and the JSON | ⚠️ DIVERGES, decided |
| General notes | `Notes` | ✅ BUILT |
| Photograph links | `Photos` (url) + `LabOS Photos` (attachment channel) | ✅ BUILT |
| Retest required | `Retest Required`, first-review phase only — never inferred from an unreviewed checkbox | ✅ BUILT |
| Testing continued or stopped | `Testing Continued` | ✅ BUILT |
| LabOS report / detailed-data link | `LabOS Report Link`, `Excel File Link` — CONDITIONAL, published only once a reachable origin is validated | ⚠️ conditional |
| Update existing records, never duplicate | Upsert on `LabOS Attempt ID` alone | ✅ BUILT |

### Operating rules

| His rule | How it is guaranteed | Status |
|---|---|---|
| Airtable must never control test equipment | Structural, not procedural: the runtime write allowlist is one table, and no Airtable code exists in firmware | ✅ BUILT |
| An Airtable connection problem must not stop testing | Transactional outbox; the domain save and the queue row commit together, and the worker is a separate container | ✅ BUILT |
| LabOS remains the detailed record | Airtable receives a summary; originals and full detail stay local | ✅ BUILT |
| The same information should not be entered twice | See the data-flow row above — blocked on data, not on code | ⚠️ blocked |
| Every record must use permanent identifiers | `rec…` IDs route everything; names and job numbers are display and reconciliation only | ✅ BUILT |
| UI shows Synced / Pending / Sync Failed / Retry Required | `/sync/status` returns exactly those four words | ⚠️ BUILT backend · ❌ no UI |

### The manual-entry form must already know the context

| His requirement | Our deliverable | Status |
|---|---|---|
| Project · Mock-up · Test protocol · System · Operator · Attempt number | §4.5 routes take `project_id` and derive the rest; attempt number is allocated server-side | ❌ GAP → build |

### Responsibilities and prerequisites

| His statement | Where we actually are |
|---|---|
| "The Airtable team will be responsible for defining the Airtable tables, fields and record relationships" | **Inverted, with authorisation.** LabOS defined and applied 14 fields on 2026-09-06 and proposes 3 more. The change document is what makes that legitimate rather than unilateral |
| "The LabOS team will be responsible for the interface, local storage, API communication, field mapping, sync queue and error handling" | All six are ours and all six are specified; the queue and error handling are built and tested | ✅ |
| Scoped personal access tokens, restricted base and permissions | Two PATs, server-side only. Production is read-only and every write path refuses it unconditionally | ✅ BUILT |
| **"Before development begins, both teams need to agree on the exact field mapping and permanent identifiers"** | **The one prerequisite in his message that is still unmet.** The mapping exists — 73 register rows, 168 interface rows, permanent IDs specified — and has never been sent. This is §6.0 step 2 | ❌ **OPEN** |

## 3. Scope and decisions

### 3.0 The three meeting commitments — and where each one stands

What was agreed with IFET, traced to the artifact that satisfies it. **Nothing here depends on the Airtable
team**; all three are ours to finish.

| Commitment | Artifact | State |
|---|---|---|
| **1. Prepare the structured schema for fetching and posting data between LabOS and Airtable** | `../contract/interface-schema.csv` — generated; every field in both bases with `labos_use` = read / write / ignore. Meaning: `../contract/write-contract-v0.4.md` §§2–6. Mapping: `../contract/field-register.csv` | ✅ **Drafted, A9-narrowed and live-reconciled** — 10 real fields read plus 4 record IDs, 38 mapped OUT (32 potentially published; 6 explicitly omitted), 1 Airtable-owned read-only field and 114 deliberately ignored. ⬜ **Not yet validated** against all five test types locally — that is the gate on commitment 3 |
| **2. Make the required changes in the Testing Base only** | 14 fields applied 2026-09-06; production untouched and verified unchanged | ✅ **Done.** Evidence: `../evidence/testing-base-changes-2026-09-06/` |
| **3. Prepare and share a document of all changes made, with the reason for each** | `../evidence/testing-base-changes-2026-09-06/README.md` (per-field reasons, before/after schema, field IDs) · `production-change-spec.csv` (**one row per field: KEEP or ADD, whether LabOS reads or writes it, and why**) · cover letter `../correspondence/airtable-team-questions-2026-09-06.md` | ✅ **Written.** ⬜ **Deliberately not sent** — it goes out after commitment 1 is validated locally. Asking them to change production on an unvalidated schema is how we would end up asking twice |

**The document is what unlocks their side.** They update production from it; we do not touch production
ourselves. So the sequence is: validate the schema locally → send the document → they apply → M5 cutover.



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
| **A10** | **No extractor dependency, and the document is sent only after local validation (2026-09-06).** We do not wait for, or ask for, an extractor fix — A9 removed our need for it. The three meeting commitments are ours to complete: the structured fetch/post schema, the Testing-Base-only changes, and the change document. **The document goes to the Airtable team only once the schema is validated locally against all five test types** — we do not ask them to change production on the strength of an unvalidated design |
| **A11** | **Linking is forward-only (2026-09-07).** Linking a local job to an Airtable record makes only *subsequent* attempts sync-eligible; an earlier attempt is published by an explicit operator action, never by the link. A link asserts identity, not that the work under it has been re-examined. Full reasoning and what it obliges MU to show: §6.1 |
| **A9** | **LabOS is standalone; Airtable is management's mirror (2026-09-06).** LabOS stays fully functional without Airtable. The integration syncs **jobs and reports**, joined by `IFET job number` for humans and `rec…` IDs for machines. LabOS reads **14 inbound fields and no requirement values at all** — the operator sets a test up in LabOS exactly as today. `Requirement Code` routes the test type and `Applicability` says whether the section is assigned; they are the only two non-identity fields. Both bases keep all 14 applied fields; unread ones are `IGNORED` in the register, not deleted. This removes the proposed verification form, **not the existing cross-platform duplication of requirement entry** |

Settled defaults: `Test Date` = completion; explicit UTC `Testing Start/End Date`; declared operator and
reviewer identity stored separately; originals local, previews in Airtable; no mandatory report link before a
reachable origin exists; a not-required section receives no fabricated passing attempt.

**Standing caution — do not drive a rig from Airtable requirement values.** Their PDF extractor drops blank
cells, so a 60 PSF requirement reads as 9. LabOS cannot detect it; every shifted value is individually
plausible. Contract §10.19.

**A9 satisfies that caution by construction rather than by discipline.** LabOS reads no requirement values,
so there is no path by which a shifted one could start a rig. The caution stays written down because it
still binds *them* — a shifted value has already reached a Passed record on their side — and because it
applies in full the day any future release consumes requirement values.

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

**First, what is actually concurrent here — because it is narrower than §7.1's language suggests.**

| | |
|---|---|
| **The rigs are not.** One rig runs one test at a time; that is a hardware limit | Two rigs run two *different* attempts, so they take different `attempt_id`s and **never contend for the same row.** There is no "two rigs at once" case, and nothing below is justified by one |
| **One attempt, two actors — yes** | The rig POSTs its `/trials` callback for attempt A while the operator uploads a photo or presses finish for A from the UI. Both enqueue into A's queue. A human and a machine, with no hardware limit between them. **This is the case the sequence-allocation fix exists for** |
| **Worker count — a deployment property, not a hardware one** | **Decided 2026-09-06: exactly one, enforced** (see DG6). The mechanisms below then cost nothing and mean the topology question stops mattering — a rolling restart, a stray `up -d`, or someone running the worker by hand cannot corrupt anything |

Each mechanism fails silently without its implementation, and **none is observable in a SQLite test** —
`SKIP LOCKED` is ignored, two connections cannot contend, and a savepoint retry has nothing to race.
Contract §7.1.

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


### 4.5 Manual test capture — Impact, Forced Entry, ANSI Z97.1

**None of the three touches the rig.** No VFD, no valves, no MQTT, no stage trials, no run binding. They are
manual entry, which is why they can ship to production ahead of any Airtable work and independently of the
firmware legs. They go in `report-api` beside static and cyclic; `sync-worker` is not involved.

**What they are, because the names mislead.** ANSI Z97.1 is a *bag-drop* safety-glazing test — a weighted bag
swung into the glazing, pass if it does not break or breaks safely. Missile Impact is *windborne debris*
(ASTM E1886/E1996). Both are "impact" and they are different tests, which is why contract §3.2 already
carries `ANSI_IMPACT` separately from `IMPACT_LMI`/`IMPACT_SMI`. Forced Entry is forced-entry resistance
(ASTM F588 / F476, AAMA 1304): specified loads and manipulation against the lock and sash.

**Business shape, from the product owner (2026-09-07).** Impact is *how many impacts, whether each passed,
and a few photographs* — no heavy metadata. Forced Entry and ANSI are *pass or fail*. ANSI is normally the
first test performed on a specimen; that is **informational ordering only** and is not enforced, because a
hard block would eventually stop legitimate work and there is no override in this design.

#### Entities

**`ManualAttempt` — a mixin, not a table.** The columns every non-rig attempt needs, and precisely what the
outbound envelope already consumes. A mixin because the repo already uses one for exactly this purpose
(`AirtableProtocolRef` on `StaticTest`/`CyclicTest`), and because static and cyclic take the same columns
later without a rewrite.

| Column | Note |
|---|---|
| `labos_attempt_id` | UUID, unique. The upsert key |
| `attempt_number` | allocated server-side, per (project, test type) |
| `status` | `In Progress` → `Completed` / `Aborted` |
| `test_result` | `Pending` until the first review, then Pass / Fail / Inconclusive |
| `operator_name` · `testing_start_date` · `testing_end_date` | |
| `verdict_by` · `verdict_at` · `retest_required` | **first review only.** All three nullable — an unreviewed attempt has not answered the retest question, and `bool(None)` is an answer nobody gave |
| `testing_continued` · `note` · `abort_reason` | |

**`manual_tests`** — Forced Entry and ANSI Z97.1 in **one** table with a `type` discriminator. Both are
pass/fail with a note; the shape is identical, so two near-identical tables would be duplication rather than
fidelity to the pattern. `StaticTest` already carries a `type` column, so this matches the repo.
Columns: `id`, `project_id` FK, `type` (`Forced Entry` | `ANSI Z97.1`), `required_option` (the grade or
class, e.g. `ASTM F588 Grade 40`, `Class A`), `result` boolean, plus the mixin.

**`missile_impact_tests` / `shots`** — **already exist and are already in production use: 39 impact tests and
114 shots.** This is not greenfield. `Shot.result` is already the per-impact boolean the product owner
described. Changes are additive only: add the mixin to `missile_impact_tests`, and widen
`missile`, `missile_weight`, `shots.area`, `shots.velocity` to nullable so the operator is not forced to type
metadata the test does not need. Existing report generation keeps working.

**`test_photos`** — `id`, `filename`, `path`, `note`, and two nullable FKs
(`missile_impact_test_id`, `manual_test_id`). Explicit columns rather than a polymorphic key. Enabled for all
three types and required by none: a *failed* Forced Entry or ANSI is exactly when someone wants a photograph,
and evidence cannot be added after an attempt freezes.

**`projects`** gains `gauge_count` and `impact_count`, both nullable — the two requirements the product owner
asks Airtable to supply that today have nowhere to land.

#### Routes

Phases follow the contract: create → terminal → first review. All under `report-api`.

| Route | Behaviour |
|---|---|
| `POST /projects/{id}/manual-tests/` | Create a Forced Entry or ANSI attempt. Allocates `attempt_number`, sets `Pending` |
| `GET /projects/{id}/manual-tests/` | List, with attempts |
| `PUT /manual-tests/{id}/finish` | Terminal: result, notes, end time. Explicit completion or an abort reason — never inferred |
| `POST /projects/{id}/impact-tests/` | **Create an Impact attempt — no create route exists today**; Impact is currently write-by-report-generation only |
| `POST /impact-tests/{id}/shots` | One impact: pass/fail, optional area/velocity/note |
| `PUT /impact-tests/{id}/finish` | Terminal |
| `POST /{manual-tests,impact-tests}/{id}/photos` | Upload; original retained locally |
| `PUT /{manual-tests,impact-tests}/{id}/verdict` | First review, once: reviewer, time, rationale, `Retest Required` |

FastAPI generates the OpenAPI document, so the UI developer is unblocked the moment these exist — before any
deployment and before any Airtable work.

#### Validation rules

1. **A verdict is recorded once**, by a named reviewer, and never by the terminal write.
2. **Operator and reviewer are stored separately**, even when they are the same person.
3. **Impact requires photographic evidence at finish**, enforced on the run-finish path — *not* as a
   precondition for publishing to Airtable, because attachments are their own delivery channel and may
   settle later. Forced Entry and ANSI require none.
4. **Missing telemetry never implies a pass.** Completion is explicit or it is an abort with a reason.
5. **A new attempt never overwrites an earlier one.** Corrections are new rows referring to the original.

### 4.6 Field ownership — standalone versus synced

**The rule that keeps this from forking into two systems:** the sync service never writes LabOS domain
tables; it fills the local mirror only. Creating a project always goes through the *same*
`POST /devices/{id}/projects/` whether the values were typed or pre-filled. Standalone and synced are one
form with the boxes empty or filled — not two flows, one create path, one set of tests.

`report-api` reads a **local** mirror table. It never calls Airtable and never imports `app.airtable` or
`app.sync`. An empty mirror means an empty picker, not a blocked operator.

**Class 1 — LabOS owns it; Airtable never supplies it.** `device_id` (which rig — not an Airtable fact, and
an explicit operator choice at import), all measured values, the verdict, reviewer and operator identity, and
the fourteen derived stage definitions. Sync must be structurally incapable of writing these.

**Class 2 — dual-source: the operator types it, or Airtable pre-fills it.** Job number, mock-up name, the
inward/outward pair, water applicability, gauge count, impact count, missile type/weight, shot velocity.
Requirements: every one stays manually enterable **forever**; pre-fill is a default, never a lock; the
existing `NOT NULL` on the DP pair is unchanged because the operator always supplies it either way; and the
import records *which* values came from Airtable so a wrong one stays traceable.

**Class 3 — Airtable-only, display, never required.** The `rec…` join keys and the display metadata
(`Product Type`, `Height`, `Width`, `Service line`). All nullable. Absent is normal, not degraded — a project
with no `airtable_*` id is `Excluded` from sync under A11 until an operator explicitly links it.

### 4.7 Sync wiring — the four call sites, and the six fields that prove it

**Why this section exists.** DG6 was closed on 2026-09-07 as "exactly one worker, enforced", which is true
of the *process* and misleading about the *pipeline*. Audited 2026-09-08:

| | State |
|---|---|
| `sync_outbox` / `sync_attempt_state` / `sync_state` tables | ✅ migration `c4e1f8a92b07` |
| `outbox.enqueue()` · `claim()` · fencing · lease · retry | ✅ built, 4 phases declared at `outbox.py:48-52` |
| `app/sync/service.py` runnable process + advisory-lock singleton | ✅ built |
| `sync-worker` compose service, starts disabled | ✅ built |
| `envelope.build_start` / `build_terminal` / first review | ✅ built, v0.4 |
| **Any caller of `enqueue()`** | ❌ **none.** `grep` finds the definition and zero call sites outside `app/sync/` |
| **`GET /sync/status` · `GET /sync/queue` · `POST /sync/queue/{id}/retry`** | ❌ **not built.** `state.status_payload()` is documented as "the payload behind `GET /sync/status`" and `outbox.py:408` as "the manual half of `POST /sync/queue/{id}/retry`" — both functions exist, neither is routed. `openapi.json` has no path containing `sync` |

So the queue is permanently empty and the worker has no liveness surface. **DG6's own justification for the
worker having no health check — "liveness stays the heartbeat row `report-api` already serves" — depends on
a route that does not exist.** That wording is corrected below rather than left standing.

#### The transaction rule

`enqueue()` runs **inside the domain save's transaction**. Contract §4: *"Each mutation and outbox entry
commits atomically."* The test row and the queue row commit together or neither does.

This is what delivers the product owner's rule that an Airtable problem must not stop testing (§2a): the
save touches only local Postgres, which is provably up because it just wrote the result. No HTTP request to
Airtable is ever on the operator's path.

**It does not violate TB2's isolation test.** `tests/test_report_api_isolation.py` forbids `report-api`
importing `app.airtable` or calling Airtable inline. A local `INSERT` into `sync_outbox` is neither — it is
the seam the isolation exists to create. The test's source scan must be narrowed to `app.airtable` and the
`app.sync` *client* path, not `app.sync.outbox`, and the narrowing recorded in the test itself.

#### The four call sites

Phases are `create → terminal → verdict`, plus a separately tracked `attachment` channel — contract §4 and
§6, and already the constants at `outbox.py:48-52`. One attempt is **one Airtable row**, upserted on
`LabOS Attempt ID` on every phase and retry (§6).

| # | Route as built (TB2) | Phase | Payload builder |
|---|---|---|---|
| 1 | `POST /projects/{pid}/{manual,impact}-tests/{id}/trials` and the rig `/trials` callbacks | `create` | `envelope.build_start` — identity, type, `Test Status = In Progress`, `Testing Start Date`, operator, explicit `Test Result = Pending` |
| 2 | `PUT /test-results/{id}/finish` | `terminal` | `envelope.build_terminal` — `Completed`\|`Abborted`, `Testing End Date`, `Test Date`, JSON detail. **`Test Result` stays `Pending`** |
| 3 | `PUT /test-results/{id}/verdict` | `verdict` | first-review builder — `Passed`\|`Failed`\|`Inconclusive`, `LabOS Verdict By`/`At`, `Retest Required`, rationale |
| 4 | `PUT /test-results/{id}/finish` (same call as 2) | `attachment` | one entry per attempt carrying the photo set as it stands at termination |

**Route names diverge from §4.2 and the built ones win.** §4.2 specifies a logical `/runs/{id}/finish` and
`/runs/{id}/verdict`; TB2 built `/test-results/{id}/finish` and `/test-results/{id}/verdict`, one route each
for all five test types. §4.2 is the older logical sketch; these four are the real call sites.

**Attachments enqueue at terminal, deliver asynchronously.** Decided 2026-09-08. Contract §6 permits
attachments to settle after terminal state without changing measured evidence, and the local rule that a
photo after the verdict is a `409` already guarantees the set cannot grow after review — so the set is
complete and immutable at termination, which is the earliest moment it can be sent as one entry. A slow or
failing upload therefore parks in its own channel and can never hold up a measured result.

**But only when the set is non-empty**, which the first draft of this section missed. Only *impact* attempts
must have a photograph to finish; Forced Entry and ANSI may complete with none, and static and cyclic
normally do. Enqueueing unconditionally would put an entry carrying nothing into the attachment channel for
most attempts — visible as permanent attachment backlog in `GET /sync/status`, i.e. the status surface
reporting missing evidence for attempts that were never required to have any. So the `attachment` entry is
enqueued only if at least one photo exists at termination, and an attempt with no photographs has **three**
phases, not four.

**No backfill.** The 623 live `test_results` rows predate P1 and carry no `labos_attempt_id`,
`labos_test_id` or requirement snapshot; every one would fail envelope validation and park, burying real
traffic behind 623 permanent failures. New attempts only, from deploy forward. A dated opt-in range tool is
a separate decision, not part of this.

#### The status surface — three routes, four words

| Route | Behaviour |
|---|---|
| `GET /sync/status` | `state.status_payload()` verbatim: the four contractual values **Synced · Pending · Sync Failed · Retry Required**, plus attachment backlog and `worker_heartbeat_at`. Computed at read time; **never** an Airtable call |
| `GET /sync/queue` | queue entries with phase, state, attempt count, next-eligible time, last error |
| `POST /sync/queue/{id}/retry` | `outbox.py:408` un-park — re-enables eligibility only, on the same FIFO worker. Never sends inline |

These three are also the UI's status chip (§2 row 7) and the **only** liveness surface for `sync-worker`,
which by design serves nothing itself.

#### The six fields that prove the wiring — the ground base

The Testing Base changes we applied in TA2/M1 split exactly along the read/write line, and the six write
fields land one per phase. **This is the acceptance matrix, not an illustration:**

| Field (`LabOS Raw Data Table`) | Type | Phase | Proves |
|---|---|---|---|
| `Testing Start Date` | dateTime | `create` | the create phase fires at Start, not at the end |
| `Corrects Attempt ID` | singleLineText | `create` | a correction is a new attempt, linked, original intact (§4) |
| `Testing End Date` | dateTime | `terminal` | terminal is a **merge** onto the create row, not a second row |
| `LabOS Verdict By` | singleLineText | `verdict` | operator and reviewer stored separately, `identity_assurance = declared` |
| `LabOS Verdict At` | dateTime | `verdict` | review is a third phase; `Retest Required` never inferred before it |
| `LabOS Photos` | multipleAttachments | `attachment` | evidence delivers on its own channel and may settle late |

The other eleven applied fields are **read** side, on `Protocol Sections` — `Missile Type`
`fld5Bs0aQXXeVso2y`, `Missile Weight` `fldmhdhonyyLcx4Ex`, `Impact Velocity` `fldJNfUVyqQEFOVWx` and the
eight requirement fields. TA3 already round-tripped these against fixture `IFET-FIXTURE-0001`; they are
pre-fill inputs and no sync phase writes them.

**All three missile fields are optional at every layer, confirmed 2026-09-08** — `missile_impact_tests.missile`
and `.missile_weight` and `shots.velocity` are `nullable` (widened from `NOT NULL` by `d1a6b93f2e57`), their
schemas are `Optional[... ] = None`, `POST /impact-tests/` accepts `{}`, and neither creating nor finishing an
impact test requires any of them. This is §4.6 Class 2 — *pre-fill is a default, never a lock* — and it means
the sync wiring can be built and accepted **without** these three carrying a value. Per-field phase assignment for all 38 `OUT` fields is the
`write_phase` column of `../contract/interface-schema.csv`, which is generated — it governs, not this table.

#### Prerequisite: all five test types means TC1 first

Manual and Impact could enqueue today. Static and cyclic **cannot** — no `run` UUID is minted, no
requirement snapshot is persisted, and the reviewer columns are unpopulated, so there is nothing to put in a
`create` payload. Wiring them without TC1 would enqueue entries that fail validation on every attempt.
TC1 lands first; the wiring is one change covering all five.

#### Test plan — dry-run, then one live round-trip

Both, in that order (decided 2026-09-08). All on **postgres:13** via the disposable harness, never SQLite:
§4.3's mechanisms are invisible there — `SKIP LOCKED` is ignored and a savepoint retry has nothing to race.

1. **Mechanism, no network.** Worker enabled, `AIRTABLE_TOKEN` blank. Proves: the queue fills from real
   saves; per-attempt FIFO with `create` before `terminal` before `verdict`; `SKIP LOCKED` gives one owner;
   the lease re-asserts per send; a bumped `owner_epoch` discards a stale outcome; a second worker instance
   exits rather than racing; and a rolled-back save leaves **no** queue row.
2. **Envelope refusal.** Each of the six fields sent in the wrong phase must be refused by `envelope.py`
   ahead of the column/JSON split — the failure mode that caught `Max Pressure Achieved`.
3. **Live Testing Base only.** `AIRTABLE_ALLOW_PRODUCTION_WRITE` stays `false`. One attempt of each of the
   five types, driven through all four phases, against fixture `IFET-FIXTURE-0001` — asserting **one** row
   per attempt with all six fields correct after the merge, via the existing `tests/stage3_live_write.py`
   path. This is TC2's acceptance.
4. **Both origins.** The same five, once from an imported Airtable job and once created locally with no
   `airtable_*` id — which must stay `Excluded` under A11 and enqueue nothing. Neither path may block the
   other (§6.1).

**Production is untouched throughout.** It has none of these tables — live alembic head is `3a65a83e0463`,
before P1.

## 5. Gaps — consolidated

**`DG*` are delivery gaps and this file owns them.** They were plain `G*` until 2026-09-06, which collided
with a second, older vocabulary: `G1`–`G5` and `gap H` in `../contract/write-contract-v0.4.md` §9–§10 are
**legacy July item labels** meaning entirely different subjects. Five letters, two meanings, no marker for
which — so a reference to "G1" could not be resolved without knowing who wrote it. The prefix fixes that.
The contract keeps its legacy labels untouched; nothing there needs to change.

| Legacy label | Subject | Where it lives now | Evidence |
|---|---|---|---|
| `G2` | the sign question | **Closed** — typed magnitudes, no legacy parsing | contract §9 |
| `G4` | achieved-pressure acquisition | milestone **M7** | contract §10 |
| `G5` | field creation | **authorized delivery work** — the 14 applied fields | contract §9 |
| `G1`, `G3` | **not recoverable** — see below | probably **M6** | contract §9 |
| `gap H` | the firmware leg had no milestone | **DG4**, below — closed by MF | this file |

Legacy `G1` and `G3` did not survive the consolidation: no definition of either exists in the current
doc set, and git history carries only the labels. Contract §9 groups them with `G4` as "retain the
release behavior until evidence supports widening it", and that is the omission trio — so they are
almost certainly `Deflection Value` and `Deflection Unit`, which makes them **M6** / legacy item 27.
**Read that as an inference, not a record.** If the July plan resurfaces, confirm it.

### Status of all eleven

| | Gap | State | Owner | Blocks | What actually unblocks it |
|---|---|---|---|---|---|
| **DG3** | Impact / Forced Entry / ANSI have no backend | 🔴 **OPEN — the largest piece of work left** | LabOS | M3, MU | nobody else. Ours to build |
| **DG1** | Work order never reaches the rig | 🟡 **Decided · firmware landed** | LabOS + firmware | MF, M3 | backend: mint `run` on the two GETs |
| **DG2** | Callback has no run / stage / event ID | 🟡 **Decided · firmware landed** | LabOS + firmware | MF, M3 | backend: key `/trials` on `event_id`; record unbound as unmapped |
| **DG5** | No operator surface | 🟡 **Scoped as MU** | LabOS | whether the release is usable | M3, plus DG7/DG8 decided |
| **DG6** | Register / entity drift · sync deployment unspecified | 🟡 **OPEN — mechanical** | LabOS | M2 exit tidiness | our own edit; an hour |
| **DG7** | Impact requirements not in the register | ✅ **Closed by A9** | LabOS | — | not needed — requirements are entered in LabOS |
| **DG8** | Forced Entry / ANSI / failure-note output shape | ✅ **Closed by A9** | LabOS | — | no dedicated scalar; `Test Result` + JSON. Revisit only for a named report |
| **DG9** | Loading-sequence ownership never agreed | ✅ **Closed by A9** | LabOS | — | LabOS derives; Airtable supplies nothing |
| **DG4** | Firmware leg had no milestone (`gap H`) | ✅ **Closed** | — | — | MF exists; July item 53 delivered |
| **DG10** | Sim harness undocumented, and aimed at production | ✅ **Closed** | LabOS | — | `simulation/mf_harness/` + warnings + §11 rule |
| **DG11** | Two latent firmware crashes | ✅ **Fixed, not deployed** | LabOS | system-2's turbo path | **a deploy decision of its own** |

**Nothing is blocked on anyone outside the team any more.** The three 🔵 gaps closed on 2026-09-06 when A9
decided that LabOS reads no requirement values — they were questions about an inbound surface that no longer
exists. Every remaining item is 🔴 or 🟡 and entirely ours.

---

## 5a. Open — all of them ours, none blocked externally

### DG3 · Three of five test types have no backend at all — **critical**

| Type | Model | Route | Table |
|---|---|---|---|
| Static Load, Cycles | ✔ | ✔ | ✔ |
| Impact | `MissileImpactTest` / `Shot` exist — **read-only, report generation only** (`main.py:992-1009`) | ✗ | ✔ |
| Forced Entry | ✗ | ✗ | ✗ |
| ANSI Z97.1 | ✗ | ✗ | ✗ |

`grep -rniE 'forced.?entry|ansi' app/` hits only the unwired v0.3 `contract.py` and the LaTeX template.
Against that, the plan gives Static/Cycles a full identity design and gives these three one sentence.
Neither Forced Entry nor ANSI appears in any acceptance check as a **capture** case.

### DG1 · The work order never reaches the rig — **DECIDED; firmware half landed**

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
- **Cyclic works the same way for free.** DG1/DG2 were written around static's `(project_id, test_index)`, but
  cyclic never had a `test_index` at start — it calls `GET /projects/{pid}/next-cyclic-test` and the server
  already chooses. That made cyclic the *easier* binding, not a second problem.

Landed in firmware on `feature/labos-firmware-p3`: `StateMachine.bind_run()` takes the identity off the test
payload at every start and mints one stage event ID. **Still open — the backend half:** minting the object on
those two GETs. Until then a real rig gets no binding and every callback is unmapped, which is the designed
degradation, not a failure.

### DG2 · Two incompatible callback shapes — **DECIDED; firmware half landed**

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

### DG5 · No operator surface — now scoped as MU, not closed

> **Reduced by A9, 2026-09-06.** The verification form — the screen this gap was mostly about — is gone,
> because LabOS reads no Airtable requirement values and the operator sets tests up as they do today. What
> remains of MU is the sync-status chip, the manual-entry screens for the three non-rig test types, and the
> job/section picker that links a LabOS test to an Airtable record. Still a deliverable, materially smaller.

Contract §3.3 required the operator to enter the verified pair, its reference, verifier and time. A8 deferred
the UI, and M3 is "all five backend workflows" — so the release was an API with no consumer, and **no rig
could lawfully start.** IFET's 2026-09-06 message is written entirely from the operator's seat, which settles
it: the UI is a deliverable, tracked as **MU**.

Still true and still worth writing down: **M1–M5 acceptance is API-level**, and "cannot drive a rig from
Airtable values" persists past M5 regardless of MU, because that constraint belongs to the extractor, not to
the interface.

### DG6 · Register and entity drift — small, mechanical

| Item | Problem |
|---|---|
| `completion_source` | Required by contract §2; absent from the register **and** from §4.1's run columns (now added above) |
| `identity_assurance = declared` | Required by contract §4; same absence (now added above) |
| Sync service deployment | ✅ **CLOSED 2026-09-07. Exactly one worker, enforced.** `app/sync/service.py` is the runnable process; `app/sync/singleton.py` holds a Postgres advisory lock so a second instance **refuses to start** rather than racing. Chosen for how it releases — the lock lives on one connection and vanishes when that connection does, so a SIGKILLed worker leaves nothing to clean up. Liveness is **intended** to be the heartbeat row `report-api` serves, because a worker answering its own health check would report healthy from inside a process whose database connection had gone — but ⚠️ **that route does not exist** (see §4.7), so the worker currently has no liveness surface at all. ✅ The `sync-worker` compose service and `SYNC_LOG_LEVEL` landed 2026-09-07 | ⚠️ **Corrected 2026-09-08: the process is closed, the pipeline is not.** Nothing calls `outbox.enqueue()`, so the queue is permanently empty, and the three `/sync` routes are unbuilt. §4.7 owns the wiring.
| Gauge selection | `GAUGE_COUNT` is a snapshotted programme parameter (contract §3.2); firmware takes `selectedSensors[]` live at MQTT start. Never reconciled; a mismatch at start has no defined behaviour |
| **Nine JSON-only fields, not two** | `Test Name` and `Abort Reason` are JSON-only by contract §6 and have no register row, so a register-vs-base diff reports them missing. **Counted 2026-09-07: there are nine** — those two plus `Required Value`, `Required Unit`, `Cycles Required`, `Cycles Completed`, `Test Rig`, `LabOS Version` and `Result Rationale`. They are absent by decision (§10.15), not by oversight. Note the whole set in the register header; `tests/test_five_test_types.py::JsonOnlyFieldsSurvive` pins it so the list cannot drift silently |

---

## 5c. Closed — kept for the record, and because each one changed the plan

### DG7 · Impact requirements are not in the register — **CLOSED by A9**

> **Closed 2026-09-06 without needing their answer.** A9 means impact requirements are entered in LabOS as they are today, so the four proposed fields are not needed and were never created. The question of whether Airtable should carry missile type, weight and velocity does not arise while LabOS reads no requirement values.

Their message asks LabOS to receive "impact requirements" so the operator stops retyping them. The register
carries only a **count** of impacts (`IMPACT_LMI` / `IMPACT_SMI` as Count/impacts). Missile type, missile
weight and target velocity — the values our own `missile_impact_tests` and `shots` tables hold — appear
nowhere in it, so an LMI operator would still type them by hand.

Four rows are now in the register as `OPEN`/`PROPOSED`. **The open question is whether they belong in Airtable
at all**: the protocol normally fixes the missile and velocity, so Airtable may only need to carry per-job
deviations, plus `Impact Locations`, whose relationship to the total-impacts count is itself unsettled.
Decide with them before creating the fields.

### DG8 · Forced Entry, ANSI and failure notes — output shape reopened — **CLOSED by A9**

> **Closed 2026-09-06 without needing their answer.** No dedicated scalar. `Test Type` and `Test Result` are both `singleSelect`, so Airtable filters and groups both workflows natively and the sub-detail travels in the JSON. The standing rule survives: add one **only** when a named operational report requires it. `Failure Notes` stays inside `Notes`.

Their message lists "forced-entry results", "ANSI Z97.1 results" and "failure notes" as things LabOS sends
back. §7 decided sub-detail lives in JSON with `Test Result` carrying pass/fail, and to add a dedicated scalar
**only when a named operational report requires one**. Their message may be exactly that request — or it may
be a description of what they want visible, which the JSON plus `Test Result` already satisfies.

Three rows are in the register as `OPEN`/`PROPOSED`. **Ask which report needs them before creating them**, and
decide Forced Entry and ANSI together or not at all. `Failure Notes` is the easiest of the three and the most
likely to be genuinely wanted: today one `Notes` field carries both meanings.

### DG9 · Loading sequences — ownership never agreed — **CLOSED by A9**

> **Closed 2026-09-06 without needing their answer.** LabOS derives the loading sequence from the pair it already holds, and under A9 reads nothing from Airtable to do it. There is no longer a shared assumption to reconcile — the recommendation became the design.

Their message lists loading sequences as flowing **from** Airtable into LabOS. Nothing in Airtable holds
them; LabOS derives 14+ stages from the verified inward/outward pair, and that derivation is validated to
full precision against production data.

**Recommendation: LabOS keeps deriving them**, and Airtable supplies only the pair. It works today, it is
already proven, and it removes a thing that would otherwise have to stay in sync between two systems. But
that is currently an assumption on our side and a different assumption on theirs — settle it in writing
before M3, because it changes what a Protocol Section has to carry.

---

### DG4 · The firmware leg had no milestone — a regression, now closed

The July internal plan — retired into this file, recoverable from git history — tracked it as **gap H** and off-dashboard
items **51** (capture actual & max pressure) and **53** (thread IDs through `start` + result POST), scheduled
for **W2** — which is now. The September design's M0–M7 are entirely backend, Airtable and metrology. Item 51
survived as **M7** under a new name; **item 53 and gap H were lost.** They are DG1 and DG2 above.

**Item 53 is now delivered on the firmware side, in W2 as originally scheduled** — `bind_run()`, the echoed
binding and the stage event ID. Gap H's remaining half is the backend. Item 51 stays M7, still hardware-bound.

### DG10 · The simulation harness existed, was undocumented, and pointed at production — **closed**

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

### DG11 · Two latent firmware crashes, found by running the harness — **fixed**

Neither is MF, and neither is theoretical:

| Where | Fault |
|---|---|
| `state_machine.py` `__init__` | `turbo_id`/`turbo_valves` were only assigned when the config had a `turbo` block, but five states read `machine.turbo_id` on **every** test. Any config without `turbo` raises `AttributeError` inside the state-loop thread on the first start and the rig stops responding. Latent only because every production config happens to define `turbo` |
| `states/start_vfd.py:29` | `self.turbo_id` where `self.machine.turbo_id` was meant — `State` has only `.machine`. Short-circuit evaluation hides it unless `vdf_feedback == 0` **and** `turbo_vdf_feedback != 0`, i.e. on the turbo rig (**system-2**) with the slave reporting a non-zero frequency at that moment. Then it kills the state loop in `StartVDFState.on_exit` |

Both are one-line fixes on `feature/labos-firmware-p3`. **Neither is deployed**, and the second one is a
live-rig fault on system-2's turbo path, so it wants a deploy decision of its own rather than riding along
with MF.

## 6. Milestones

### 6.0 The remaining work, in order

**This section owns *sequence* only.** Per-item state lives in §5 (gaps) and §8 (deviations); milestone
definitions live in the table below. Do not restate status here — that is how five status surfaces drifted
apart once already.

**`#` is an order, not an identifier.** The identifiers are the `Ref` column: existing milestone and `DG`
IDs. Nothing here invents a new numbering scheme.

**Landed so far:** the Testing Base additions (M1's 14 fields), the design and contract at v0.4, MF's
firmware half, and most of M2 — harness, the migration that did not exist, and 8 of 9 §8 deviations.
**Nothing is deployed.**

**Three tracks, and they do not block each other.** This was one chain until 2026-09-08, which made the
Airtable team appear to be waiting on our build. They are not: what they need from us is a *schema*
document, and the schema is validated. Splitting the sequence is what lets them start.

### Track A — unblock the Airtable team (days, not weeks)

| # | Do this | Ref | Owner | Waits on | Done when |
|---|---|---|---|---|---|
| ~~**TA1**~~ | ~~Validate the write surface against all five test types~~ **✅ 2026-09-07** | §3.0 · A10 | LabOS | — | Done, and **it failed first** — three defects, all five types. Evidence: `../evidence/schema-validation-five-types-2026-09-07.md` |
| ~~**TA2**~~ | ~~Add three Impact requirement fields to the Testing Base~~ **✅ 2026-09-08** | §9 | LabOS | — | Applied. **156 → 159.** `Missile Type` `fld5Bs0aQXXeVso2y`, `Missile Weight` `fldmhdhonyyLcx4Ex`, `Impact Velocity` `fldJNfUVyqQEFOVWx`. `Impact Locations` deliberately not created — location is a per-impact observation, not a requirement. Production untouched at 142 |
| ~~**TA3**~~ | ~~Fixture round-trip — the read side had never been exercised~~ **✅ 2026-09-08** | M1 | LabOS | ✅ TA2 | Done. `app/airtable/fixture.py` seeded `IFET-FIXTURE-0001` into the previously empty Testing Base and read it back: every field readable and correctly typed, an **asymmetric** 60/45 pair derived all 14 stages, `FORCED_ENTRY`/`ANSI_IMPACT` carried a class and no numeric value, and no section carries a legacy `Value`. **This is also M1's fixture**, and the UI developer's data |
| ~~**TA4**~~ | ~~Regenerate `interface-schema.csv` and `production-change-spec.csv`~~ **✅ 2026-09-08** | §9 | LabOS | ✅ TA2 | Done, and it needed a register correction first: the six typed requirement fields were still `IGNORED` from the A9 era. **Pre-fill reads the typed fields and never parses `Value`**, so they are `IN` and `Value` stays `IGNORED`. Now **159 fields — 17 ADD, 142 KEEP; LabOS reads 20, writes 35, ignores 104** |
| **TA5** | **Send both** — `../correspondence/testing-base-change-document-2026-09-08.md` to the Airtable team, and `../correspondence/po-update-and-test-node-request-2026-09-08.md` to the product owner. **Both written 2026-09-08, NOT SENT.** The Airtable document now opens with answers to their three clarifications (2026-09-08) and carries the change reference behind them, so their questions and our changes arrive together rather than as two exchanges | §3.0 commitment 3 · §10 | **IFET/you** | ✅ TA3, TA4 | Send records filled in and copies in `correspondence/sent/`, which is append-only |

**Behaviour is explicitly out of Track A.** Automation compatibility, roll-up behaviour and upsert-in-anger
need the vertical flow *and* their base, so they are marked "verified at cutover" in the document rather than
holding it. A10's gate was against sending an **unvalidated schema**; the schema is validated, so the gate is
satisfied.

### Track B — unblock the UI developer (parallel, no Airtable dependency)

| # | Do this | Ref | Owner | Waits on | Done when |
|---|---|---|---|---|---|
| ~~**TB1**~~ | ~~The migration~~ **✅ 2026-09-08** | DG3 · §8 | LabOS | — | `d1a6b93f2e57`: `manual_tests` + `manual_test_results`/`impact_test_results` as **joined-table subclasses of `TestResult`**, following `static_tests`→`static_test_results`. `test_photos` owned by the attempt. Numbered `shots` with the 114-row backfill. Rehearsed P1 → M2 → this against **populated** tables and rolled back. Also widened `retest_required` to nullable and added the missing `verdict_by`/`verdict_at` |
| ~~**TB2**~~ | ~~The endpoints~~ **✅ 2026-09-08** | DG3 → M3 | LabOS | ✅ TB1 | 18 routes. Terminate, review and evidence are **one route each on `/test-results/{id}`** for all five test types, not a copy per type — so static and cyclic inherit review the day they need it. `tests/test_report_api_isolation.py` enforces that `report-api` imports no `app.airtable`/`app.sync`, by import **and** source scan. 238 tests + 84 subtests on Postgres |
| ~~**TB3**~~ | ~~Hand over the OpenAPI document~~ **✅ 2026-09-08** | MU | LabOS | ✅ TB2 | `MANUAL_TESTS_API.md` + `openapi.json`, both in `ifet-management`. Every documented route cross-checked against the generated spec. **The UI developer is unblocked, before any deploy** |
| **TB4** | **Deploy the three test types to `management`** | M3 | LabOS + IFET | TB2, a window | Impact, Forced Entry and ANSI capture live alongside static and cyclic. No Airtable involvement. Runbook `../runbooks/p0-p1-deploy-2026-08-28.md`, **§2 is the go/no-go** |

### Track C — the integration itself (after A and B)

| # | Do this | Ref | Owner | Waits on | Done when |
|---|---|---|---|---|---|
| **TC1** | **The verdict route's remaining half** — the reviewer *columns* landed with TB1 and the verdict route with TB2, so what remains is programme/run and mirror persistence for the **rig** test types | §8 (9th deviation) | LabOS | ✅ TB1 | Static and cyclic attempts carry the same identity and review path the manual types now have |
| **TC1a** | **Wire the four call sites** — `enqueue()` inside each domain save's transaction, `create`/`terminal`/`verdict`/`attachment`, all five test types. Narrow `test_report_api_isolation.py` to `app.airtable` and the sync *client*, so a local outbox `INSERT` is not mistaken for an inline Airtable call | §4.7 · DG6 | LabOS | TC1 | The queue fills from a real save, per-attempt FIFO, and a rolled-back save leaves no entry |
| **TC1b** | **Build the three `/sync` routes** — `GET /sync/status` (the four contractual words + attachment backlog + `worker_heartbeat_at`), `GET /sync/queue`, `POST /sync/queue/{id}/retry`. The functions behind all three already exist and are unrouted | §4.7 · §4.2 | LabOS | TC1a | `sync-worker` has a liveness surface, the UI has its status chip, and DG6's justification is true rather than aspirational |
| **TC2** | **The vertical flow — two origins, one merge** (§6.1) | M2 | LabOS | TC1a, TC1b, TA3 | import → run → finish → worker restart → **one** attempt in the Testing Base, **and** the same for a job created locally with no Airtable origin. Neither path may block the other. **Acceptance is the six applied write fields, one per phase** — `Testing Start Date`, `Corrects Attempt ID` (create) · `Testing End Date` (terminal) · `LabOS Verdict By`/`At` (verdict) · `LabOS Photos` (attachment): §4.7 |
| **TC3** | **MF backend half** — mint `run` on the two GETs, key **both** `/trials` routes on `event_id`, record an unbound callback as unmapped | DG1 · DG2 → MF | LabOS | TC2 | `simulation/mf_harness/` passes against the real backend. **Two routes, not one**: `api.py:94` and `api.py:109` |
| **TC4** | **Capture actual and maximum pressure** — subscribe to `{device_id}/sensors/{addr}` during a run and persist max plus final | M7 | LabOS | TC2 | Closes two product-owner requirements. **Not "no source"** — the value is on the bus and renders live in the UI; nothing stores it |
| **TC5** | **MU — the operator interface** | DG5 → MU | LabOS | TB3, TC2 | An operator completes all five test types end to end and sees the sync status of each |
| **TC6** | **DG6's remaining drift** | DG6 | LabOS | — | Register rows for `completion_source` and `identity_assurance`, defined behaviour for a `GAUGE_COUNT` vs `selectedSensors[]` mismatch at start, and the nine JSON-only fields noted in the register header |
| **TC7** | **M4 — the change document with actual results** | M4 | LabOS | TA5, TC2 | Every planned change marked applied/verified or outstanding, with evidence |
| **TC8** | **M5 — production cutover for the integration** | M5 | LabOS + IFET | TC7, and a window | Schema and automation acceptance, migration rehearsal, preflight, agreed window |

**Deliberately still not delivered, and both are decisions rather than omissions.** Deflection values stay
quarantined until calibration (M6) — publishing uncalibrated raw counts mislabelled as inches would publish a
number we cannot stand behind. Loading sequences stay derived in LabOS rather than supplied by Airtable
(§2a). Both need saying to the product owner rather than being discovered at demo.

**Step IDs are prefixed `TA`/`TB`/`TC`** so they cannot be confused with decisions A1–A11 in §3 — the same collision that made a bare `G1` unresolvable before the `DG` prefix.

**Track B is done through TB3 and Track A through TA4.** What remains: **TA5 is yours to send**, TB4 needs a window, and Track C is the integration itself. Nothing is deployed.

**Two independent passes on 2026-09-07 found the same defects, which is worth recording.** The five-type
schema validation (step 1) and the implementation audit both landed on `Test Result = Pending` being
refused at create and on `Test Date` carrying the **start** instant. The audit went further and found the
phase model missing entirely; the validation went further and found an attachment upload gating a measured
result. Neither pass alone was sufficient, and the 172-test suite was green through all of it — because
every test in it exercised Static Load and the create phase. **A green suite is not coverage of a matrix
nobody enumerated.**

One of these defects published a plausible **wrong** timestamp rather than nothing, which is the same
failure class as the extractor shift this whole design guards against — on our own side of the boundary.
A10 put the gate between validation and the send precisely so the Airtable team would not be the ones to
find it, in production, after applying a schema on our word.

### 6.1 What step 5 actually means — two origins that must merge

Clarified 2026-09-07, and it widens the step. "Import" is not one path, it is the
narrower of two, and the plan had only described that one.

**Origin A — the job is registered in Airtable.** Sync fetches what the
`management` node needs to run it: the job, specimen, protocol and section
identity, plus `Requirement Code` so LabOS knows which of the five tests a
section is and `Applicability` so it knows whether the section is assigned. The
operator picks it and runs. Results flow back against that section's record IDs.

**Origin B — the job is created in LabOS.** An operator sets up a project and a
test on the node directly. **This must work with Airtable absent, unreachable,
stale, or never involved at all** — LabOS is fully operational and functional
whether or not it is in sync, and that is not a degraded mode, it is the normal
one. Nothing about origin B may depend on a mirror being fresh, or present.

**And the two must merge, not fork.** A job that began locally can later turn out
to be a job Airtable knows about; when it does, the local work is *linked* to the
Airtable record rather than re-created beside it. That link is what makes
subsequent attempts eligible to sync.

| Rule | Why |
|---|---|
| **Import is idempotent on the `rec…` record ID** | Re-importing a job reuses the local rows. Anything else quietly produces two of the same job, and the second one looks exactly as legitimate as the first |
| **Linking is an explicit operator action, never a name match** | `IFET job number` is hand-typed and project names repeat. Auto-merging on either would silently attach one job's results to another — and names never route work anywhere else in this contract, so they must not route a merge |
| **Unlinked local work is `Excluded` from sync, not queued** | It has no Airtable identity to upsert against. Excluded is a decision the operator reverses by linking, not a failure to retry |
| **A stale or missing mirror never blocks a test** | The mirror is a convenience for picking work. If it is empty, origin B still works, and origin A degrades to "you cannot pick from the list yet" rather than "you cannot test" |

**A11 — linking is forward-only (decided with IFET, 2026-09-07).** When a local
job is linked to an Airtable record, only attempts recorded *after* the link
become eligible to sync. An earlier attempt is published by an explicit operator
action, one at a time, never by the link itself.

§3 already excluded historical attempts with no name-based backfill, which
settled the 640 pre-integration rows — but not a run recorded locally yesterday
and linked today. This settles it. The reasoning is that a link is a statement
about *identity*, not a statement that everything recorded under that identity
has been re-examined and is fit to publish; collapsing the two would let one
operator action push untriaged attempts into Airtable, where there is no undo on
our side of the boundary. Keeping the decision with a person costs a click and
removes a whole class of accident.

**What this obliges MU to show:** an attempt that is Excluded because it predates
its link must say so, and offer the publish action. Silently excluded work looks
identical to work that failed to sync, and the four contractual status words
(§7) do not distinguish them — `Excluded` is a decision the operator reverses,
not a failure to retry.

### Out of band — do not queue these behind the ten

| Item | Ref | Owner | Why it is not in the sequence |
|---|---|---|---|
| **Deploy the system-2 turbo fix** | DG11 | **IFET/you** | It is a **live-rig fault**, not integration work: `start_vfd.py` would kill the state loop on system-2's turbo path. Fixed and committed, **not deployed**, and it should not wait for M5's window |
| **Verify the running firmware matches this tree** | — | **IFET/you** (node) | A read-only `sha256sum` of the `*.py` inside each running `state_machine` container. The harness builds from the repo while production runs a baked image, and system-1 carries an uncommitted `recovery_time` edit — so until this is done, "the harness proves the firmware" has an unmeasured gap in it |
| **Bench/rig hardware** | M6 · M7 | IFET | One ask covers both. The rig now being connected to the fleet may be it — confirm which node and when |
| **The extractor fix, automations check, blast-radius report** | §9 | Airtable | Requested in step 1 and **none of them blocks anything of ours** — A9 removed our dependency on their requirement values entirely. The extractor still matters to *them*: a shifted value has already reached a Passed record on their side |

| M | Deliverable | Owner | Exit evidence | Depends on |
|---|---|---|---|---|
| ~~**M1**~~ | Testing Base additions — **14 fields applied 2026-09-06**; synthetic linked fixture still outstanding | LabOS | ✅ Schema diff, before/after, field IDs and per-field reasons captured. ⬜ Fixture: asymmetric pair, blank/N-A/unknown examples | — |
| **M2** | **Disposable PostgreSQL harness first**, then local migration and the first vertical flow | LabOS | ✅ Harness on **postgres:13** (the version production runs), disposable by construction. ✅ The missing migration, rehearsed as **P1 → M2 in one ordered upgrade** on real Postgres and rolled back. ✅ 8 of 9 §8 deviations closed. ✅ Single-worker compose service. ✅ Prior concurrency suite: 172 PG / 163 + 9 skipped SQLite after the schema-view update. ⬜ Finish v0.4 envelope/lifecycle semantics and rerun PostgreSQL. ⬜ Vertical flow: both origins → run → finish → worker restart → one Testing Base attempt | — |
| **MF** | **Firmware run/stage association — DG1 + DG2.** Firmware half ✅ 2026-09-06; **backend half open** | LabOS + firmware | ✅ Firmware: 22 unit tests, plus both harness scenarios green — a start carries a run identity, the callback echoes it with a stable event ID, replay creates nothing, and a pre-MF response yields an UNMAPPED callback rather than a guessed run. ⬜ Backend: mint the binding on the two GETs, key the trials route on `event_id`, record unbound callbacks as unmapped. ⬜ Then re-run on a real rig | M2 identity (backend half only) |
| **M3** | All five backend workflows, review, corrections, evidence — **including DG3 capture for Impact / Forced Entry / ANSI** | LabOS | §7 acceptance cases | M2, MF |
| **MU** | **Operator interface — the A9-reduced journey in §2.** Pickers/linking, run setup, the three manual-entry screens, review, explicit earlier-attempt publishing and the sync-status chip. No Airtable-requirement verification form | LabOS | An operator completes each of the five test types end to end; Airtable identity is selected rather than retyped, while test parameters are entered in LabOS exactly as today | M3 · DG7/DG8 decided |
| **M4** | Change document with actual implementation results | LabOS | Every planned change marked applied/verified or outstanding | M1–M3 |
| **M5** | Production cutover, separately scheduled | LabOS + IFET | Schema/automation acceptance, migration rehearsal, preflight, agreed window | M4 · window |
| **M6** | Deflection calibration (legacy item 27) | LabOS | Known displacement applied to a gauge, transform identified end to end; `Deflection Value`/`Unit` unquarantined **or** the omission reconfirmed with evidence | bench/rig hardware |
| **M7** | Achieved-pressure acquisition (**legacy** gap G4 — the contract's vocabulary, not DG4; off-board item 51) | LabOS | A validated measurement source for `Max Pressure Achieved`, **or** the omission reconfirmed with evidence | bench/rig hardware |

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

| Deviation | Contract | State |
|---|---|---|
| **The three sync tables had no migration at all** — `sync_outbox`, `sync_attempt_state`, `sync_state` existed only as models. **The outbox could never have been deployed**, and the one mechanism that would have created them is `startup.sh`'s autogenerate — the same mechanism that kept the chain off this repo | §7 | ✅ `c4e1f8a92b07` |
| `enqueue()` allocates `max(seq)+1` read-then-insert; a collision fails the caller's transaction | §7.1 sequence allocation | ✅ savepoint + bounded retry |
| `claim()` leases without row locking | §7.1 exclusive claim | ✅ `FOR UPDATE … SKIP LOCKED` |
| One `leased_until` stamped per batch, then sequential sends | §7.1 lease at send time | ✅ re-asserted per send |
| No `owner_epoch` — a late lander's outcome is recorded | §7.1 fencing token | ✅ epoch bumped per claim; stale outcomes discarded |
| Lease (120 s) unrelated to the client's retry budget | §7.1 client deadline | ✅ one decision — derived from `request_budget_seconds()` (~168 s), with a test guarding the ordering |
| `/sync/status` returns `green/amber/red`, no attachment backlog | §7 status vocabulary | ✅ four contractual words + backlog; `led` retained for the deployed bundle |
| 23 tests are SQLite-only | §8 step 5 · acceptance 21–25 | ✅ one switch, both backends — 166 on PG, 157 + 9 skipped on SQLite |
| The Airtable implementation view was v0.3. `contract.py` now declares v0.4 and matches live names/types; `envelope.py` now separates create, terminal and first review and mapping no longer invents a pre-review `Retest Required = false`. Reviewer persistence and the review mutation route still do not exist | v0.4 §§4–6 | 🟡 **PARTIAL 2026-09-07.** Schema and envelope halves fixed and 200 tests + 82 subtests pass on PostgreSQL. Programme/run/mirror and reviewer persistence/API remain step 3 in §6.0; evidence: `../evidence/contract-implementation-audit-2026-09-07.md` §5 |

**Eight closed; the ninth is partial.** The field/type and envelope halves closed on 2026-09-07; persistence
and API integration must close before the vertical flow.

**The ninth found a live defect rather than just stale text.** A2 and A3 decided
`Max Pressure Achieved` and the deflection pair are never published, and nothing
enforced it: `mapping.py` emitted all three straight from the ORM, so the first
real sync would have published a target as an achievement and raw IO-Link counts
as inches. The envelope now refuses them **ahead of the pairwise rules and before
the column/JSON split**, because the contract rejects them in the JSON too —
routing an unvalidated measurement into the overflow would satisfy the letter of
"we do not publish it" while publishing it somewhere nobody looks.

**And one correction to our own reasoning.** `Required Value`/`Required Unit`
were briefly marked omitted on the grounds that A9 leaves nothing to echo back.
Wrong: A9 stops LabOS *reading* requirement values from Airtable, not publishing
the ones its own operator entered — and those are the trustworthy ones precisely
because they never went through the extractor. Both restored to the JSON valve.

**The lease number was wrong in a measurable way.** 120 s against a client whose
worst case is 5 attempts × 30 s timeout plus capped backoff with jitter plus
throttle — 168 s. A worker still legitimately sending could have its entry taken.

**One deviation was found only by running it.** On SQLite, `begin_nested()` +
`flush()` **commits** the insert, because pysqlite does not open the transaction
SQLAlchemy's SAVEPOINT support needs — so the entry survived the caller rolling
back, breaking the atomicity the module exists for. The savepoint is therefore
Postgres-only; SQLite has a single writer and no race to protect against.
Evidence: the row outlived a `session.rollback()`.

---

## 9. Airtable team — what we need, what we owe

**Environments.** Testing `app4oXS3Kd5IKWgJ7` · Production `app0OCunbmuXl7Hc9`.
Read: `IFET Projects` `tblLYcRC7q6Srjfk3` · `Mock-Ups/Specimens` `tblcrGv0WJn6FTTGO` ·
`Tests Protocols` `tblutO1Q8TNC4BLk0` · `Protocol Sections` `tblqpvuJlSdkeS9PS`.
Write: `LabOS Raw Data Table` `tblnc9SsbXU0C0FWh` — **the runtime write allowlist is this table alone.**
Schema-write credentials belong to setup, never to the runtime worker. Tokens stay server-side, out of git and
out of browser-served config.

**Schema is no longer a permission question.** LabOS is authorized to define and add the required fields in
the Testing Base with a documented change register. All 73 register rows are now **DECIDED**: 44 BASELINE,
**14 APPLIED**, 4 CONDITIONAL, 10 OMITTED and 1 PLANNED local-only. The seven former OPEN/PROPOSED rows were
settled by A9 and are deliberately omitted, not pending agreement.

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

**What we owe them:** `../correspondence/airtable-team-questions-2026-09-06.md` — **rewritten 2026-09-06 and
ready to send; still NOT SENT.** It is no longer a *planned*-change notice: the 14 fields are applied, so it
is now an **applied-change report** carrying the change document, plus the three decisions that block
DG7/DG8/DG9 and the three things we need them to do. The earlier draft still read "planned, not applied yet"
and asked none of the three questions — sending it would have understated the work and asked for permission
we already had. It also now states plainly that our verification step contradicts their "no double entry"
requirement, and why, rather than letting them discover it. `correspondence/sent/` is append-only; copy the
artifact there after an authorized send and never edit it afterwards.

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
revalidated** against MF, DG3 or the hardware dependency. No new date is committed here until M1 and M2 land;
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
  11883/18000, identity `device901`. A simulated rig must never be able to reach a real broker. §5 DG10.
- **Secrets never enter git**, and never `deployment/config/config.json` or `src/ifet_ui_react/config.json` —
  both are served to the browser.
- **Docs:** this file is the delivery authority and is edited in place. New dated `.md` files belong in
  `evidence/` and `correspondence/` only. Close open items in the authoritative document first, then views.
- **Commits** are authored `gad <abdulrahmanashraf.gad@gmail.com>` with no assistant attribution.
