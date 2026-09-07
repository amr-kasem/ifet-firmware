# Schema validation against all five test types — 2026-09-07

**What this is:** the evidence for delivery plan **§6.0 step 1**, the gate on §6.0 step 2 (sending the change
document to the Airtable team). A10 put that gate there deliberately: *"we do not ask them to change
production on the strength of an unvalidated design."*

**Result: step 1 initially FAILED on all five test types, for three independent reasons. All three are now
fixed, and the suite is green.** The gate held — this is exactly the class of error that would otherwise have
been discovered by the Airtable team, in their production base, after we had asked them to apply it.

Scope: the **write** surface, phase by phase, for Static Load, Cycles, Impact, Forced Entry and ANSI Z97.1.
The read surface is unchanged and needed no correction: under A9 it is 10 fields plus the four `rec…` record
IDs, and `Requirement Code` alone carries meaning.

---

## 0. Grounding

Read-only, both bases, using the two PATs in `ifet-management/.env`.

| | |
|---|---|
| Probe | `python3 -m app.airtable.probe` — 0 failures, 1 warning (a stale literal in the probe's own comparison text, not a schema fault) |
| Testing base `app4oXS3Kd5IKWgJ7` | 8 tables. `LabOS Raw Data Table` holds **36** fields — the 35 the contract expects, plus their `Raw Modified Time` |
| `Protocol Sections` | 24 fields — 16 baseline plus the 8 applied on 2026-09-06 |
| Live select sets | `Test Type` = all five · `Test Status` = `Not Started / In Progress / Completed / Abborted` · `Test Result` = `Pending / Passed / Failed / Not Applicable / Inconclusive` |
| Type answers | `Photos` is `url`; all four `Airtable … ID` fields are `singleLineText`; `Impact Result` is free text |

The shared base link and the token-derived baseline agree exactly, so the field inventory is complete rather
than merely plausible. The token remains the grounding: it returns field IDs, which a shared view cannot.

---

## 1. The three defects

Every one was invisible to the existing 172-test suite, and for the same structural reason: **the suite
exercised Static Load and the create phase.** The other four types and the later phases were covered by
prose, not by assertions. A green suite is not coverage of a matrix nobody enumerated.

### V1 · The create payload the contract mandates was refused by our own validator

Contract §6: *"Creation explicitly sends Test Result = Pending."* The register agrees —
`Test Result` carries `write_phase = create+terminal+verdict`.

`envelope.py` raised `'Test Result' must be omitted while In Progress (contract §4.3)`, and `Pending` was not
in `contract.py`'s option list either, so the field failed twice over. **All five types.**

§4.3's actual concern is a *verdict* arriving before a review has happened. `Pending` is the absence of a
verdict, not one — the guard was too wide by exactly one value.

**Fixed.** `Pending` is a legal option (`C.RESULT_PENDING`), defaulted at create, and the three verdict values
are still refused on an In Progress write. Defaulted rather than merely permitted: a blank cell and a
`Pending` cell read differently to a PM and to their automations — blank says nobody filled it in.

### V2 · `Test Date` carried the wrong instant, and two applied columns were never written

The worst of the three, because it published a plausible wrong number rather than nothing.

`Testing Start Date` and `Testing End Date` were **applied to the Testing Base on 2026-09-06** as part of M1's
fourteen fields, and marked `PRESENT` in `contract.py`. `envelope.py` was not updated with them: it still ran
§10.13's collapse, written when their table had no start/end pair. So it skipped both real columns and
stamped `Test Date` with the **start** instant.

Contract §5 is unambiguous — *"Test Date means execution completion, omitted while running"* — and their
automation derives the Protocol Section `Testing Date` from it. The published date would have been wrong by
the duration of the test, with nothing on the row to reveal it. **All five types.**

This is the same failure class as the extractor shift the whole design guards against: not a missing value,
an individually plausible wrong one. Worth noting that it was on **our** side.

**Fixed.** Both columns are written; `Test Date` is the completion instant and is omitted while running;
`duration_s` is still computed into the JSON valve.

### V3 · An attachment upload was a precondition for publishing a measured result

`REQUIRED_BY_TEST_TYPE` required `LabOS Photos` inside the **terminal** payload for Impact, Forced Entry and
ANSI Z97.1. `outbox.py` says the opposite in its own docstring: attachments are their own delivery channel
(`ATTACHMENT`), and *"an attempt can be fully delivered while its photographs are still queued."*

So the contract module asserted the inverse of the queue it feeds. An Impact attempt could not reach
`Completed` in Airtable until a file transfer unrelated to the measurement had succeeded — and §6 explicitly
allows an ambiguous upload to be **parked for reconciliation**, which would have parked the result with it.

**Decided with IFET, 2026-09-07:** Impact requires photographic evidence; Forced Entry and ANSI Z97.1 are
recorded as a pass/fail outcome and require none.

**Fixed.** The requirement was real, its placement was wrong. `REQUIRED_EVIDENCE_BY_TEST_TYPE` now holds
Impact's photo requirement and is enforced on the **run-finish** path — where the operator is — while the
terminal payload no longer demands it. An undelivered upload stays visible as attachment backlog in
`/sync/status` rather than blocking the result. Forced Entry and ANSI carry no photo requirement at all.

---

## 2. What the validation now proves

`tests/test_five_test_types.py` — 20 cases, and it is a schema-coverage suite, not a behaviour suite. For
each of the five types it asserts create, terminal, verdict and aborted all build; that `Pending` is
defaulted at create and a verdict is refused there; that `Test Date` is completion and omitted while running;
that no type requires an attachment in its terminal payload; that the three A2/A3 fields are refused in the
JSON as well as in the columns; and that the nine JSON-only fields are absent by decision.

| | Before | After |
|---|---|---|
| SQLite | 140 | 160 (2 skipped) |
| **PostgreSQL 13, disposable harness** | 172 | **192 + 63 subtests** |

The harness is the one the plan requires — `postgres:13`, the version production runs, on 127.0.0.1:15432,
tmpfs, torn down with `down -v`. SQLite results are not accepted as proof of any §7.1 guarantee.

---

## 3. Two things this did not find, and one it corrected

**The read surface needed nothing.** A9 reduced it to identity plus `Requirement Code`, and the eight typed
`Protocol Sections` fields are live and correctly typed. Ten read fields are enough to identify the work for
all five types, because LabOS does not execute from any of them.

**A completed Static Load or Cycles row still carries no number describing what physically happened.** A2
omits `Measured Value` and `Max Pressure Achieved`, A3 quarantines the deflection pair, and the rig sends
only `deflections[]` plus `recovery` — which is the 60 s config constant, not a measurement. That is the
decided initial behaviour (M6/M7), not a defect this validation found. It remains the first thing the
Airtable team will ask about, and the change document should say so plainly rather than let them notice.

**Corrected while here:** the four existing tests that asserted V1's and V2's behaviour. They were green, and
they were encoding the defects — `test_start_instant_goes_into_their_test_date` said in its own name what was
wrong. Rewritten to assert the contract.

---

## 4. Register and prose drift, found alongside

Not defects in the interface, but they make the register and the plan disagree about what was decided.

| | |
|---|---|
| Register status | **73 rows, all `DECIDED`; 10 `OMITTED`.** A9 closed DG7/DG8's seven `OPEN`/`PROPOSED` rows into it — correctly. Plan §9 and `INDEX.md` still describe "66 DECIDED … 3 OMITTED … plus 7 OPEN/PROPOSED" |
| JSON-only fields | DG6 notes two (`Test Name`, `Abort Reason`). There are **nine**: those plus `Required Value`, `Required Unit`, `Cycles Required`, `Cycles Completed`, `Test Rig`, `LabOS Version`, `Result Rationale`. A register-vs-base diff reports all nine as missing |
| Trials routes | §6.0 step 6 says "key `/trials` on `event_id`", singular. There are **two** — `POST /projects/{id}/static_tests/{idx}/trials` and `POST /projects/{id}/cyclic-tests/{idx}/trials` — and firmware posts to both (`api.py:94`, `api.py:109`). Likewise two GETs to mint `run` on |

---

## 5. Step 1 is passed. Step 2 is unblocked.

The change document in `testing-base-changes-2026-09-06/` describes the fourteen applied fields, and nothing
found here changes which fields exist or what they are called — all three defects were in how LabOS fills
them. **The document is still accurate and can now be sent.**

One sentence should be added to the cover letter before it goes: `Test Date` is written as the **completion**
instant, and `Testing Start Date` / `Testing End Date` carry the pair, because their automation derives the
Protocol Section date from `Test Date` and that dependency should be stated rather than inferred.

Commands and outputs: `schema-validation-five-types-2026-09-07.txt`.
