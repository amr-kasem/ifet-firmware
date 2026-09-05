# LabOS ↔ Airtable integration contract — v0.4

**Owner:** LabOS (Abdelrahman) · **Decision date:** 2026-09-06
**Status:** DESIGN DECIDED for the initial implementation; NOT APPLIED or production-validated.
**Authority:** the user authorized LabOS to define/add the required fields and types in the Testing Base,
with a documented change register. This is not a claim of counterparty ratification or deployment approval.
**Supersedes:** v0.3 and the open alternatives in the September 5–6 design drafts.
**Amended 2026-09-06** — §7.1 concurrency mechanisms, §8 sequencing, §10 measurement milestones. Delivery
mechanism only: **A1–A8 and the wire envelope are unchanged, and `Schema Version` stays `0.4`.**

## 0. Scope and environments

Five workflows: Static Load, Cycles, Impact, Forced Entry, ANSI Z97.1. UI work and water infiltration
integration are deferred. Existing local water workflows remain unchanged. Historical attempts are excluded
from automatic synchronization; no name-based backfill.

Testing: `app4oXS3Kd5IKWgJ7`. Production: `app0OCunbmuXl7Hc9`.

| Table | ID | Runtime access |
|---|---|---|
| IFET Projects | `tblLYcRC7q6Srjfk3` | read |
| Mock-Ups/Specimens | `tblcrGv0WJn6FTTGO` | read |
| Tests Protocols | `tblutO1Q8TNC4BLk0` | read |
| Protocol Sections | `tblqpvuJlSdkeS9PS` | read |
| LabOS Raw Data Table | `tblnc9SsbXU0C0FWh` | write; read for delivery reconciliation |

Only the schema/fixture setup workflow may mutate requirement records in the Testing Base. The runtime
client's write allowlist remains the raw-results table alone. Tokens are server-side, outside git and
browser-served configuration. Schema-write credentials belong to setup, not the runtime worker.
Capture field IDs separately per base; bind logical fields to those IDs after checking type/options.
Production replication and automation acceptance are release work, not prerequisites to local development.

## 1. Ownership

HubSpot supplies approved commercial scope. Airtable owns the assigned project/specimen/protocol hierarchy,
requirements and operational roll-ups. LabOS owns executable procedures, hardware, local attempts,
operator/reviewer decisions and original evidence. LabOS can run local unlinked work; it does not create
duplicate Airtable projects to represent it. No billing, contacts, invoices or scheduling data enters the
runtime mirror. Read only the field allowlist in the register.

LabOS writes its verdict to the raw-results row. Airtable automation projects that verdict into operational
views; LabOS never writes Protocol Section `Result`, `Status` or `Testing Date` directly. A parameter row
such as gauge count is not an executed test and receives no synthetic pass/fail. The integration does not
infer the meaning of existing historical `Passed` values or rewrite those rows.

## 2. Identity and programme runs

Keep `ProjectParent` for a local job and `Project` for a specimen. Public API terms are projects/specimens.
Picker endpoints return mirror resources before import, not necessarily already-materialized ORM rows.

Use two logical levels, implementable as `test_programmes` and `test_programme_runs`:

- A programme is one specimen × primary section × test type. `labos_test_id` is its persisted UUID.
  A local unlinked programme also gets a UUID but is excluded from outbound sync.
- Each execution is a run with its own persisted UUID `labos_attempt_id` and monotonic `attempt_number`.
  The run has a frozen procedure version, ordered stage definitions and verified requirement snapshot.
- One raw-results row represents one run, for all five types. Static/cyclic stage trials and manual
  observations/shots are children. Existing stage IDs and legacy report data are retained.
- A stage may have multiple trials during an unfinished run; retain them all and explicitly select the
  trial used for completion. Restarting an entire programme after termination is a new run. No automatic
  reuse of successful stages from an earlier terminated run in this initial version.
