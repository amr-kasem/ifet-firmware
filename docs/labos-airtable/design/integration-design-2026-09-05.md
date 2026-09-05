# LabOS ↔ Airtable — implementation design

**Decision date:** 2026-09-06 · **Status:** DESIGN DECIDED; implementation incomplete, not deployed.
**Authority:** `../contract/write-contract-v0.4.md`; **mapping view:** `field-register-2026-09-05.csv` (66 rows).
BASELINE in the register means observed field existence, not implemented code. Record IDs are API metadata;
the LOCAL_ONLY row is queue design, not a field to create. Fourteen actual field additions are planned.
The user authorized LabOS to define Testing Base additions and close the design. This replaces the previous
draft alternatives; no schema mutation or backend implementation is performed as part of this document edit.

## 1. Scope and data flow

Five test types, backend first. UI and water integration are deferred. Airtable owns assigned work; LabOS
owns procedures, execution, verdicts and originals. Read project/specimen/protocol/section fields from the
local cache; import by permanent IDs. Snapshot independently verified requirements before starting a run.
Save the run and outbox entry atomically. The separate sync service publishes a single raw-results row per
run, and Airtable automation updates operational views. Testing continues during Airtable outages.

Full reads every 60 seconds replace the speculative delta cursor. One existing PostgreSQL database and one
new service are sufficient. No additional broker, public sync port or generic schema framework.

## 2. Closed decisions A1–A8

1. **A1:** one programme run equals one Airtable attempt; stages and shots are children. Programme identity
   is stable across reruns; run identity is always new. `test_programmes` owns the unique programme tuple;
   `test_programme_runs` owns attempt identity. Never put a unique programme tuple on the run table.
2. **A2:** rig Measured Value and Max Pressure Achieved are omitted until sourced and validated. Genuine
   manually entered quantities remain allowed with units/provenance. Targets are never achieved values.
3. **A3:** all uncalibrated deflection evidence stays local. Outbound data_quality explains omissions.
4. **A4:** execution evidence freezes on termination, first verdict is recorded once, corrections create
   new immutable records referring to the original. A missing target field queues the correction.
5. **A5:** incomplete requirements warn at selection; execution requires actual independently verified
   values, verifier/time and source reference. A checkbox or provenance tag alone cannot release a rig.
6. **A6:** unsupported codes/shapes/applicability remain visible but non-executable. Codes, not names, route
   work. Legacy Value is never parsed into execution pressures. Eight typed fields are specified in contract §3.
7. **A7:** keep ProjectParent/Project database names; expose projects/specimens at the API boundary.
8. **A8:** water infiltration integration is excluded from this five-type release; existing behavior remains.

Additional defaults are also settled: Test Date is completion; explicit UTC start/end fields; declared
operator/reviewer identity; original photos local and immutable previews in Airtable; no mandatory report
link before a reachable origin exists. A not-required section receives no fabricated passing attempt.

## 3. Local entities and constraints

- `test_programmes`: UUID Test ID, specimen, primary section/type, active procedure identity.
- `test_programme_runs`: UUID Attempt ID, programme FK, atomic ordinal, frozen requirement/procedure snapshot,
  execution/first-review state, source/verification facts, correction FK and reason, data_quality.
- Existing static/cyclic stage trials link to runs without changing legacy identities or reports. Freeze an
  ordered stage plan per run; multiple child trials are retained and the chosen completion trial is explicit.
- Manual observations/shots link to the same run parent. Use typed common columns (ordinal, location,
  declared outcome, notes) and versioned detail for optional quantity/unit/source observations.
- `at_mirror_projects/specimens/protocols/sections`: base+record ID, allowlisted fields, content hash,
  successful acquisition time, relationship IDs, availability. Store import identity on the local domain rows.
- `sync_outbox`: immutable payload, attempt_seq, eligible time, lease, delivery state/error. Allocate the
  sequence in the domain transaction; exactly one sender owns an attempt at a time.
- `sync_state`: heartbeat, pull/push outcomes, mirror revision. Counts include queued/parked work and photos.
- Local evidence plus `sync_attachments`: artifact ID, full content hash, persisted preview, remote ID/state.

