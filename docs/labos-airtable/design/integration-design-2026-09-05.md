# LabOS ↔ Airtable — Draft Design Package

**Owner:** LabOS (Abdelrahman) · **Date:** 2026-09-05 · **Status:** `DRAFT — for internal review`
**Baseline:** `../schema/baseline-2026-09-05/` (both bases, read-only, this date)
**Register:** `field-register-2026-09-05.csv`
**Builds on:** contract `v0.3` §4/§9/§10 · `../correspondence/airtable-team-questions-2026-08-31.md` §2 ·
`../evidence/labos-real-data-types-2026-08-31.md` · `../evidence/firmware-production-runtime-contract-2026-08-31.md`

---

## 0. What this is, and where each part goes

This is the design package agreed in session on 2026-09-05, covering the operator-driven test flow
(five test types), the requirements read path, and the synchronisation service.

**Nothing here has been applied.** No Airtable schema was mutated, no LabOS migration was written, no
container was built. The only action taken was the read-only baseline export.

`contract/` holds exactly one file by rule, so this package stages in `design/` until review. On approval it
splits by role:

| Part | Folds into |
|---|---|
| §2 decisions, §4 register, §6 Airtable changes | `contract/` — as write contract `v0.4` |
| §7 implementation sequence, §8 acceptance tests | `runbooks/` |
| §9 questions | `correspondence/` — the next message to the Airtable team |
| §3 gates | contract §10, as numbered open items |

---

## 1. The ownership boundary

Restated because every design choice below follows from it.

| | Airtable | LabOS |
|---|---|---|
| Project / specimen / protocol structure | **owns** | mirrors, read-only |
| What testing is required | **owns** (from HubSpot) | reads |
| Operational status, scheduling, billing | **owns** | never reads |
| Test equipment — VFD, valves, sensors, gauges | never | **owns** |
| Test execution and the detailed record | never | **owns** |
| Pass/fail verdict | never | **owns** |
| Evidence — photos, raw data, reports | receives copies | **owns the originals** |

Two rules that fall out of it:

- **Airtable never controls test equipment.** Requirements read from Airtable are displayed to the operator;
  they do not drive a rig without the §3 G3 gate being satisfied.
- **An Airtable outage never stops testing.** Enforced structurally in §5, not by careful coding.

---

## 2. Decisions settled 2026-09-05

### D1 — Deflection export is blocked pending calibration

`max_deflection` spans **−1280.91 → 1288.86** across 1127 production rows
(`evidence/labos-real-data-types-2026-08-31.md` §320). The firmware audit identified the pipeline: **raw
IO-Link counts × 0.0393701, mislabelled as inches, with the defect in the SICK gateway** rather than the
firmware. The pipeline is understood; the correct scale still requires physical measurement.

**Decision.** `Deflection Value` and `Deflection Unit` are **omitted from the payload** — not null, not zero.
`envelope.build()` **raises** if either is populated, so the block cannot be lifted by an edit that does not
know why it exists.

**The per-gauge readings stay local.** An earlier draft carried them to Airtable under
`deflection_raw_uncalibrated`, then under `sick_gateway_raw_counts`. Both names are wrong: the stored values
have *already* been multiplied by 0.0393701 and rounded, so they are neither calibrated deflections nor raw
counts, and no accurate short name exists for a number whose transform is not yet understood. Publishing a
value we cannot describe is worse than not publishing it. LabOS retains the evidence; nothing goes on the
wire until G1 closes.

This is an engineering investigation, not a value to guess. It blocks two fields and nothing else.

### D2 — The verdict stays in LabOS

Nothing in LabOS writes `TestResult.result` today; the firmware audit found Pass/Fail has no owner. Deciding
it in Airtable would contradict §1.

**Decision.** An operator-recorded verdict, with **reviewer identity and timestamp**. `Test Result` is
`Pending` until reviewed. The sync service only transports it.

New columns: `verdict_by`, `verdict_at`, beside the existing `test_result`.

### D3 — Operator is a declared identity

A rig-level name cannot identify who performed a test, and LabOS has no authentication.

**Decision.** Explicit operator selection or entry **per session**, snapshotted onto **every attempt**.
Because there is no authentication behind it, the payload says so: `identity_assurance: "declared"` inside
`Complete LabOS JSON Response`. The caveat travels with the record rather than living only in a document.

### D4 — UTC on the wire, America/New_York in reports — with one exception

**Decision.** Store and transmit UTC. Render lab reports in `America/New_York` including the offset.
Airtable's client-timezone *display* does not change the stored instant.

**The exception, and it is easy to get wrong.** `Test Date` on the raw table is `dateTime` — an instant, so
UTC is correct. But **`Testing Date` on Protocol Sections is a plain `date`**, and a date has no instant. A
test finishing 21:00 EDT is already tomorrow in UTC. Date-typed fields must therefore be rendered in
`America/New_York` **before** writing. Two rules in one payload; the register carries it per field.

### D5 — Keep the database names, fix the vocabulary at the boundary

The two systems use "project" for different things:

| Airtable | LabOS | Production count |
|---|---|---|
| Project (`IFET-25-0111`) | **`ProjectParent`** | 32 LabOS · 1 Airtable |
| Mock-Up/Specimen | **`Project`** | 79 LabOS · 6 Airtable |

**Decision.** Do not rename the tables — a migration plus UI churn for no functional gain. Every
Airtable-facing name and every API path speaks **Airtable's** vocabulary: `/airtable/projects` returns
ProjectParents, `/airtable/specimens` returns Projects. The mapping is stated once, at the top of the
register.