- A completed run means all required stages/observations were recorded and the operator finished it;
  it does not imply a passing verdict or verified sensor performance. Record `completion_source`.
  Missing completion telemetry is never inferred from disconnection, a timeout or a pressure setpoint.

Unique: `(base_id, external_project_id)` on imported jobs; `(base_id, external_specimen_id)` on imported
specimens; `(specimen_id, primary_section_id, test_type)` on linked programmes; UUIDs; and
`(programme_id, attempt_number)` on runs. Parent IDs, section references on stages and section IDs across
runs intentionally repeat. A run has its own primary key; the programme tuple is not unique on runs.

The external project ID echoed on results comes from the imported hierarchy, never a matching display name.
Conflicting parent links are rejected for import; the last consistent mirror remains usable offline.

## 3. Requirements and execution

### 3.1 Typed fields on Protocol Sections

Preserve `Section Name` and `Value` verbatim. Add these eight fields; their semantics are decided here.

| Field | Airtable type | Rule |
|---|---|---|
| Requirement Code | singleSelect | Stable code from §3.2; names are display labels |
| Requirement Kind | singleSelect | `Magnitude`, `Directional Pair`, `Count`, `Enum`, `Not Applicable` |
| Required Value | number | Finite scalar for Magnitude; non-negative integer for Count |
| Required Value Inward | number | Independent positive magnitude, PSF; required for pressure execution |
| Required Value Outward | number | Independent positive magnitude, PSF; never copied from inward |
| Required Unit | singleSelect | `PSF`, `in`, `s`, `cycles`, `impacts`; blank for unitless count, enum or N/A |
| Required Option | singleLineText | Explicit enum value; initial static programme supports `Full` |
| Applicability | singleSelect | `Required`, `Not Required`, `Unconfirmed` |

The last three additions beyond the previous five-field proposal resolve three gaps: a stable code avoids
routing by mutable names; Required Option makes Enum usable without parsing Value; Applicability distinguishes
missing requirements from an explicitly unneeded test. Blank Applicability is Unconfirmed, never Not Required.
Zero remains data, but a zero pressure does not qualify as a valid positive design-pressure pair.

### 3.2 Executable sections versus parameters

| Stable code | Existing label for migration review only | Kind / unit | Use |
|---|---|---|---|
| STATIC_PRESSURE | DP (+) (PSF) | Directional Pair / PSF | Primary section for Static Load |
| CYCLIC_PRESSURE | Cyclic (PSF) | Directional Pair / PSF | Primary section for Cycles |
| IMPACT_LMI | LMI (impacts) | Count / impacts | Primary section for Impact, LMI variant |
| IMPACT_SMI | SMI (impacts) | Count / impacts | Primary section for Impact, SMI variant |
| FORCED_ENTRY | Forced Entry (*) | Not Applicable / blank | Primary section for Forced Entry; applicability explicit |
| ANSI_IMPACT | Impact under ANSI Z97.1 | Not Applicable / blank | Primary section for ANSI Z97.1; applicability explicit |
| GAUGE_COUNT | # Dials | Count / blank | Programme parameter, no independent result |
| STATIC_PROGRAMME | Static / Type | Enum / blank | Programme parameter, no independent result |
| WATER_PRESSURE | Water (PSF) | Magnitude / PSF | Visible but unsupported in this integration release |

Not Applicable is a value shape (no numeric requirement), not a statement that the test is unneeded:
Applicability decides whether FORCED_ENTRY or ANSI_IMPACT is assigned. Their manual observations and verdict
are still required. Unknown code, unsupported kind/option, contradictory fields or Unconfirmed applicability
is visible and non-executable. New names do not silently introduce new procedures. No closed-world promise
is required from Airtable: add support explicitly when a new code is introduced.

Each programme consumes its own typed pressure section. Cycles does not require a duplicate populated
Static Load row if its own verified directional pair is present. Missing DP elsewhere may be a warning,
not proof of an extractor defect. Gauge/programme parameters are resolved within the specimen and snapshotted;
ambiguous duplicate parameter sources require explicit local resolution before a run starts.

