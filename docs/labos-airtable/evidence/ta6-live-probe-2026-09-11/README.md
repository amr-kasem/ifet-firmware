# TA6 live probe — the per-standard result pair, on the real wire, 2026-09-11

**Result: 101/101 assertions passed, in one clean run — `20260911T010333Z`.**
Read `probe-results-20260911T010333Z.json`; it is the authoritative artifact.

**Re-run after DG14.** The first authoritative run was 97/97 at
`20260911T001123Z`. The requirement release gate landed the same day and adds
four assertions to this probe, so it was re-run rather than left claiming a
count from before a gate that sits directly on the static and cyclic path it
exercises. Nothing about TA6 changed; the TA7 probe was re-run too and is
unchanged at 64/64.

Run by `ifet-management` `src/management_service/tests/ta6_probe_live.py` against the **Testing** Base
`app4oXS3Kd5IKWgJ7`. Production `app0OCunbmuXl7Hc9` was read for comparison and never written.

## Why this exists at all

Every local suite injects a transport that accepts any payload. That is right for testing the queue, and it
is exactly how a sender that would have rejected *every photograph* once passed 270 tests. This probe uses
the real chain and no substitutes:

```
Airtable records -> mirror.refresh -> importer -> HTTP routes
  -> sync.publish -> sync_outbox -> worker.drain
  -> service.make_sender(AirtableClient) -> Airtable
```

It is the **same harness** as the TA7 probe, not a second one: `Report`, the disposable-database guard,
the stack builder, the hierarchy snapshot and the safety rules are imported from `ta7_probe_live`.

## What it proves

**The matrix, on the wire, for all five test types.**

| Type | phase | `Test Result` | `Forced Entry Result` | `ANSI Result` |
|---|---|---|---|---|
| Forced Entry | terminal | `Pending` | `Pending` | **absent** |
| Forced Entry | verdict | `Passed` / `Inconclusive` | the same value | **absent** |
| ANSI Z97.1 | terminal | `Pending` | **absent** | `Pending` |
| ANSI Z97.1 | verdict | `Failed` | **absent** | the same value |
| Static Load | terminal | `Pending` | **absent** | **absent** |
| Cycles | terminal | `Pending` | **absent** | **absent** |
| Impact | verdict | `Passed` | **absent** | **absent** |

*Absent* is asserted as `name not in fields` — the key is missing, not blank. All four option values reach
the base: `Pending` at terminal, then `Passed`, `Failed` and `Inconclusive` at verdict, in the **wire**
spelling that `option_wire` produces from LabOS's `Pass`/`Fail`.

**And the JSON-valve transition, which is the reason a live probe was required.** While the columns did
not exist the envelope carried the value through `Complete LabOS JSON Response` as
`labos_extra.forced_entry_result`. Both states are asserted from one set of mapped values:

- `PRESENT` → the value is a **column** (`Passed`) and `labos_extra` does not contain it;
- `ABSENT` → the column is not sent and `labos_extra.forced_entry_result` holds `Passed` — the **wire**
  spelling, so nothing was lost in the interim;
- and the contract is back to `PRESENT` when the check finishes.

The live rows confirm the first half independently: every `Complete LabOS JSON Response` in this run has
`labos_extra` limited to `duration_s`, `test_name`, `testing_start_date`, `testing_end_date`.

**And DG14, on the real wire** — the requirement release gate, because this
probe drives static and cyclic stages on an Airtable-imported job and is
therefore the only place it can be exercised end to end:

- an unverified imported requirement **cannot start a rig** — `409` from
  `PUT /projects/{id}/static_tests/0/start`;
- a verification of `9.0/9.0` against a mirrored `60.0/45.0` is **refused**,
  which is the production defect in miniature — *"the pair you verified,
  [9.0, 9.0] PSF, does not match what LabOS mirrored from Airtable,
  [60.0, 45.0] PSF. Nothing has been recorded."*;
- the agreeing pair releases the job, and only then does the stage run;
- and the verification is **frozen onto the attempt** — `verified_by`,
  `reference`, both values and the time, inside `requirement_snapshot`.