**Linkage is by permanent record ID, never by job name.** And note what the counts mean: **31 of 32 LabOS
jobs have no Airtable counterpart at all.** This is not a backfill exercise — there is almost nothing to
match. Linkage happens **going forward, at project-import time**; historical data stays deliberately
unlinked under the migration's existing `Excluded` marker (623 rows when written, **640** today).

**Uniqueness is per imported entity, not global.** A blanket "no Airtable record ID may be claimed by two
LabOS rows" would be wrong — and would reject correct data, since six specimens legitimately share one
project ID, and every attempt at a test legitimately repeats that test's section ID. **Parent references are
supposed to repeat.**

The full table is in **D7**, which has to be read first: it decides what a LabOS "test" *is*, and therefore
what repeats. In short — two unique keys (`project_parents.airtable_project_id`,
`projects.airtable_mockup_id`), and everything below the specimen repeats by design.

The relationship fields that carry the hierarchy — `Mock-Ups/Specimens.Project Name`,
`Tests Protocols.Mock-Up`, `Protocol Sections.Test Protocol` — are in the register as `RELATIONSHIP` rows;
they were missing from the first draft. §8 D6 tests both halves: the unique keys reject a duplicate, and the
repeating references are accepted.

### D6 — Pressures: free text preserved, typed fields for execution

**Decision.** `Value` is retained unchanged as the human-facing display string. Execution reads the typed
`Required Value Inward` / `Required Value Outward` fields proposed in
`correspondence/airtable-team-questions-2026-08-31.md` §2.2.

Until the sign convention is confirmed (§3 G2), the parser **stores and refuses**: `required_value_raw`
persists, `required_value_inward` / `required_value_outward` stay null, and nothing auto-fills a rig. Neither
the sign convention nor the section→test-type map is decided from six symmetric examples.