Ranges, slash strings, signs and symbols in legacy Value are never execution inputs. Typed inward/outward
fields define direction by their field names; firmware sign/direction encoding remains LabOS's existing
procedure logic. No automatic parse or mass backfill of `+110/110` is authorized by this design decision.

### 3.3 Source verification

The known extraction defect remains unresolved evidence, not a design question. While it remains unresolved,
Airtable requirements are displayed but cannot directly drive a rig. The operator must record the actual
independently verified pair from the trusted proposal, its reference/revision, verifier and verification time.
An `operator` provenance tag alone is insufficient. Check this on the backend start path, not only in a UI.

Freeze source record IDs, hashes of relevant fields, pull time, entered values, units, verification facts,
operator identity, procedure version and stage targets at run creation. Local verified requirements remain
usable offline. Changes after start require a new run, not a mutated active snapshot. Fixture requirements
are explicitly synthetic and are never eligible for production execution.

## 4. Results, review and corrections

Execution states are In Progress → Completed or Aborted. Map Aborted to the existing wire spelling
`Abborted`; never alter an existing select option merely for spelling. Test Result is Pending until the
first review, then Passed, Failed or Inconclusive. Not Applicable is reserved for Airtable's operational
handling of unneeded work; no fake execution row is created for an unneeded section.

Each mutation and outbox entry commits atomically. Delivery has create, terminal and first-review phases,
plus separately tracked attachment delivery; these are phases, not a limit of four HTTP requests.
Initial review records declared reviewer identity, UTC time and rationale. Operator and reviewer are stored
separately even when the same person performs both; `identity_assurance = declared` is explicit.

Terminal measurements, stage evidence, identities and requirement snapshots are immutable. First review sets
the verdict once. A correction always creates a new attempt UUID with the same Test ID, next number,
`Corrects Attempt ID` and `Correction Reason`, without rewriting the original. A correction is not physical
retesting; carry `attempt_kind = correction` and original execution times, plus separate correction creation
time. Retests use `attempt_kind = execution` and have new physical execution times. Local correction chains
must be acyclic. Corrections wait in the queue until the target schema supports their linkage; never send
them as ordinary retests. Airtable roll-ups must exclude superseded results and must not count corrections
as extra physical tests. That behavior is verified before production cutover.

## 5. Measurements and time

For this release, omit unverified Deflection Value/Unit, all legacy transformed gauge readings, and
Max Pressure Achieved. Omit Measured Value for Static Load/Cycles because the current firmware has no
measurement source for it. Genuine manual measurements may be sent only with explicit quantity, unit and
operator provenance. Do not relabel targets, configured counts or elapsed wall time as achieved measurements.
Original unavailable/untrusted evidence remains in LabOS; corrections do not erase it.

Send machine-readable `data_quality` reasons in detailed JSON, without exporting the untrusted numbers.
The envelope rejects attempts to put quarantined measurements into scalar fields or JSON. Deflection
calibration and actual-pressure acquisition are follow-on hardware validation work, not reasons to invent data.
An operator cannot derive a supported passing certification solely from missing instrument data; the review
must reference independent supporting evidence or remain Pending/Inconclusive as appropriate.

Test Date means **execution completion**, omitted while running. Add `Testing Start Date` and
`Testing End Date` as dateTime fields; send start on create and end on termination. Both also appear in JSON.
Corrections retain the corrected physical execution times. All transmitted instants use UTC with Z.
Reports use America/New_York including the offset. Airtable automation derives Protocol Section Testing Date
from the completion instant in that timezone; LabOS never writes the section date.

Canonical outbound pressure unit is PSF; length uses in or mm with explicit unit, time s, counts cycles or
impacts where applicable. Keep existing text-typed Unit/Deflection Unit fields; validate tokens in LabOS.
Do not convert historical values or treat `Inches` as an outbound canonical token.

## 6. Wire envelope and artifacts