Database checks enforce run UUID and programme ordinal uniqueness, immutable evidence and first review.
Correction chains must not cycle. Parent references and stage section references repeat by design.
Default new local-only runs to Excluded until explicitly linked; historical rows remain Excluded dynamically,
not by hard-coded counts such as 640. Import is idempotent and rejects conflicting parent assignments.

## 4. Backend API boundary

Routes below express the logical API; use the existing application's route prefix consistently.

| Route | Behavior |
|---|---|
| GET /airtable/projects | List cached jobs, including those not imported |
| GET /airtable/projects/{rec}/specimens | Cached specimen children |
| GET /airtable/specimens/{rec}/protocols | Cached protocol children |
| GET /airtable/protocols/{rec}/sections | Cached sections with applicability/support/completeness |
| POST /airtable/refresh | Coalesce a background refresh; never a synchronous Airtable dependency |
| POST /projects/import | Import consistent project/specimen hierarchy by base+record IDs |
| POST /specimens/{id}/programmes | Create/reuse a programme from a supported primary section/type |
| POST /programmes/{id}/runs | Create a run after verifying required inputs; request idempotency key |
| GET /runs/{id} | Run snapshot, child observations, review and delivery status |
| POST /runs/{id}/stage-trials | Record a stage trial with a stable child-event ID; duplicates replay safely |
| POST /runs/{id}/observations | Record manual observation/impact shot before termination |
| POST /runs/{id}/finish | Terminate after explicit stage completion or abort reason; idempotent |
| POST /runs/{id}/verdict | First review once, with reviewer/time/rationale; no measurement edits |
| POST /runs/{id}/corrections | New attempt copying execution reference and recording corrected facts/reason |
| POST /runs/{id}/photos | Persist original evidence and preview work before review; later new evidence uses correction |
| GET /sync/status | Local state and live counts, never an Airtable call |
| GET /sync/queue | Paginated operator-visible pending/failed work |
| POST /sync/queue/{id}/retry | Re-enable eligibility; same worker/FIFO path, never direct parallel send |

All repeated creates/commands use persisted request/event IDs, not newly minted attempt IDs on every HTTP
retry. The existing firmware /trials seam needs an explicit run/stage association before integration into
real execution. An unmapped firmware callback is preserved locally and excluded, not guessed into a run.
This adaptation is implementation work; generic outbox tests do not establish it exists.

## 5. Delivery rules

Create → terminal → first review are ordered per run. Photos are a separate tracked channel; the overall
attempt is not Synced while required preview delivery is pending. Correction publication waits for both its
schema and original identity to be available. An uncertain write cannot be passed by a later phase.
Retry does not regenerate IDs, payloads, sequences or preview bytes. Park data/schema errors with evidence;
back off transient failures and stop hammering invalid credentials. Timestamp comparison is not concurrency
control. Validate lease and single-owner behavior under PostgreSQL, including worker death and slow requests.

Full reads stage results outside a DB transaction and publish atomically after all pages and relationships
validate. No deletion inference on failed/truncated reads. Differentiate removed records from changed links;
do not mutate frozen active/historical runs. Compare canonical allowlisted content so timestamps, billing
changes and field order do not cause revisions. Request only needed fields, not all customer records.

Polling rate is configurable. At current size, four pages/minute costs about 5,760 calls/day before writes;
check monthly account allowance. Refresh requests coalesce. Read and write budgets leave capacity for other
integrations. An unavailable worker is shown through a stale heartbeat; spinner is not an endless outage state.

## 6. Delivery work with decided fallbacks

- **Schema setup:** LabOS adds the contract's fields/types to Testing Base and records before/after/IDs.
  No field-design permission question remains. Test fixtures carry synthetic values and provenance.
- **Extractor:** unresolved source defect; keep independent verification. No legacy pair parser/backfill.
- **Deflection/actual pressure:** omit until a separately tested measurement source exists. Bench/rig testing
  is necessary for metrology, not for local migration or queue rehearsal.
- **Automations:** test UUID linkage, completion dates, review-only verdicts, correction supersession and
  parameter-row exclusion. Production's existing automations are not assumed compatible merely because fields exist.