**The safeguard is an execution rule, not an acknowledgement.** A checkbox — even one naming the proposal
revision — is provenance, not protection. The backend **refuses to start a pressure-driven test** unless
`required_params` carries an inward/outward pair whose provenance is `proposal` or `operator`. An Airtable-
sourced value is displayed and never executed while G3 is open. Naming what was checked against ("proposal
PDF rev C, 2026-07-14") is required *in addition*, because it is the artifact you want when a result is
challenged a year later — but it is not what stops a bad test. §8 E1 and E3 test the rule, not the checkbox.

---

### D7 — Programme versus stage: what an Airtable attempt row *is*

**This has to be settled before any uniqueness constraint, because it decides what repeats.**

A LabOS `StaticTest` / `CyclicTest` row is **not** a test. It is one **stage** of a programme that LabOS
derives from the design-pressure pair — six static stages at `× [0.75, 0.75, 1.0, 1.0, 1.5, 1.5]`, eight
cyclic stages with their own factors and cycle counts. Confirmed in production on 2026-09-05:

| | min | avg | max | `preset` |
|---|---|---|---|---|
| static stages per project | **6** | 6.43 | 9 | 498 / 508 |
| cyclic stages per project | **8** | 8.03 | 9 | 632 / 634 |
| trials per static stage | 1 | 1.16 | 2 | — |

Airtable's `DP (+) (PSF)` is **one Protocol Section**. LabOS expands it into **six** stages, each with its own
trials. So section : stage is 1 : 6, and section : trial is 1 : ~7.

**Decision — one Airtable attempt row per programme run, not per stage.**

`Protocol Section` carries a singular `LabOS Attempt ID` and a `Latest LabOS Attempt Number`; their table is
shaped for one result per requirement line. Sending six stage rows would answer none of the operational
questions Airtable exists to answer ("is static load done on Fixed Window 3, pass or fail?") without forcing
them to build a roll-up — and §1 says roll-ups are theirs, not something we should oblige them to write to
get a basic answer. It is also the same call already made for impact shots: **one attempt, many children,
detail in the JSON valve.**

Consequences, and they are not small:

- A new LabOS entity, `test_programme_runs`: one row per run of one section's programme, identified by
  `(project_id, airtable_section_id)`. It carries `labos_test_id`, `labos_attempt_id`, `attempt_number`,
  status and the terminal roll-up.
- **`labos_test_id` identifies the programme, not the stage.** `labos_attempt_id` identifies one *run* of it.
- Existing stage trials (`StaticTestResult` / `CyclicTestResult`) become **children** of a run. They keep
  their own rows and their own detail; they simply stop being what gets sent.
- `envelope_values()` maps from **the run**, not from a trial. This revises P1's mapping — cheap now, since
  nothing is deployed, and expensive later.
- Per-stage results go to `Complete LabOS JSON Response`.

**What this does to uniqueness** — the reason it had to come first:

| | Rule |
|---|---|
| `test_programme_runs.labos_attempt_id` | **unique** |
| `(project_id, airtable_section_id)` | identifies a programme; `labos_test_id` unique per programme |
| `tests.airtable_section_id` | **repeats** — 6 stages descend from one section |
| `test_programme_runs.airtable_section_id` | **repeats across runs** — one per retest |

The rule stated in D5's first draft — "`tests.airtable_section_id` unique across test rows" — was wrong, and
would have rejected every correctly derived programme.

---

## 3. Unresolved gates

Five, each with one owner. None blocks the others.

| | Gate | Owner | Blocks | Unblocked by |
|---|---|---|---|---|
| **G1** | Deflection calibration — what is `max_deflection` actually in? | **LabOS** | `Deflection Value` + `Deflection Unit` | A known displacement applied to a gauge. **Needs a rig.** |
| **G2** | Sign convention for `+110/110`, and ratification of the section→kind map | **Airtable team** | typed pressure execution | One answer to §9 Q1–Q2 |
| **G3** | Extraction defect — contract §10.19 | **Airtable team** | driving a rig from Airtable values | Their extractor fix |
| **G4** | **No measurement source for pressure** | **LabOS** | `Max Pressure Achieved`, and `Measured Value` for rig tests | A firmware change, or an agreed derivation |
| **G5** | `Corrects Attempt ID` absent from both bases — contract §10.14 | **Airtable team** | distinguishing a correction from a retest | Field delivery |

### 3.1 G4 — the gap the register exposed

Verified in `../evidence/firmware-production-runtime-contract-2026-08-31.md` §710–715: the firmware →
Management trial payload is **exactly one field**, `deflections: List[DeflectionCreateSchema]`. No pressure,
no duration, no cycles, no timestamps, no pass/fail.

So `Max Pressure Achieved` has **no source at all**, and `Measured Value` has one only for operator-entered
manual tests. The configured setpoint is not a substitute: static pressure is driven **open-loop from a
browser slider**, so what the rig configured and what it achieved are different numbers by construction.

Both fields are therefore omitted, on the same terms as deflection. Two rows this register originally marked
`AGREED` were unsourced — the register found it, which is what a register is for.

**G1 needs a rig, and both rigs are production.** The `test` node has been offline since ~2026-07-24.
That makes three things now waiting on it — G1, sync rehearsal, and migration verification — which is worth
raising with the manager as **one** ask rather than three.

### 3.2 A completeness check that catches half of G3's symptoms

The production base holds 6 specimens × 9 sections. Three of six specimens have **no TAS-202 requirements at
all**, while all six carry TAS-203 cyclic pressures:

```
                    spec-1  spec-2  spec-3  spec-4  spec-5  spec-6
TAS-202 DP (+)      +75/75    —       —       —    +75/75  +110/110
TAS-202 Water        11.25    —       —       —     11.25     8.25
TAS-202 # Dials          1    —       —       —         1        1
TAS-202 Static/Type   Full    —       —       —      Full     Full
TAS-203 Cyclic      +75/75  +75/75  +75/75 +110/110 +75/75  +110/110
```

**State this at the right strength.** In *LabOS's* execution model, TAS-203 cyclic pressures are derived from
the TAS-202 design-pressure pair, so a specimen with `Cyclic` present and `DP` absent **cannot be executed** —
the required input is missing. That is a **completeness check on LabOS's inputs**, and it is certain.

It is *not*, on its own, proof of an extraction defect. That inference needs a premise we have not confirmed:
that Airtable's own model also requires `DP` whenever `Cyclic` is populated. Until they confirm the
cross-protocol requirement (§9 Q2), the correct claim is the narrower one.

So this refines — but does not overturn — the claim we have repeated since 2026-08-23: *"every shifted value
is individually plausible."* True of a **shifted** value. A **missing** one is at least visible, and it
happens to coincide with 3 of the 6 specimens here.

**Design consequence.** The mirror computes a per-specimen `requirements_completeness` verdict and the picker
surfaces it before selection. It **warns** rather than blocks — the cause is upstream of LabOS. But
acknowledgement alone is not the safeguard; §2 D6 and §8 E1 put the real bar on execution.

---

## 4. The field register

`field-register-2026-09-05.csv` — 58 rows, one per field, both directions.

Columns: `direction · airtable_table · airtable_field · airtable_type · labos_source · write_phase · rule ·
status · gate`.

- **`status`** is `AGREED` (no dependency), `PROPOSED` (specified by us, awaiting their agreement), or
  `BLOCKED` (named gate).
- **`write_phase`** is the §5.2 phase a field is written in.
- The register is keyed on **field names**, not IDs — field IDs differ between the two bases. The ID maps are
  *captured artifacts* in `../schema/baseline-2026-09-05/`, never hand-typed.

### 4.1 Schema changes the Airtable team already shipped

Diffing today's baseline against `../schema/schema-production-2026-08-23.json`:

| Change | Effect |
|---|---|
| `Test Type` now offers all five options, **both bases** | **Contract §10.17 closes.** The P0 blocking every manual-test write is gone. |
| `Test Date` → `dateTime` | **§10.20 closes.** §10.13 survives — one instant cannot hold start *and* end. |
| `Correction Reason` added (multilineText) | §10.14 narrows. `Corrects Attempt ID`, `Test Name`, `Abort Reason` remain absent. |

Nothing else moved. Raw table: 29 → 30 fields.

---

## 5. Architecture

### 5.1 Shape

A new `sync-service` container in the existing management compose project. Same Postgres, own tables, **no
exposed port**.

```
report-api ──one transaction──▶ [attempt row] + [sync_outbox row]
                                                      │
sync-service ── pusher ───────────────────────────────┘──▶ Airtable
             └─ puller ◀── 60 s, full read of the 4 tables, hash-compared ────┐
                    │                                                         │
                    ▼                                                         │
              [at_mirror_*] ◀── report-api serves the picker from here ───────┘

browser ──1 Hz──▶ report-api  GET /sync/status   (reads sync_state + live COUNT)
```

**Transactional outbox is the load-bearing idea.** Saving a result writes the attempt *and* its queue entry
in one commit. Either both land or neither does. Airtable being unreachable is then structurally incapable of
losing a result — the row is already durable and the pusher drains it when the network returns. §1's second
rule, enforced by the database rather than by discipline.

**`/sync/status` is served by report-api, not by sync-service.** It reads the `sync_state` row and computes
queue depth with a live `COUNT(*)`. So a stopped sync container still produces a useful answer: stale
heartbeat, red LED, and a queue depth that is still **true** — a depth cached by the worker is exactly the
number that goes wrong when the worker dies. No extra port, no proxy, no CORS.

| LED | Condition |
|---|---|
| spinner | report-api unreachable — the only real "cannot fetch" |
| 🟢 green | heartbeat fresh, last pull OK, queue empty |
| 🟡 amber | queue has pending entries — **testing continues normally** |
| 🔴 red | heartbeat stale, or last pull/push failed. Shows age of last good sync |

The browser polls **LabOS** at 1 Hz; **LabOS** polls Airtable at 60 s. Airtable's limit is 5 req/s per base —
a 1 Hz browser poll straight to Airtable would burn 20% of the lab's entire budget per open tab.

### 5.2 An attempt row is eventually complete

It reaches Airtable in up to four writes, all upserting the same record on `LabOS Attempt ID`:

| Phase | When | Carries |
|---|---|---|
| `create` | attempt starts | identity, linkage, type, `In Progress`, dates, operator |
| `terminal` | completes or aborts | measurements, notes, `Completed`/`Abborted`, `Test Result = Pending` |
| `verdict` | reviewer records it (D2) | `Test Result`, `Retest Required`, `verdict_by`, `verdict_at`, **and a rewritten JSON valve**. Never `Correction Reason` — see §5.2.1 |
| `attachment` | photo upload | `LabOS Photos` |

**This amends contract v0.3's write-once/terminal rule** — the record upsert is terminal for field *values*;
verdicts and attachments are later phases that may lag. One rule covering two cases, rather than an exception
for attachments.

Four rules make the phase model safe:

1. **The JSON valve is rewritten at `verdict`, not only at `terminal`.** Written once at terminal it would
   permanently predate the review it is supposed to record.
2. **Measurements freeze at `terminal`.** A verdict write may add verdict fields and notes; it may never
   alter a measured value. Enforced in the envelope, not by convention.
3. **The `verdict` phase is one-shot.** It moves `Pending` to a verdict, once. See §5.2.1 — a correction is
   never a rewrite.
4. **Monotonic guard.** Every payload carries `labos_updated_at`; the pusher drops any entry older than what
   the record already holds. This is the defence against a *duplicate* delivery of something we believed
   failed. It is **not** the ordering mechanism — that is §5.2.2.

`verdict_by` / `verdict_at` are proposed as typed fields (§6.2) and ship inside the JSON valve until those
exist — a verdict whose author is not on the wire is not an auditable verdict.

### 5.2.1 Corrections are immutable — a correction is a new attempt

The earlier draft had `review_kind = correction` rewriting the verdict on the same record. That contradicts
the append-only attempt model: it destroys what was originally recorded, which is the one thing an audit
trail exists to preserve.

**A recorded verdict is never edited.** `verdict_at` is set once; the transition is enforced in the database,
not by convention. If the verdict was wrong — or the data behind it was — LabOS mints a **new attempt**:

| | Corrected attempt | Correcting attempt |
|---|---|---|
| `labos_attempt_id` | unchanged | **new** |
| `labos_test_id` | unchanged | **same** — it is the same test |
| `Attempt Number` | unchanged | next in sequence |
| `Corrects Attempt ID` | — | the corrected attempt's id (**G5**) |
| `Correction Reason` | — | required |
| verdict, measurements | **frozen as recorded** | the corrected values |

So `Corrects Attempt ID` and `Correction Reason` are written at the **`create`** phase of the *new* row, not
at the `verdict` phase of the old one. The register carries them that way.

**This is why G5 blocks more than it looks like it does.** Without `Corrects Attempt ID`, a correcting attempt
is indistinguishable from an ordinary retest — same test id, higher attempt number, no way to say *why*. And
`Correction Reason`, which they did deliver, has nothing to point at. Until G5 closes, LabOS records the
correction locally and the Airtable row shows only a retest.

There is deliberately **no grace window** for fixing a mis-click. A rule that depends on how long ago
something happened, or on whether a network call had completed, is a rule nobody can audit.

### 5.2.2 Delivery is ordered per attempt, parallel across attempts

The phases in §5.2 are **not independent**. If `terminal` fails and `verdict` succeeds, Airtable holds a
verdict with no measurements behind it — a record that looks complete and is not. Last-write-wins does not
prevent this; only ordering does.

**The outbox is a set of per-attempt FIFO queues, not one global queue.**

- Every entry carries `attempt_seq`, monotonically increasing **within one attempt**, assigned in the same
  transaction that enqueues it.
- The pusher delivers an attempt's entries **strictly in `attempt_seq` order**.
- A failure **head-of-line blocks that attempt only.** Entry `n+1` waits for `n`. Other attempts are
  unaffected — a single poisoned record must never stall the lab.
- Retries preserve position; the entry stays at the head until it succeeds or is parked.
- **No cross-phase coalescing.** Collapsing a pending `terminal` and `verdict` into one write would drop
  whichever fields the later payload omits. Only repeated attempts at the *same* entry collapse, which is
  what a retry already is.
- After `max_attempts`, the entry is **parked**, not dropped: the attempt's queue stops, `/sync/status` shows
  it, and `POST /sync/queue/{id}/retry` resumes it. Silent discard is the one failure mode that loses a
  result.

The §5.2 monotonic guard stays, doing a different job: ordering stops *us* from sending out of sequence; the
guard stops a **duplicate** of something we believed failed from overwriting newer state.

### 5.3 Pusher

- Idempotent **upsert on `LabOS Attempt ID`** — makes a retry after an ambiguous timeout safe, and satisfies
  "never create duplicate records".
- Exponential backoff; retry classes per contract v0.3.
- **Attachments need separate tracking, and local state is not enough.** `uploadAttachment` is **not
  idempotent** — re-running after an ambiguous timeout appends a *second* copy. A local
  `(attempt_id, local_file)` table records what we *believe* we uploaded, which is precisely the thing an
  ambiguous timeout leaves unknown: Airtable may have accepted the bytes and lost the response.

  So the protocol is **remote-authoritative**:

  1. Each photo gets a **deterministic filename** derived from its content —
     `{labos_attempt_id}__{sha256[:12]}.jpg`. That is the persistent artifact ID, and it is identical whether
     computed before or after a failed attempt.
  2. `sync_attachments` records `(attempt_id, sha256)` → `airtable_attachment_id`, `state`, `last_attempt_at`.
  3. **Before any retry, read the record's attachment field and match by filename.** Present → record the
     returned attachment ID and mark done, no upload. Absent → upload.

  Only step 3 closes the ambiguous-timeout case; steps 1–2 exist to make step 3 cheap and unambiguous.
- Photos are **downscaled LabOS-side** to a web-sized JPEG under the 5 MB direct-upload cap. LabOS keeps the
  original. This removes the large-file delivery problem rather than solving it, and needs no publicly
  reachable LabOS.

### 5.4 Puller — full reads, not delta polling

**Delta polling is not implementable against this base, and an earlier draft of this document assumed it
was.** The baseline settles it:

| Table | Whole-record modification timestamp |
|---|---|
| IFET Projects | **no** — `Project Status Modified Time` is `lastModifiedTime` **scoped to one field** (`referencedFieldIds`), so it tracks Project Status and nothing else |
| Mock-Ups/Specimens | **none** |
| Tests Protocols | **none** |
| Protocol Sections | **none** |

A cursor built on any of these would silently miss every requirement edit — exactly the change LabOS most
needs to see.

**Design: paginated full reads of the four tables, with local comparison.** The volume makes this a
non-issue: production holds **1 project + 6 specimens + 24 protocols + 54 sections = 85 records**, four
requests at 100 records per page. At 60 s that is ~0.07 req/s against a 5 req/s ceiling.

- Each record is hashed on its field content; the mirror upsert is a no-op unless the hash changed, and only
  a real change bumps the `revision` the UI polls.
- **Checkpoint semantics still apply** — the mirror is committed only after the whole cycle processes
  successfully, so a crash mid-pull re-reads rather than half-applying.
- **Deletes fall out for free.** A full read enumerates every live record ID, so absent mirror rows are
  marked `unlinked_at` on every cycle rather than needing a separate daily reconciliation — **soft, never
  hard**, since a completed attempt may reference one.
- 60 s, configurable. Queued **"Refresh now"**.

**Revisit only if volume justifies it.** Incremental polling becomes worth its complexity somewhere around
10⁴ records, and it needs a whole-record timestamp that does not exist today. If the Airtable team adds an
unscoped `Last Modified Time` to the four tables, this section is the one to reopen.
- **Requirements snapshot.** At attempt creation the mirror's section values are frozen into
  `required_params`, with **per-value provenance** — `airtable` / `operator` / `proposal` — plus the source
  record IDs, the mirror's **content hash** for each, and the timestamp of the pull that produced it. (Not a
  source `lastModifiedTime`: the base does not publish one, which is the same finding that forced full reads
  above.) A later Airtable edit can then never retroactively change what a test was run against, and a report
  can *prove* which numbers drove the rig. This is what makes G3 auditable after the fact instead of a
  procedure we hope was followed — and it is where §2 D6's execution rule reads its provenance from.