**Everything the pair had to not break:** one Raw Data row per attempt · the correct `Test Type` ·
photographs through the real attachment path · valid `Complete LabOS JSON Response` · a re-queued current
phase upserting onto the **same record id** with no `createdRecords` · a phase behind the delivered
watermark reported superseded · 25 probe rows and 25 distinct attempt ids, so no duplicate logical
attempt · no write to any of the four hierarchy tables · production schema byte-identical and its record
count unchanged before and after.

## Identifiers — the authoritative run `20260911T010333Z`

| | |
|---|---|
| Job | `IFET-PROBE-TA6-0001-010333` · project `recQ2ZTonl6qaU3fI` |
| Raw Data rows | FE pass `reciMH1VqUVC9074b` · FE inconclusive `recIo74BY0V9S1pUQ` · ANSI fail `recEBb8oGaOX75ea6` · Static `recwA4mfTErtWCbdS` · Cycles `recIZvqVzDU3BlW3Q` · Impact `recjlMRSRRnV6UGgW` |
| Full identifier set | `probe-results-20260911T010333Z.json` — hierarchy, section ids, attempt ids and LabOS test ids for the run |

## Probe history — four earlier runs, and what each one caught

Four runs preceded this one. **Every failure was in the probe, not the product**, and each one is worth
recording because in each case the system refused something it should have refused:

| Run | Failure | What it actually was |
|---|---|---|
| 1 | no manual tests created | The probe seeded `FORCED_ENTRY` and `ANSI_IMPACT` as `Requirement Kind = Enum`. `requirements.KIND_BY_CODE` pins both to `Not Applicable`, and both sections were **correctly refused** |
| 2 | `[Impact] finish accepted` — 400 | *"A completed impact attempt requires at least one photograph. Evidence cannot be added after review."* The probe posted a shot with no photograph; TA7a's completion gate did its job |
| 3 | `[Cycles] reached the base` — 0 rows | `CYCLIC_PRESSURE` seeded as `Count`/`cycles` instead of `Directional Pair`/`PSF`. The section was refused, so the eight derived cyclic stages were never bound, and each landed in `GET /sync/failures` as a non-recoverable *"no Airtable linkage"* rather than publishing against the wrong requirement |
| 4 | `[Cycles] reached the base` — 0 rows, again | Different cause: `Cycles Completed` was `None`, so the terminal payload was refused under §5.1. The count is snapshotted from `cyclic_tests.current_cycle`, which the rig reports through `update_status`, and §6 forbids substituting zero for unknown. The probe now reports progress first |

Two probe assertions were also wrong and were corrected rather than worked around:

- the valve was expected to preserve `Pass`; it preserves `Passed`, because the envelope translates
  through `option_wire` **before** deciding where the value goes. That is better, and the assertion now
  says so;
- re-recording an already-delivered `terminal` was expected to be silently declined. It is declined, but
  it also **records a visible refusal** and marks the attempt `Sync Failed` — correct behaviour that
  nothing in the routes triggers, and not something worth manufacturing to observe. The probe now reads
  the watermark instead of provoking a false alarm in `GET /sync/failures`.

Run 4 also showed why the per-type assertions must be scoped to **this run's project record** rather than
the operator tag: earlier runs' rows carry the same tag, so a tag-wide query would let a run pass on a
previous run's evidence. It does not any more.

## Synthetic records

**37 rows remain in the Testing Base**, tagged `Operator Name = LABOS-PROBE-TA6`, with their hierarchy.
They are listed in `probe-records-inventory.txt`. **Retained deliberately, not deleted**: the probe only
ever creates, LabOS has no delete path, and removing records from a base shared with the Airtable team is
a separate operation that needs its own approval and its own record. See the delivery plan's cleanup item.

## Files

`probe-results-*.json` — every assertion, its result and its detail, plus the record ids.
`imported-project-*.json` — what the importer built from the seeded hierarchy.
`testing-schema-*.json` — the Testing Base Meta schema at probe time, 164 fields.
`production-before-*.json` · `production-after-*.json` — the production Meta schema either side of the
run, compared byte-for-byte by the probe itself.
`probe-records-inventory.txt` — every synthetic record left behind, across all runs.