- **Reports:** original/detailed data stays local. Publish external links only after access is validated.
- **Deployment:** no production experiments. Rehearse upgrade chain on local PostgreSQL, inspect current
  production alembic head at deploy, coordinate owner/window and production schema/automation delivery.

## 7. Implementation milestones

| Milestone | Deliverable | Exit evidence |
|---|---|---|
| M0 | This decided contract, field register and change notice | No unanswered design alternatives; delivery status explicit |
| M1 | Testing Base additions and synthetic linked fixture | Schema diff, field IDs, asymmetric pair, blank/N/A/unknown examples |
| M2 | Local PostgreSQL migration and first vertical flow | Import → run → finish → worker restart → one Testing Base attempt |
| M3 | All five backend workflows, review/corrections and evidence | Repeatable acceptance cases below |
| M4 | Change document with actual implementation results | Every planned change marked applied/verified or outstanding |
| M5 | Separately scheduled production cutover | Schema/automation acceptance, migration rehearsal, preflight and window |

Existing outbox code is groundwork, not proof M2 is delivered. P1 is a migration dependency and can be
rehearsed in one ordered upgrade with the new revision; it need not be deployed separately before local work.
UI development remains a later task. No email/message is sent merely by committing the notice.

## 8. Acceptance checks

1. One programme, six static or eight cyclic child stages: one Attempt ID per run, new UUID/ordinal on rerun.
2. Multiple specimens share a job ID; multiple stages/runs share section IDs; duplicate entity imports reuse IDs.
3. Concurrent run creation gives distinct ordinals, while replayed create requests return the same run.
4. Domain save and enqueue are atomic under rollback; new unlinked/historical attempts never auto-sync.
5. Network outage, bad token and stopped worker do not prevent local saves; local status reports accurate counts.
6. Lost write response, process kill, lease expiry and concurrent retry preserve per-attempt phase order.
7. Failed attempt A does not stop unrelated B; a correction never overtakes unresolved original identity.
8. First review records identity/time once; correction makes a new row and leaves original evidence unchanged.
9. Corrections do not count as physical retests; Airtable roll-ups choose the non-superseded result correctly.
10. Lost attachment response is reconciled without blind append; uncertain presence remains parked; previews
    and originals have stable IDs/hashes; missing previews keep the attempt Pending/Failed visibly.
11. More than 100 records, mid-page error, changed links and concurrent upstream edits cannot publish a partial
    hierarchy or erase history; unchanged full reads do not move the mirror revision.
12. Only allowlisted operational/testing fields enter the mirror; names and unrelated field edits cannot reroute work.
13. Unknown code/kind/option, unsupported water or Unconfirmed applicability stays visible but cannot start a run.
14. Missing values differ from zero/N/A; asymmetric positive magnitudes remain independent; no legacy Value parsing.
15. Airtable-only or merely tagged operator values cannot release a rig; actual independently verified pair,
    source reference, verifier and verification timestamp are required and frozen.
16. Cycles uses its own verified pair without requiring a duplicate Static Load row; parameters create no test rows.
17. Quarantined deflection and unavailable rig pressure are rejected everywhere in outbound JSON/scalars;
    sourced manual observations include unit/quantity; configured targets are never reported as achieved.
18. Test Date is absent at create, equals completion at terminal; start/end are UTC; corrections preserve
    original execution times; Airtable-derived local dates cross midnight/DST correctly.
19. Runtime writes to any hierarchy table or an unapproved production target are refused; schema drift fails loudly.
20. Existing legacy reports and local static/cyclic/water behavior remain intact; run/stage callback association
    is explicit, duplicate stage events replay safely, and missing telemetry cannot imply a passing test.
21. Local PostgreSQL migration rehearsal covers constraints, leases, P1 ancestry and restart behavior; SQLite-only
    tests are not accepted as proof of those guarantees. Production deployment has separate recorded checks.

## 9. Communication

`../correspondence/airtable-team-questions-2026-09-06.md` is now a planned-change notice, not a permission
request. It remains NOT SENT. Report what is designed, then actual changes with evidence after implementation.
The earlier correspondence and pre-closure contract are historical evidence, not active instructions.