### 5.5 Rate budget

One shared token bucket. Ceiling is 5 req/s per base; **we cap our steady state at ~3 req/s** so other
Airtable integrations are not starved. **Pusher preempts puller** — results out beat requirements in.

---

## 6. Proposed changes — not applied

### 6.1 LabOS schema (one Alembic revision, on top of the undeployed P1 revision)

| Object | Purpose |
|---|---|
| `sync_outbox` | the transactional queue |
| `sync_state` | worker heartbeat, checkpoints, last pull/push outcome |
| `sync_attachments` | attachment dedup, `(attempt_id, local_file)` → `airtable_attachment_id` |
| `at_mirror_projects` / `_specimens` / `_protocols` / `_sections` | read-only mirror, `unlinked_at` soft delete |
| `test_programme_runs` | **D7** — one row per run of one section's programme; what actually syncs |
| `impact_tests` / `forced_entry_tests` / `ansi_z97_tests` | three thin tables carrying `AirtableProtocolRef` |
| `ImpactTestResult` / `ForcedEntryTestResult` / `AnsiZ97TestResult` | `TestResult` subclasses |
| `impact_shots` | one attempt → many shots |
| `test_results.verdict_by`, `.verdict_at` | D2 · set-once, enforced in the database (§5.2.1) |
| `sync_outbox.attempt_seq` | §5.2.2 — per-attempt FIFO ordering |