Upsert raw results only on `LabOS Attempt ID`, using the persisted run UUID on every phase and retry.
Runtime writes never enable `typecast` or create select options. Unknown fields, incompatible types/options
and missing required fields fail validation and remain queued for repair.

Omit unavailable or inapplicable fields; never substitute empty strings, zero or false for unknown data.
Runtime result writes do not clear cells with `null`. A genuine permitted zero is numeric `0`, and a
reviewer's explicit boolean is JSON `true`/`false`; neither is a missing value. Reject non-finite numbers.
Creation explicitly sends Test Result = Pending. Terminal and first-review payloads include only the
fields permitted for that phase, preserving earlier identities and frozen evidence.

`Schema Version = 0.4`; detailed JSON has `schema = 0.4`. It contains identity, attempt_kind, execution
start/end, requirements snapshot, procedure version, stage/observation detail, review and data_quality.
Use arrays of explicit objects with stable IDs for stages, shots and observations. Each numeric observation
declares quantity/unit/source; unavailable values are omitted. Do not change existing sample 1.0 rows.
Consumers must branch on schema version; compatibility with existing automations is a release test.

Always carry four Airtable IDs, Test ID, Attempt ID, attempt number, type, state, operator and created/updated
timestamps. Correction linkage is required on corrections. Send Test Name and Abort Reason in JSON; abort
reason is required on aborted executions. Rig identity and software/procedure versions also live in JSON.
Terminal result is Pending; first review updates verdict, Retest Required, reviewer fields and JSON together.
Retest Required is meaningful only once review exists, never inferred false from an unreviewed checkbox.
Testing Continued records explicit operator disposition, not an assumption from status.

Add raw-results fields `Corrects Attempt ID` (singleLineText), `LabOS Verdict By` (singleLineText),
`LabOS Verdict At` (dateTime), `Testing Start Date` (dateTime), `Testing End Date` (dateTime),
and `LabOS Photos` (multipleAttachments). Existing Correction Reason and Test Date remain.
The accompanying CSV describes field mapping; this prose governs on disagreement. Build a setup diff that
checks names, types/options and per-base IDs before mutation, and records actual before/after evidence.

LabOS retains original photos and generates a persisted JPEG preview under the direct-upload limit for
Airtable. Preview ID is persistent, with full content hash and deterministic filename. One sender owns an
artifact at a time. After an ambiguous upload, reconcile remote attachments and wait for any outstanding
request to settle before retrying; a single immediate absent read is not proof of failure. If still ambiguous,
park for reconciliation instead of blindly appending. Record returned attachment IDs and test lost responses.
Attachments may finish after terminal state without changing measured evidence; adding new substantive
evidence after review requires a correction. Matching originals/previews are immutable and linked locally.

Preserve Photos (url), but send at most one validated reachable link. Reports/Excel links are optional until
a reachable authenticated origin is validated; omit localhost/LAN/unconfigured URLs for remote consumers.
No public lab-network exposure is needed for preview upload. Validate report access separately before
advertising report links as delivered. Missing evidence delivery remains visible in sync status.

## 7. Sync architecture

One new sync-service container, existing PostgreSQL, no additional broker and no public service port.
report-api saves domain state and outbox entry in one transaction. The worker alone calls Airtable.
Queue payloads are immutable snapshots; sequence allocation is transactional per attempt. Process FIFO per
attempt with one owner, lease recovery and no later entry passing an unresolved predecessor. Manual retry
only makes an entry eligible for this same worker. Timestamps are audit data, not remote compare-and-swap.
An ambiguous predecessor is reconciled/retried before advancing; correction delivery also respects its
original-attempt dependency. Park failures with payload/error intact. Distinguish transient network/429/5xx
retry from schema/value errors needing repair and authentication failures needing credential restoration.

### 7.1 Concurrency mechanisms — required, not implied

The FIFO and single-owner properties above are guarantees, not hopes. Each needs a named mechanism, because
each fails silently without one and none of them is observable in a SQLite test.

