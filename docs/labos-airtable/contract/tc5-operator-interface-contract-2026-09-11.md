# TC5 — operator interface implementation contract, 2026-09-11

**For the UI developer.** Everything below is live and proven on the real wire today; none of it is
planned. The backend is complete and this document does not propose changing it.

**Why this exists.** Three of the five test types — Impact, Forced Entry, ANSI Z97.1 — have a complete,
probed API and **no consumer**. The deployed bundle in `src/ifet_ui_react/static/` contains no reference to
`manual-tests`, `impact-tests`, `ANSI Z97`, `Forced Entry` or `sync/status`, and the UI source is not in
this repository. So an operator cannot run three of five workflows, and the release is blocked on that
alone. Delivery plan **TC5 / DG5**.

Authoritative companions, and where they beat this document if they disagree:

| | |
|---|---|
| Route and payload shapes | `ifet-management/src/management_service/openapi.json` — **generated, and gated**: `TheCommittedApiContractIsCurrent` fails the suite if it drifts from the app |
| Prose and the reasoning | `ifet-management/MANUAL_TESTS_API.md` |
| Executable behaviour | `tests/test_manual_tests.py` (91 tests) · `tests/test_requirement_release.py` (24) |
| Field meanings | `contract/write-contract-v0.4.md` · `contract/field-register.csv` |

---

## 0. The five screens, and no more

This is the **minimum**, not a wish list. Anything not on it is out of scope for closing TC5.

| # | Screen | Exists today? |
|---|---|---|
| 1 | **Job picker** — choose an Airtable job, see what LabOS will and will not run, import it | no |
| 2 | **Requirement release** — confirm the design-pressure pair against the proposal | no, and **nothing runs without it** |
| 3 | **Manual test** — Forced Entry and ANSI Z97.1, one screen with a type switch | no |
| 4 | **Impact test** — classification, target velocity, one attempt per impact | no |
| 5 | **Sync status** — did it reach Airtable, and what do I do if not | no |

Screens 3 and 4 share one **attempt** component: start → evidence → finish/abort → verdict is the same
lifecycle for all three types, on the same `/test-results/{id}` routes. Build it once.

---

## 1. Screen 1 — picking the work

**Every read here hits a local mirror, never Airtable.** A picker at a rig cannot depend on someone else's
API being up, so an empty mirror gives an empty list rather than a spinner.

```
GET  /airtable/projects                          -> jobs, each with `mirrored_at`
GET  /airtable/projects/{rec}/specimens          -> each with `imported_project_id`
GET  /airtable/specimens/{rec}/protocols
GET  /airtable/protocols/{rec}/sections          -> `executable`, `applicability`, `refused`
POST /airtable/refresh                           -> the ONLY route that calls Airtable
POST /airtable/import/plan                       -> what an import would do, without doing it
POST /airtable/import                            -> {device_id, project_record_id,
                                                     specimen_record_id, protocol_record_id, name?}
```

Three behaviours to build around:

- **Show `refused`.** It is the one thing the operator can act on — it says why LabOS will not run a
  section, in a sentence. A section list that hides refusals looks like a shorter protocol.
- **`mirrored_at` is a fact worth showing.** A stale mirror is not an error state, but the operator should
  know how old it is before deciding it is complete.
- **`imported_project_id` means "already imported".** Say so, rather than letting someone import twice and
  wonder why nothing changed. `POST /airtable/import` is idempotent on the mock-up and returns the
  existing project.

**`device_id` is the operator's decision.** Which physical rig runs the job is not something Airtable has an
opinion on.

---

## 2. Screen 2 — the requirement release ⚠️ **nothing runs without this**

**DG14 / contract §3.3.** LabOS derives all fourteen static and cyclic stages from the imported
design-pressure pair, and the upstream extractor is known to shift values one column to the left — a 60 PSF
requirement arrives as **9**, plausibly, in the right column, with the right unit. Nothing can detect that
by looking at it, so the control is that **two independent readings have to agree**.

```
GET  /projects/{id}/requirement-release?kind=static&static_test_index=0
POST /projects/{id}/requirement-verification
```

`GET` returns `RequirementReleaseSchema` — **the same function the start path enforces**, so a green light
here is never one the backend will refuse:

```json
{"executable": false,
 "code": "unverified",
 "reason": "this requirement came from Airtable and has not been independently verified …",
 "airtable_section_id": "rec…",
 "imported_pair_psf": [60.0, 45.0],
 "verified_pair_psf": null}
```

`code` is a stable token to branch on. `reason` is the sentence to show:

| `code` | Screen behaviour |
|---|---|
| `local` | executable. A LabOS-only job — the operator typed these pressures, there is nothing to verify. **Do not show this screen** |
| `released` | executable. Show who verified it and against which document |
| `unverified` | **the normal first state of an imported job.** Show the verification form |
| `verification_disagrees` | show both pairs and escalate. Do **not** offer "use the Airtable value" |
| `project_drifted_from_mirror` | the section changed upstream after import. Offer re-import |
| `invalid_requirement` | the section no longer validates. Show `reason` verbatim |
| `section_missing` | the section is gone from the mirror. Offer refresh, then re-import |
| `not_a_pair` | this test is bound to a section with no design-pressure pair |

`POST` body — **every field required, none defaulted**:

```json
{"inward_psf": 60.0, "outward_psf": 45.0, "unit": "PSF",
 "reference": "Proposal P-2291 rev C", "verified_by": "technician-1"}
```

- `200` → the job is released; the response is the same `RequirementReleaseSchema`, now `executable: true`.
- `409` → refused, with the reason in `detail`. **Nothing was stored.** The important case is a
  disagreement: *"the pair you verified, [60.0, 45.0] PSF, does not match what LabOS mirrored from Airtable,
  [9.0, 9.0] PSF. Nothing has been recorded."*
- `400` → this job has no Airtable-bound rig test, so there is nothing to verify.

**Design notes that are not negotiable, because they are the control:**

1. **The operator types the pair from the proposal. Never pre-fill it from `imported_pair_psf`.** A
   pre-filled field that the operator confirms is one reading, not two, and the whole control collapses.
   Show the imported pair only *after* a mismatch, when explaining the refusal.
2. **`reference` is which document, at which revision** — "Proposal P-2291 rev C", not "the proposal". §3.3:
   an operator provenance tag alone is insufficient. Blank or whitespace is a `409`.
3. **Do not offer a "use Airtable's value" button on a disagreement.** LabOS refuses to choose between two
   contradicting sources by design. The operator re-reads the proposal, or the section is fixed upstream.
4. It is **immutable once a rig attempt exists** (`409`). Before that it may be re-recorded, so a typo
   caught immediately does not need a new job.

---

## 3. Screen 3 — Forced Entry and ANSI Z97.1

One screen. The only differences are the `type` value and the word for `required_option`.

```
POST /projects/{pid}/manual-tests/            {type, required_option?, airtable_*?}
GET  /projects/{pid}/manual-tests/            ?type= optional
POST /projects/{pid}/manual-tests/{id}/trials {operator_name}      -> starts an attempt
PUT  /projects/{pid}/manual-tests/{id}/finish                      -> finishes the TEST
```

`type` is `"Forced Entry"` or `"ANSI Z97.1"`; anything else is `422`. `required_option` is the grade or
class — `"ASTM F588 Grade 40"`, `"Class A"` — **pre-filled from the section's `Required Option`** when the
job came from Airtable, typed by the operator when it did not.

Then the shared attempt lifecycle in §5.

**What the screen must show that is not obvious:**

- **The grade or class is the requirement.** There is no numeric target. A grade LabOS does not recognise is
  displayed and the test stays non-executable rather than being guessed at.
- **ANSI Z97.1 is recommended first on a specimen and is not enforced.** Approved by the product owner on
  2026-09-10. Show it as guidance; do not block.
- **The result now lands in two columns.** `Test Result` as always, **and** `Forced Entry Result` or
  `ANSI Result` — the same value, on its own axis, so a report about one standard does not have to filter by
  test type first. The UI sends one verdict; the backend projects it.

---

## 4. Screen 4 — Impact

```
POST  /projects/{pid}/impact-tests/           {} is valid — everything optional
PATCH /projects/{pid}/impact-tests/{id}       {impact_level?, target_velocity?, impact_family?}
POST  /projects/{pid}/impact-tests/{id}/trials {operator_name}   -> starts ONE impact
POST  /test-results/{aid}/shots               {result, area?, velocity?, note?}
POST  /shots/{sid}/photos                     multipart, once per photograph
PUT   /projects/{pid}/impact-tests/{id}/finish
```

**One physical impact is one attempt is one Airtable row.** A five-impact test is five attempts, each with
its own verdict and photographs. `Impact Number` distinguishes them.

**The classification control, and this shape matters:**

| Section's `Requirement Code` | What the screen offers |
|---|---|
| `IMPACT_SMI` | **no family control.** Show "SMI", read-only |
| `IMPACT_LMI` | a **required** D / E choice, and nothing else |
| LabOS-only test | a family choice, write-once, fixed as soon as any attempt exists — aborted included |

**Never a three-option picker on a bound test.** The SMI/LMI half is Airtable's answer, frozen at import;
offering it invites a contradiction the API rejects anyway (`400`).

`impact_classification` comes back on the test and on the project as a **read-only derived value** — `SMI`,
`LMI Level D`, `LMI Level E`. Render it; never compute it, never send it.

`target_velocity` is **operator-entered, ft/s, per test**. `shots.velocity` is the achieved velocity of one
impact. Different fields, different meanings — **they must not share a control.**