**Manual tests go on the existing attempt spine**, so they inherit `labos_attempt_id`, `labos_test_id`,
retest grouping, `airtable_sync_state` and the envelope mapper. One mapper covers five test types instead of
two.

**Legacy `MissileImpactTest` / `Shot` are left untouched** — they feed `/projects/{id}/report` (main.py
993–1009). Backfill is a later decision, not a prerequisite.

**Shots are not flattened onto the attempt row.** A single scalar on the attempt cannot express one attempt →
many shots; shot detail goes to `Complete LabOS JSON Response` with `Impact Result` carrying the roll-up.
Per-shot visibility on their side would need a child table, which is theirs to own.

### 6.1.1 Endpoints

All served by report-api. The picker reads the **mirror**, never Airtable directly, so it works offline.

| Endpoint | Purpose |
|---|---|
| `GET /airtable/projects` | picker level 1 — returns ProjectParents (D5 vocabulary) |
| `GET /airtable/projects/{rec}/specimens` | picker level 2 |
| `GET /airtable/specimens/{rec}/protocols` | picker level 3 |
| `GET /airtable/protocols/{rec}/sections` | picker level 4, with `requirements_completeness` per §3.2 |
| `POST /airtable/refresh` | queue a "Refresh now" pull |
| `POST /projects/import` | materialise a LabOS project from `{project_rec, mockup_rec}`; enforces D5 uniqueness |
| `POST /projects/{id}/{impact\|forced-entry\|ansi-z97}-tests` | create a manual test bound to a section |
| `POST /…/{test_id}/trials` | create an attempt — mints `labos_attempt_id` on the programme run (D7), freezes `required_params` |
| `POST /…/trials/{attempt_id}/correct` | §5.2.1 — mints a **new** attempt carrying `Corrects Attempt ID`; never edits the original |
| `POST /…/trials/{attempt_id}/shots` | append a shot to an impact attempt |
| `PUT /…/trials/{attempt_id}/finish` | terminal write |
| `PUT /…/trials/{attempt_id}/verdict` | D2 — one-shot; records verdict, `verdict_by`, `verdict_at` |
| `POST /…/trials/{attempt_id}/photos` | upload evidence to LabOS; queues the attachment phase |
| `GET /sync/status` | the 1 Hz poll |
| `GET /sync/queue` · `POST /sync/queue/{id}/retry` | operator-visible queue and manual retry |