**Sequence allocation.** `attempt_seq` must be allocated so two concurrent enqueues for one attempt cannot
compute the same value. A read-then-insert `max(seq)+1` is not sufficient: the unique constraint rejects the
loser, and because enqueue shares the caller's transaction that rejection **fails the operator's save** —
inverting the guarantee the outbox exists to provide. Use a per-attempt database sequence, or
`INSERT … ON CONFLICT` with a bounded retry. Never let allocation surface as a domain-write error.

**Exclusive claim.** Claiming must lock the rows it leases — `SELECT … FOR UPDATE SKIP LOCKED` on
PostgreSQL. Read-then-write leasing lets two workers hold the same entry. One owner is a property to enforce,
not a deployment convention to rely on.

**Lease at send time, not batch time.** A batch claim that stamps every lease with one timestamp starts the
clock on the last entry before the first has been sent; ten entries at twenty seconds each expire a
two-minute lease while still queued behind their own batch. Re-assert the lease immediately before each send
and skip the entry if it has been lost.

**Fencing token.** Every claim increments a monotonic `owner_epoch` on the row. Before recording an outcome,
verify the epoch still matches; if it does not, **discard the result rather than record it.** This is the
only mechanism that stops a late lander — a process paused by GC or a CPU limit can always complete after
its lease expired, and upserting on `LabOS Attempt ID` prevents a duplicate *row* while doing nothing about
which write lands last. Without fencing, a stale `terminal` can overwrite a reviewed verdict silently.

**Client deadline.** The Airtable client's total retry wall-clock must be bounded well below the lease, so an
expired-lease send is structurally improbable rather than merely unlikely. Lease duration and retry budget
are one decision, not two independent constants.

**Local pre-send checks are not ordering control.** `is_superseded` is evaluated before a request is issued
and sees nothing already in flight; timestamps on the wire are audit data, never remote compare-and-swap.

Full paginated reads of four tables every 60 s, configurable and coalesced with Refresh now. Hash canonical
allowlisted field content, excluding acquisition timestamps. Stage a complete successful read cycle, validate
links and atomically publish its changes; never hold a DB transaction open while waiting on Airtable.
Mark absent IDs unavailable only after successful complete enumeration, not after errors or partial pages.
Preserve local history; treat changed links separately from deletion. Cross-table reads are not a remote
transaction: inconsistent relationships keep the prior valid cache and are retried. Newly imported work must
have complete relationships. Unknown/unlinked records do not invalidate already-frozen runs.

At the observed size four pages per minute means about 5,760 requests/day, excluding writes, schema reads
and retries. Check the account's monthly allowance before enabling continuous polling; interval is a config
value, not a correctness dependency. Share a conservative per-base request budget across reads and writes;
give results priority without starving cache refresh. No delta cursor or extra timestamp field is needed now.

report-api serves /sync/status from persisted worker heartbeat, successful pull/push times, queue counts and
mirror revision, even if the worker is down. Include attachment backlog and parked entries. Use Synced,
Pending, Sync Failed, Retry Required; errors/stale heartbeat override Pending. These four are the
contractual values. A colour hint may be returned **alongside** them as a presentation convenience, never
instead of them. Queue and attachment counts are computed at read time; a count cached by the worker is
exactly the number that is wrong when the worker is down. Spinner only while a request
is outstanding; timeout shows LabOS unreachable. UI polling never calls Airtable.

## 8. Implementation sequence

1. Generate the Testing Base schema diff and reviewed synthetic linked fixtures from the register. Apply
   authorized additions there, capture post-change schema/IDs, and maintain the change register throughout.
2. **Stand up the disposable PostgreSQL harness first** — isolated instance, synthetic data, and the
   ability to run **two independent worker processes on separate connections**. Two sessions inside one
   process share too much and will pass while §7.1's defects stand. Then rehearse local migrations: programme/run identity, stage linkage, outbox, mirror,
   first review, corrections and artifacts. Existing P1 migrations are dependencies in the upgrade chain,
   not a demand for a separate production deployment before development can start.