Two `400`s on finish, for an Impact attempt with no `abort_reason`: the test needs a resolvable
classification, and a `target_velocity`. An abort needs neither. And **a completed impact attempt requires at
least one photograph** — evidence cannot be added after review.

---

## 5. The shared attempt lifecycle — build once, use three times

```
PUT  /test-results/{id}/finish    {result, note?, testing_continued?}  OR  {abort_reason}
PUT  /test-results/{id}/verdict   {test_result, verdict_by, retest_required, rationale?}
POST /test-results/{id}/photos    multipart: file, note?
POST /test-results/{id}/correct   {reason}          -> a NEW attempt superseding this one
```

| State | What the screen offers |
|---|---|
| `In Progress` | record evidence · Finish · Abort |
| `Completed` / `Aborted`, no verdict | Review · Correct |
| reviewed | Retest (a new attempt) · Correct. **Nothing is editable** |

- `test_result` is `Pass` · `Fail` · `Inconclusive`. `retest_required` is **required and not defaulted** —
  an unchecked box is not a decision.
- **Start is idempotent.** `POST …/trials` on a test with an open attempt returns *that* attempt. A
  double-click cannot become two certification records. A "Retest" button must finish or abort first.
- **One active run per rig.** Starting a test on a busy rig returns `409` naming the blocking attempt.
  Surface the message.
- **Correction is not retest.** A retest is another go; a correction says the earlier record is wrong. Never
  offer "Correct" as a synonym for "try again" — it writes `Corrects Attempt ID` onto a row that supersedes
  nothing, and no route takes it back. Its three `400`s are in `MANUAL_TESTS_API.md`.

---

## 6. Screen 5 — sync status

```
GET  /sync/status                    -> Synced | Pending | Sync Failed | Retry Required
GET  /sync/queue                     -> one row per pending write, with `channel`
POST /sync/queue/{id}/retry
GET  /sync/failures                  -> payloads LabOS REFUSED to queue
POST /sync/failures/{id}/repair      -> 409 while still refused, with the current reason
```

- **`/sync/failures` needs its own surface.** These are results saved correctly that could not be described
  to Airtable. They never got a queue entry, so they are invisible in `/sync/queue` by construction — before
  this route existed the headline read `Synced` for an attempt that had never been published.
- **Show `attachment_backlog` separately.** A photograph stuck in delivery cannot hold up a verdict and must
  not drag the headline to `Retry Required`.
- `worker_alive` / `worker_heartbeat_at` is the worker's only liveness surface, deliberately.

---

## 7. Acceptance — TC5 closes when all of this passes with a real operator

Against a real deployment, by a person who is not the developer:

| # | | Must |
|---|---|---|
| 1 | Import an Airtable job | refused sections visible with their reasons; re-import returns the same project |
| 2 | **Try to start a static stage before verifying** | **refused**, with the §3.3 reason shown |
| 3 | Verify the pair correctly | job becomes executable; static and cyclic run |
| 4 | **Verify with a deliberately wrong pair** | **refused**, both pairs shown, nothing stored, job still not executable |
| 5 | Forced Entry, end to end | create → start → photo → finish → verdict; one Airtable row; `Test Result` **and** `Forced Entry Result` both carry the verdict; no `ANSI Result` |
| 6 | ANSI Z97.1, end to end | same, mirrored |
| 7 | Impact, five impacts | five attempts, five rows, `Impact Number` 1–5, each with its own photograph and verdict |
| 8 | Impact on an `IMPACT_SMI` section | **no family control offered** |
| 9 | Abort one attempt of each type | accepted with a reason; no evidence required |
| 10 | Correct a reviewed attempt | new attempt; original row unchanged in Airtable; `Corrects Attempt ID` set |
| 11 | Stop the worker, complete a test, restart it | nothing lost; status honest throughout; row appears once |
| 12 | Re-publish the same attempt | **same** Airtable record id, no duplicate |

**1–12 green, performed by an operator, is the definition of done.** Until then TC5 is an
**EXTERNAL BLOCKER** and this release cannot go.

---

## 8. What not to build

- **No second interface for static and cyclic.** Those screens exist and work. Screen 2 is the only
  addition they need.
- **No verification pre-fill, and no override.** §2.
- **No client-side derivation.** `impact_classification`, the fourteen stages, `Cycles Completed`,
  `Impact Result` and both per-standard results are all derived server-side. Render them.
- **No editing after review.** Terminal measurements, identities and requirement snapshots are immutable by
  contract §4. The correction route is the only path.
- **No credential in `config.json`.** Both `deployment/config/config.json` and
  `src/ifet_ui_react/config.json` are served to the browser. The Airtable token is server-side only, and
  the UI never talks to Airtable — it talks to LabOS.