### 6.2 Airtable Testing Base changes

**Additive only.** Never repurpose or delete an existing field — their automations and roll-ups attach to
them and we cannot see what breaks. `Value` and `Photos` are both **retained unchanged**.

| Table | Field | Type | Why |
|---|---|---|---|
| Protocol Sections | `Requirement Kind` | singleSelect | makes the EAV row self-describing |
| Protocol Sections | `Required Value` | number | Magnitude / Count kinds |
| Protocol Sections | `Required Value Inward` | number | **G2** |
| Protocol Sections | `Required Value Outward` | number | **G2** |
| Protocol Sections | `Required Unit` | singleSelect | `PSF · in · s · cycles · impacts` |
| LabOS Raw Data | `LabOS Photos` | multipleAttachments | beside `Photos`, not replacing it |
| LabOS Raw Data | `LabOS Verdict By` | singleLineText | §5.2 — a verdict without an author is not auditable |
| LabOS Raw Data | `LabOS Verdict At` | dateTime | §5.2 |
| LabOS Raw Data | `Corrects Attempt ID` | singleLineText | **G5** · contract §10.14 — asked for since v0.2 |

**Two constraints on delivery:**

1. **Our production PAT cannot write schema** (`schema.bases:read` only). Every field we add in testing must
   be **re-applied by the Airtable team in production**. The change register is therefore not a courtesy
   write-up — it is the *delivery mechanism*, and it must be executable by them, with a rollback note per
   change.
2. **The update-field API does not expose type conversion.** Confirmed against their documentation. So
   nothing changes type; typed requirements are new fields beside the old ones. This is why §6.2 is additive
   by construction rather than by policy.

---

## 7. Implementation sequence

| | Step | Depends on | Gate |
|---|---|---|---|
| **S0** | Baseline export, both bases | — | ✅ **done 2026-09-05** |
| **S1** | This package: register, decisions, contract `v0.4` delta | S0 | ← **review here** |
| **S2** | Send §9 questions (Q1–Q10) to the Airtable team | S1 | works **G2, G3, G5** |
| **S2b** | Decide G4 — either a firmware change to report achieved pressure, or an agreed derivation, or the two fields stay omitted | S1 | **ours**; independent of S2 |
| **S3** | Testing Base changes + change register | S2 for the typed fields; `LabOS Photos` can go earlier | |
| **S4** | LabOS migration: outbox, mirror, `test_programme_runs`, manual-test models, verdict columns | S1, **D7** | **P1 migration + `startup.sh` must ship first** |
| **S5** | `sync-service` container + `/sync/status` in report-api | S4 | |
| **S6** | Manual-test endpoints — no longer blocked, §4.1 | S4 | |
| **S7** | Acceptance suite, §8 | S5, S6 | |
| **S8** | Final change document to the Airtable team | S3, S7 | |

**UI work stays deferred**, as agreed. The React source exists nowhere — repo, node, or upstream GitHub — but
is recoverable from the deployed bundle's sourcemap (`sourcesContent` present, 56 app files, bundle hash on
the node matches the repo). A git repository is expected to be supplied later; the backend is built so the UI
is the only remaining piece.

### 7.1 Deployment notes

- **Adding a container does not restart existing ones.** `docker compose up -d sync-service` creates only the
  new service. The caveat: compose *will* recreate a sibling whose resolved config hash changes, so add the
  service without touching shared anchors or env, and verify with `--no-recreate` before the real run.