3. Wire one complete local flow: import → start → save/finish → restart worker → one testing-base row.
4. Add all manual forms' backend APIs, review/corrections, preview uploads and status. UI remains deferred.
5. Validate PostgreSQL concurrency against §7.1 with four named cases — **concurrent enqueue, competing
   workers, slow send, stale owner** — plus offline replay, missing measurements, full-read failure, schema
   drift and Airtable automation behaviour. SQLite tests are useful groundwork, never proof of locking.
6. Produce the actual-change document with rationale, examples, validation, migration/rollback notes and
   known delivery limits. A design notice is not evidence that a field or feature has shipped.
7. Production requires owner coordination, schema/automation replication, validated migration rehearsal and
   a maintenance window. Read the live alembic head immediately before deployment. No live experiments,
   hot patches or container recreation merely to test this design. Bench hardware is needed for metrology;
   local sync and migration rehearsal do not wait for the offline test node.

Design documentation is the work authorized in this closure session. Subsequent schema/application work is
an implementation task, not something silently performed while closing the design.

## 9. Decision closure

No unanswered design questions remain for the initial scope. A1 programme-level runs; A2 omit unavailable
rig pressure but allow sourced manual measurements; A3 retain uncalibrated evidence locally; A4 immutable
corrections; A5 verified execution values; A6 explicit supported codes/shapes; A7 stable DB names and clear
API vocabulary; A8 water integration deferred — all decided under the user's instruction to close the design.

Schema permission does not establish the truth of legacy data or prove external automations correct.
The former G2 sign question is removed by defining typed magnitudes without legacy parsing. G5 field
creation is authorized delivery work. G1/G3/G4 retain the release behavior specified above until evidence
supports widening it. This is scope closure, not a claim those defects have been fixed.

## 10. Canonical delivery checks and legacy item disposition

No further field-design permission is needed for the Testing Base. These checks remain unperformed until
their evidence is recorded; they are work items with decided behavior, not open design alternatives.
References such as §10.19 in earlier documents mean legacy item 19 in the table below, not a new subsection.
The full pre-closure wording is retained in `../evidence/write-contract-v0.3-superseded-2026-09-06.md`.

| Legacy item(s) | Disposition at 2026-09-06 |
|---|---|
| 0, 13 | Decided: completion Test Date; explicit start/end; verify fields after setup |
| 1, 12 | Decided: original evidence local, Airtable previews; links omitted until reachable; test delivery |
| 2, 4, 5, 10 | Previously verified base/link/field/access decisions retained; re-probe before mutations |
| 3, 6, 7, 9, 15, 23, 24 | Decided in §§1–6; add typed fields, no parsing, no scheduling dependency; verify setup |
| 8, 14 | Decided: ordered multi-phase run delivery and immutable correction rows; create linkage and test roll-ups |
| 11 | Pending Testing Base verification of actual types, blanks, schema mismatch and retry behavior |
| 16, 18 | Existing Passed/Failed and Abborted wire spellings retained; no runtime typecasting |
| 17, 20 | CLOSED by September 5 baseline: all five test types and datetime Test Date delivered in both bases |
| 19 | Extractor defect unresolved; independently verified local requirements remain mandatory for rig execution |
| 21, 22, 25, 26 | Decided: raw table only, UUIDs, version 0.4 JSON, explicit review/disposition; validate automation compatibility |
| 27 | Deflection calibration unresolved; quarantined measurements omitted from all outbound payloads. **Tracked as milestone M6** |
| G4 | Actual pressure acquisition unimplemented; omitted for rig runs. **Tracked as milestone M7**, not left unscheduled |
| Release | Local PostgreSQL tests, testing-base acceptance, report reachability if offered, API allowance, migration and production window |

Runtime code, schema fixtures and Notion are views of this document. Existing code still targets prior
contracts until implementation updates it. All setup changes must be documented as planned/applied/verified
separately; never mark live delivery complete because the design decision is closed.