- **Migration compatibility drives sequencing, not the container add.** The undeployed P1 revision plus the
  `startup.sh` fix must ship before S4's revision reaches production — until `startup.sh` lands, every restart
  appends a no-op revision and moves the head. Re-confirm `SELECT * FROM alembic_version;` returns
  `3a65a83e0463` immediately beforehand. **Re-verified 2026-09-05: still `3a65a83e0463`.**
- **Rehearse on synthetic fixtures.** A protected production restore only where migration verification
  requires it — better on privacy grounds too, given what §7.2 describes.

### 7.2 Disclosure

Both LabOS repositories are **public on GitHub**. `IFET Projects` records carry customer names, contact
emails, proposal amounts, balances and QuickBooks invoice IDs.

- **Schema** (table/field IDs, names, types, options) → committed. It must be: the per-base ID maps cannot be
  hand-typed and the change register diffs against them.
- **Records** → outside every work tree, at `~/AWS/ifet-project/airtable-baseline-2026-09-05/`.

`app/airtable/baseline.py` **refuses** to write record CSVs into a git work tree unless explicitly overridden.

---

## 8. Acceptance tests

Grouped by the guarantee each defends. A–C and E are the ones that would let a real defect reach a customer.

### A — Identity and idempotency

| | Test | Pass |
|---|---|---|
| A1 | Sync the same attempt twice | exactly one Airtable record |
| A2 | Kill the response after a successful write, then retry | no duplicate — upsert on `LabOS Attempt ID` |
| A3 | Two attempts at one test | two records, shared `LabOS Test ID`, `Attempt Number` 1 and 2 |
| A4 | Concurrent pusher and manual retry on one entry | one record, one write wins, no error surfaced to the operator |

### B — Offline resilience (the headline guarantee)

| | Test | Pass |
|---|---|---|
| B1 | Revoke the token mid-test | result saves locally, LED amber, queue grows, **test completes normally** |
| B2 | Restore the token | queue drains, records land, LED green, **zero duplicates** |
| B3 | Stop the sync container entirely | `/sync/status` still answers; heartbeat stale, LED red, **queue depth still accurate** |
| B4 | Kill the container mid-push | on restart the in-flight entry is retried — not lost, not duplicated |
| B5 | Airtable returns 429 under sustained load | backoff, no queue entry lost, steady state stays ≤3 req/s |

### C — Eventually-complete writes

| | Test | Pass |
|---|---|---|
| C1 | `create` → `terminal` → `verdict` → `attachment` | one record; each field appears at its register-declared phase |
| C2 | Verdict recorded before the photo uploads | both land, order-independent |
| C3 | **Airtable accepts an upload but the response is lost**, then retry | **exactly one** attachment — the retry lists the record's attachment field, matches the deterministic filename, and skips the upload. Local state alone must *not* be what decides |
| C4 | Attempt aborted before terminal | `Abborted`, `Test Result` stays `Pending` |
| C5 | Duplicate delivery of a `terminal` we believed failed, after a `verdict` landed | dropped by the monotonic guard — the record keeps its verdict, not `Pending` |
| C6 | Verdict write attempts to alter a measured value | rejected — measurements freeze at `terminal` |
| C7 | JSON valve after a verdict | rewritten; contains `verdict_by`, `verdict_at` |
| C8 | **Re-record a verdict on an attempt that already has one** | **rejected** — `verdict_at` is set once (§5.2.1) |
| C9 | Correct a verdict | a **new** attempt: new `labos_attempt_id`, **same** `labos_test_id`, next `Attempt Number`, `Corrects Attempt ID` → the original, `Correction Reason` required. The corrected row is **byte-identical** afterwards |
| C10 | Correcting attempt enqueued while G5 is open | LabOS records it locally; the Airtable row shows a retest; no silent overwrite of the original |

### C′ — Per-attempt delivery ordering (§5.2.2)

| | Test | Pass |
|---|---|---|
| C′1 | `terminal` fails, `verdict` already queued | `verdict` **does not** overtake it — no record with a verdict and no measurements |
| C′2 | Attempt A head-of-line blocked | attempts B, C keep delivering — one poisoned record never stalls the lab |
| C′3 | Pending `terminal` and `verdict` for one attempt | delivered as **two** writes; no cross-phase coalescing that would drop fields |
| C′4 | Repeated retries of one entry | collapse to one delivery; position in the queue is preserved |
| C′5 | Entry exceeds `max_attempts` | **parked, not dropped** — visible in `/sync/status`, resumable via `POST /sync/queue/{id}/retry` |
| C′6 | Restart mid-queue | `attempt_seq` order resumes exactly where it stopped |

### D — Read side and mirror

| | Test | Pass |
|---|---|---|
| D1 | Table with >100 records | full `offset` pagination, no gaps |
| D2 | A field with **no** modification timestamp is edited | picked up next cycle — the puller does full reads, not delta (§5.4) |
| D3 | Crash mid-pull | mirror not committed; next run re-reads |
| D4 | Record deleted in Airtable | `unlinked_at` set, **not** hard-deleted; a referencing attempt stays intact |
| D5 | Section `Value` changed after attempt creation | the attempt's `required_params` snapshot is **unchanged** |
| D6a | Two LabOS projects claiming one `airtable_mockup_id` | **rejected** |
| D6b | Six LabOS projects sharing one `airtable_project_id` | **accepted** — parent references repeat |
| D6c | Six static stages sharing one `airtable_section_id` | **accepted** — D7; the stage is not the section |
| D6d | Two programme runs of one section | **accepted**; two runs sharing a `labos_attempt_id` — rejected |
| D7 | Import a project | linkage by permanent record ID; a job-name-only match is refused |
| D8 | Unchanged pull cycle | no mirror write, `revision` does not move, UI does not refetch |

### E — Integrity gates

| | Test | Pass |
|---|---|---|
| E1 | Specimen with `Cyclic` present, `DP` absent | completeness warning surfaced; **and starting a pressure-driven test is refused** until a verified pair is entered |
| E1b | Verified pair entered, provenance `proposal` | execution permitted; the checked-against reference is recorded |
| E1c | Pressure-driven test started from an **Airtable-sourced** pair while G3 is open | **refused** — display only |
| E2 | Something populates `Deflection Value` | `envelope.build()` **raises**; payload omits both deflection fields, and carries no substitute under any other name |
| E3 | Sign convention unresolved | `required_value_raw` stored; inward/outward null; nothing auto-fills a rig |
| E7 | Something populates `Max Pressure Achieved` | **raises** — G4, no measurement source |
| E4 | Write attempted on any table but `tblnc9SsbXU0C0FWh` | client raises — allowlist |
| E5 | Write attempted on the production base | refused unless `AIRTABLE_ALLOW_PRODUCTION_WRITE` |
| E6 | Unit written as `Inches` | rejected — vocabulary is `in` |

### F — Time

| | Test | Pass |
|---|---|---|
| F1 | Any `dateTime` field | UTC, ISO-8601 with `Z` |
| F2 | Test completes 21:00 EDT | `Testing Date` (a `date`) files as **that** local date, not next-day UTC |

### G — Non-regression

| | Test | Pass |
|---|---|---|
| G1 | `/projects/{id}/report` | unchanged — legacy `MissileImpactTest`/`Shot` untouched |
| G2 | `docker compose up -d sync-service` | no existing container recreated (`--no-recreate` verified) |
| G3 | Existing static/cyclic flows with sync disabled | unchanged behaviour |
| G4 | 640 historical attempts | remain `Excluded`, never synced |

---

## 9. Questions for the Airtable team

**Q1 — sign convention.** `DP (+) (PSF)` reads `+110/110` and `+75/75` in the production base. We read that
as `+inward / outward`, both positive magnitudes in PSF. Is the second number ever negative-signed in other
jobs? Every example available to us is symmetric, so the data cannot answer this and we will not infer it.

**Q2 — ratify the section→kind map.** `correspondence/airtable-team-questions-2026-08-31.md` §2.4 maps the
nine live `Section Name` values to `Requirement Kind` + `Required Unit`. Confirm, and confirm the list is
closed — a tenth section name appearing later would silently change what LabOS reads.

**Q3 — the five typed fields on `Protocol Sections`** (§6.2). Their §2.3 alternative — one
`Required Testing Parameters (JSON)` long-text field — remains acceptable to us and worse for them: JSON in
long text cannot be filtered, sorted, grouped or rolled up, and their own interface pages cannot show it.

**Q4 — `LabOS Photos` as an attachment field** beside the existing `Photos` url field, which we are not
touching.

**Q5 — production replication.** Our production PAT is `schema.bases:read`. Confirm who applies the agreed
changes to the production base, and when, since acceptance testing cannot conclude there without them.

**Q6 — still open from 2026-08-31, unaffected by their recent changes:** `Corrects Attempt ID` (**G5**,
§10.14) — `Correction Reason` arrived without it, and a reason with nothing to point at is not a correction
record. And **the extraction defect (§10.19)**, unrepairable on our side.

**Q7 — which sections is LabOS expected to produce results for?** `# Dials = 1` is a gauge count and
`Static / Type = Full` is a programme selector; neither is a test, yet both carry `Result` and `Status`. If
LabOS should not write results for parameter-bearing sections, say which of the nine are which.

**Q8 — what does `Protocol Section.Result` mean?** On `Fixed Window - 6` all nine sections read `Passed` /
`Completed`, **including three whose requirement value is blank** (`Impact`, `Forced Entry (*)`,
`SMI (impacts)`). That is an inconsistency we can see, not a semantics we can infer — hence the question. It
matters because your automation rolls LabOS attempts up into this field: if `Passed` sometimes means "row
closed", a LabOS verdict and an operational state merge silently.

**Q9 — is there a whole-record `Last Modified Time` available on the four read tables?** Today the only
`lastModifiedTime` fields in the base are *field-scoped* (`Project Status Modified Time` watches Project
Status alone), so LabOS reads all four tables in full every cycle. That is fine at 85 records and would not
be at 10⁴. Not blocking — worth knowing before volume grows.

**Q10 — does your model require `DP` whenever `Cyclic` is populated?** §3.2 rests on it. If yes, three of the
six live specimens are provably incomplete. If no, our check is narrower than we think.

---

## 10. Deliberately not in this package

- **Water infiltration.** It is a TAS-202 section (`Water (PSF)`) and LabOS already runs it as a 900 s static
  hold at 0.15 × inward DP — but it is **not one of the five test types** and is explicitly **out of scope**
  for this expansion unless separately agreed. Naming it here so it is a decision rather than an oversight.
- **UI design and implementation** — deferred by agreement. §7 notes the source-recovery position.
- **Any schema mutation, in either system.** Nothing has been applied.
- **Backfill of the 640 historical attempts.** They stay `Excluded`; §8 G4 defends it.
- **A pass/fail derivation rule.** D2 puts the verdict with a human; inventing a rule inside a sync service
  is how you get a wrong verdict with an audit trail behind it.
- **Report-link reachability.** A real open issue, separate from attachment delivery, and not solved here.
