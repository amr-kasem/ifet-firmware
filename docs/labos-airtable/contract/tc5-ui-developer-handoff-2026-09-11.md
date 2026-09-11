# TC5 — UI developer handoff

**Date:** 2026-09-11 · **For:** the assigned UI developer · **Supersedes:**
`tc5-operator-interface-contract-2026-09-11.md`

**Every route, payload and error in this document was verified against the running application on
2026-09-11**, not against a description of it: all 28 cited routes resolve against `openapi.json`, which is
itself gated — `TheCommittedApiContractIsCurrent` fails the test suite if the committed snapshot drifts
from the app. A second pass the same day re-audited every domain claim against the code, the tests and the
generated OpenAPI after TA6, TA7 and DG14; the eight corrections it produced are in §7. **This document is
the canonical UI implementation contract** — where any other document disagrees, this one is right.

**The backend is feature-frozen.** Nothing here is planned; all of it is live and proven end to end on the
real wire. If something you need is genuinely missing, say so and we will classify it before changing
anything — but the five workflows are each demonstrated against the live Testing base today.

| Reference | What it is |
|---|---|
| `ifet-management/src/management_service/openapi.json` | **generated and gated.** The last word on any shape |
| `ifet-management/MANUAL_TESTS_API.md` | prose and reasoning behind the manual-test routes. **Subordinate to this document on any domain question** — it is the deeper API reference, not a second model |
| `tests/test_manual_tests.py` (91) · `tests/test_requirement_release.py` (24) | executable behaviour. Read them as specification |
| `docs/labos-airtable/testing/five-workflow-e2e-acceptance-2026-09-11.md` | the acceptance run your screens will be signed off against |

---

## 0. Scope — five screens

| # | Screen | Covers |
|---|---|---|
| 1 | Job picker | selecting and importing Airtable work |
| 2 | **Requirement release** | the DG14 verification. **Static and Cycles do not run without it** |
| 3 | Manual test | Forced Entry **and** ANSI Z97.1 — one screen, type switch |
| 4 | Impact | classification, target velocity, one attempt per impact |
| 5 | Sync status | did it reach Airtable, and what to do if not |

Screens 3 and 4 share one **attempt component**. Start → evidence → finish/abort → verdict is the same
lifecycle on the same `/test-results/{id}` routes for all three types. Build it once.

**Three rules that hold across every screen:**

- **Backend is authoritative. Do not port domain validation into JavaScript.** Mirror the server's refusal,
  do not pre-empt it. Every rule below is enforced server-side and will be enforced whatever the UI does.
- **Never compute a derived value.** `impact_classification`, the fourteen static/cyclic stages,
  `Cycles Completed`, `Impact Result` and both per-standard results are derived server-side. Render them.
- **⚠️ For an imported job, never create a test.** The import already made it. §0.1 — this is the one rule
  whose breach is a data-model bug rather than a cosmetic one, and the API will not stop you.

### 0.1 ⚠️ Where the test object comes from — read this before Screens 3 and 4

**`POST /airtable/import` already creates the Forced Entry, ANSI Z97.1 and Impact tests**, one per
executable Protocol Section (`importer.bind`). They return on the import response as `manual_tests[]`
and `missile_impact_tests[]`, already carrying their `airtable_*` ids, `required_option`, and — for
Impact — a frozen `impact_family`.

| Workflow | Airtable-bound job | LabOS-only job |
|---|---|---|
| Impact | **select** the imported test; `PATCH` it to add level / velocity | **`POST /projects/{pid}/impact-tests/`** |
| Forced Entry | **select** the imported test | **`POST /projects/{pid}/manual-tests/`** with `type` |
| ANSI Z97.1 | **select** the imported test | **`POST /projects/{pid}/manual-tests/`** with `type` |

**Calling `POST` on an imported job is not refused.** It creates a *second* test with its own
`labos_test_id`, which publishes to Airtable as an unrelated group of rows against the same section —
and nothing downstream can tell that group from a real one. The `POST` routes exist for LabOS-only
work, where there is no import to have made the test.

Reload with `GET /devices/{id}/projects/` to list them. **There is no `GET /projects/{id}`** — the only
method on that path is `PUT`.

### 0.2 Status language, stated once

| | |
|---|---|
| **Implemented in `feature/labos-airtable`** | everything in this document |
| **Verified against the live Testing base** | TA6 probe 97/97, TA7 probe 64/64, both 2026-09-11 |
| **Deployed to the `management` node** | **no** |
| **Applied to the Production Airtable base** | **no** — Production is untouched at 142 fields |

Where this document says "not deployed" it means **not deployed to Production**. The Testing base
carries all 164 fields today, including both TA6 result columns and both TA7 Impact columns.

---

## 1. Screen 1 — Job picker

**Purpose.** Choose an Airtable job, see what LabOS will and will not run, and import it into a LabOS
project on a chosen rig.

**Every read hits a local mirror, never Airtable.** A picker at a rig cannot depend on someone else's API
being up, so an empty mirror gives an empty list rather than a spinner.

| Step | Method | Route | Request | Response fields that matter |
|---|---|---|---|---|
| list jobs | `GET` | `/airtable/projects` | — | `projects[]`: `record_id`, `job_number`, `project_name`, **`mirrored_at`**; `count` |
| list specimens | `GET` | `/airtable/projects/{record_id}/specimens` | — | `specimens[]`: `record_id`, `name`, **`imported_project_id`** |
| list protocols | `GET` | `/airtable/specimens/{record_id}/protocols` | — | `protocols[]`: `record_id`, `name` |
| list sections | `GET` | `/airtable/protocols/{record_id}/sections` | — | `record_id`, `section_name`, `requirement_code`, `applicability`, **`executable`**, **`refused`** |
| refresh mirror | `POST` | `/airtable/refresh` | — | the only route that calls Airtable |
| dry-run import | `POST` | `/airtable/import/plan` | `{device_id, project_record_id, specimen_record_id, protocol_record_id}` | executable / unconfirmed / refused sections, `design_pressures` |
| import | `POST` | `/airtable/import` | same body, plus optional `name` | full `ProjectSchema` |

**Operator-entered:** the job, the specimen, the protocol, and **`device_id`** — which physical rig. That
last one is the operator's decision; Airtable has no opinion on it.

**Read-only / pre-filled:** everything else. `gauge_count`, `impact_count` and the `airtable_*` ids come
back on the import response, so a pre-filled form can show what was filled in.

**Validation and errors:**

| | |
|---|---|
| `400` on import | the protocol cannot be imported — no design-pressure pair, a mismatched hierarchy, two disagreeing pairs, or a refused section. **Show `detail` verbatim**; it names the section and the reason |
| repeat import | **not an error.** Idempotent on the mock-up: returns the project it already made |

**Three behaviours to build around:**

1. **Show `refused`.** It is the one thing the operator can act on, and it is a sentence. A section list
   that hides refusals just looks like a shorter protocol.
2. **Show `mirrored_at`.** A stale mirror is not an error, but its age is a fact the operator should have
   before deciding the list is complete.
3. **`imported_project_id` means "already imported".** Say so, rather than letting someone import twice and
   wonder why nothing changed.

**Acceptance:** import a job; refused sections are visible with reasons; a second import of the same
mock-up returns the same project rather than creating a second one.

---

## 2. Screen 2 — Requirement release ⚠️ new, and nothing runs without it

**Purpose.** Record that a named person has read the design-pressure pair off the trusted proposal, so an
imported Static Load or Cycles job may run.

**Why it exists, because the interaction design depends on understanding it.** LabOS derives all fourteen
static and cyclic stages from the imported pair. The upstream extractor is known to shift values one column
to the left, so a 60 PSF requirement can arrive as **9** — a number, in the right column, with the right
unit, of the right kind. It validates. Nothing can detect it by looking at it. The control is that **two
independent readings of the same fact must agree**.

| Step | Method | Route | Request |
|---|---|---|---|
| read state | `GET` | `/projects/{id}/requirement-release?kind=static&static_test_index=0` | — |
| record | `POST` | `/projects/{id}/requirement-verification` | `{inward_psf, outward_psf, unit, reference, verified_by}` — **all five required** |

`GET` response, and `POST` returns the same shape:

```json
{"executable": false,
 "code": "unverified",
 "reason": "this requirement came from Airtable and has not been independently verified …",
 "airtable_section_id": "rec…",
 "imported_pair_psf": [60.0, 45.0],
 "verified_pair_psf": null}
```

`code` is a stable token to branch on; `reason` is the sentence to show.

| `code` | Meaning and screen behaviour |
|---|---|
| `local` | executable. A LabOS-only job — the operator typed these pressures. **Do not show this screen at all** |
| `released` | executable. Show who verified it and against which document |
| `unverified` | **the normal first state of an imported job.** Show the form |
| `verification_disagrees` | show **both** pairs, escalate. No "use theirs" button |
| `project_drifted_from_mirror` | the section changed upstream after import. Offer re-import |
| `invalid_requirement` | the section no longer validates. Show `reason` verbatim |
| `section_missing` | gone from the mirror. Offer refresh, then re-import |
| `not_a_pair` | bound to a section with no design-pressure pair |

**Operator-entered:** `inward_psf`, `outward_psf`, `unit` (must be `PSF`), `reference`, `verified_by`.
**Read-only:** `imported_pair_psf`, `code`, `reason`.

### ⚠️ The interaction, and it is the control rather than a preference

**Do not pre-fill the pair from `imported_pair_psf`, and do not display it beside the input fields.** A
pre-filled value the operator confirms is one reading, not two, and the entire control collapses into a
click. The intended interaction is:

1. the operator has the proposal open, or in hand;
2. they **type** the inward and outward values from it, and the document reference;
3. they submit;
4. **the server compares.** If the two agree, the job is released. If they disagree, the server refuses and
   the response tells the operator both numbers — that is the moment the imported pair first appears on
   screen, and it appears as an explanation of a refusal.

**No "use the Airtable value" affordance anywhere.** The server refuses to choose between two contradicting
sources, on purpose. A UI that offers to choose puts back exactly the failure this prevents.

**Errors:**

| Code | When | Show |
|---|---|---|
| `409` | the pairs disagree | `detail` verbatim — it contains both pairs. **Nothing was stored.** Offer: re-read the proposal, or escalate to fix the Airtable section |
| `409` | blank `reference` or `verified_by`, or `unit` ≠ `PSF` | `detail` |
| `409` | a rig attempt already exists | immutable now. A change needs a new run |
| `400` | this job has no Airtable-bound rig test | do not show the screen for this job |

**Acceptance:** starting a static stage before verifying is refused and the reason is shown; a deliberately
wrong pair is refused with both values displayed and nothing stored; the correct pair releases the job and
the stage then runs.

---

## 3. Screen 3 — Forced Entry and ANSI Z97.1

**Purpose.** Run a pass/fail test judged against a named grade or class, with notes and photographs.

One screen. The only differences are the `type` value and the word used for `required_option`.

| Step | Method | Route | Request |
|---|---|---|---|
| **imported job: select the test** | `GET` | `/projects/{pid}/manual-tests/` | `?type=` optional. **The import already created it — §0.1** |
| **LabOS-only job: create it** | `POST` | `/projects/{pid}/manual-tests/` | `{type, required_option?, airtable_protocol_id?, airtable_section_id?, airtable_section_name?}` |
| **start attempt** | `POST` | `/projects/{pid}/manual-tests/{id}/trials` | `{operator_name}` |
| finish the **attempt** | `PUT` | `/test-results/{aid}/finish` | `{result, …}` — **`result` is required here.** §5 |
| finish the **test** | `PUT` | `/projects/{pid}/manual-tests/{id}/finish` | — closes it to further attempts |

`type` is exactly `"Forced Entry"` or `"ANSI Z97.1"` — anything else is `422`.

**Pre-filled / read-only:** `required_option` — the grade (`"ASTM F588 Grade 40"`) or class (`"Class A"`)
— is copied **verbatim** from the section's `Required Option` when the job was imported. **Show it as the
requirement.** Typed by the operator only on a LabOS-only test.

⚠️ **It is free text, it is optional, and nothing validates it.** `FORCED_ENTRY` and `ANSI_IMPACT` carry
requirement kind **`Not Applicable`**, so `requirements.validate` does not require an option at all —
a section with a blank `Required Option` imports and is executable. There is no vocabulary anywhere in the
code for grades or classes: LabOS does not recognise `Grade 40`, does not rank it, and does not refuse an
unfamiliar string. **Do not build a picker, and do not mark a test non-executable because a grade looks
wrong** — that behaviour belongs to `STATIC_PROGRAMME`, which is the only `Enum` requirement and the only
one with a supported-values list. What *is* refused is a `Not Applicable` section carrying a numeric
`Required Value`, because that means the section is describing a different test.

**Operator-entered:** `operator_name` at start; then result, note and photographs; then the verdict.

Then the shared attempt lifecycle in §5.

**What the screen must convey that is not obvious:**

- **There is no numeric requirement.** The grade or class is the whole requirement, it is free text, and
  a blank one is legal. Display whatever arrived.
- **ANSI Z97.1 is recommended first on a specimen and is deliberately not enforced** — approved by the
  product owner on 2026-09-10. Show it as guidance; do not block.
- **The result lands in two columns.** `Test Result` as always, **and** `Forced Entry Result` or
  `ANSI Result` — the same value on its own axis. The UI sends one verdict; the backend projects it. Do not
  offer two result controls.

**No photograph is required** to finish a Forced Entry or ANSI attempt — only `result`. That gate is
Impact's alone.

**Acceptance:** select (imported) or create (LabOS-only) → start → photo → finish → verdict; exactly one
Airtable row; `Test Result` and the type's own result column both carry the verdict; the other type's
column is **absent**, not blank.

---

## 4. Screen 4 — Impact

**Purpose.** Run an impact test where **one physical impact is one attempt is one Airtable row.**

| Step | Method | Route | Request |
|---|---|---|---|
| **imported job: select the test** | `GET` | `/projects/{pid}/impact-tests/` | **the import already created it, with `impact_family` frozen — §0.1** |
| **LabOS-only job: create it** | `POST` | `/projects/{pid}/impact-tests/` | `{}` is valid — everything optional |
| set the operator's values | `PATCH` | `/projects/{pid}/impact-tests/{id}` | `{impact_level?, target_velocity?, impact_family?}` |
| **start one impact** | `POST` | `/projects/{pid}/impact-tests/{id}/trials` | `{operator_name}` |
| record the impact | `POST` | `/test-results/{aid}/shots` | `{result, area?, velocity?, note?}` — `result` required |
| photograph it | `POST` | `/shots/{sid}/photos` | multipart, once per photograph |
| **finish this impact** | `PUT` | `/test-results/{aid}/finish` | — then review it, then loop back to "start one impact" |
| finish the **whole test** | `PUT` | `/projects/{pid}/impact-tests/{id}/finish` | once, at the end. Closes it to further impacts |

### ⚠️ Two operations are called "Finish" and they are not interchangeable

| Button | Route | Means | How often |
|---|---|---|---|
| **Finish impact** | `PUT /test-results/{aid}/finish` | this impact is done | once per impact |
| **Finish test** | `PUT /projects/{pid}/impact-tests/{id}/finish` | the sequence is over | once, at the very end |

After the test-level finish, `POST …/trials` returns **400**. Do not offer both under the same word.

**The required impact count is not enforced.** `impact_count` is accumulated at import from the
`IMPACT_LMI` / `IMPACT_SMI` sections' `Required Value` and published as a requirement, but **no route
compares it to the number of attempts** — finishing after three of five is accepted. Show the operator
`3 of 5` and warn if they finish early; the API will not.

### The per-impact loop, in order

```
select/create test → PATCH level + target velocity        (once, before the first impact)
  └─ start attempt → record shot → photograph → finish attempt → verdict     (impact 1)
  └─ start attempt → record shot → photograph → finish attempt → verdict     (impact 2)
  └─ …
finish test                                               (once, at the end)
```

`impact_level` and `target_velocity` must be set before the **first** attempt completes — after that
they are `409`. The level is per *test*, not per impact.

### The classification control — this shape is required

| Section's `Requirement Code` | What the screen offers |
|---|---|
| `IMPACT_SMI` | **no family control.** Display "SMI", read-only |
| `IMPACT_LMI` | a **required** D / E choice, and nothing else |
| LabOS-only test | a family choice, **write-once** — fixed as soon as any attempt exists, aborted included |

**Never a three-option picker on an Airtable-bound test.** The SMI/LMI half is Airtable's answer, frozen at
import; offering it invites a contradiction the API rejects with `400`.

**Operator-entered:** `impact_level` (LMI only), `target_velocity`, `operator_name`, each impact's
`result`, and optionally `area` / `velocity` / `note` per impact.

**Read-only / derived:** `impact_classification` — `SMI` · `LMI Level D` · `LMI Level E` — comes back on
the test and the project. **Render it; never compute it, never send it.**

**⚠️ Two velocities, and they must not share a control.** `target_velocity` is per *test*, operator-entered,
ft/s, and is what LabOS publishes as `Target Impact Velocity`. `shots.velocity` is the achieved velocity of
one impact and stays per shot, inside the JSON. Different fields, different meanings.

**Errors:**

| Code | When |
|---|---|
| `400` on `PATCH` | `impact_family` on an Airtable-bound test; or any unexpected key is `422` |
| `409` on `PATCH` | `impact_level` / `target_velocity` after an attempt has **completed** |
| `400` on finish | no resolvable classification, or no `target_velocity`. **An abort needs neither** |
| `400` on finish | **"A completed impact attempt requires at least one photograph."** A per-impact photograph counts; evidence cannot be added after review |
| `400` on finish | **exactly one impact**, not "at least one" — zero has nothing to report |
| `409` on a second `POST …/shots` | *"One attempt is one impact — start a new attempt on this test to record the next one."* This is the sequence working, not an error to hide |

### ⚠️ Next impact, retest, correction — three buttons, and Impact blurs two of them

| The operator means | Do this | `Impact Number` | `Corrects Attempt ID` |
|---|---|---|---|
| fire the next impact | `POST …/trials` | next (3 → 4) | blank |
| re-run an impact that went wrong physically | `POST …/trials` | next (3 → 4) | blank |
| the *record* of an impact is wrong | `POST /test-results/{aid}/correct` | **next (3 → 4)** | set |

**Under one-impact-per-attempt, "next impact" and "retest" are the same call and are indistinguishable in
the data.** That is by design — a re-fired impact *is* another impact — but it means a "Retest" button on
this screen is just the next impact, and should be labelled that way rather than implying it replaces
anything.

**A correction also takes the next ordinal**, because `Impact Number` *is* `Attempt Number` by
construction. So correcting impact 3 publishes a row with `Impact Number` 4 carrying
`Corrects Attempt ID` → impact 3. Render the correction chain, not the ordinal, when showing what
supersedes what — the numbers alone will read as six impacts when five were fired.

**Acceptance:** five impacts produce five attempts and five Airtable rows with `Impact Number` 1–5, each
with its own photograph and verdict; an `IMPACT_SMI` section offers no family control; a re-publish of the
same attempt updates the same row.

---

## 5. The shared attempt lifecycle

| Step | Method | Route | Request |
|---|---|---|---|
| finish | `PUT` | `/test-results/{id}/finish` | `{result, note?, testing_continued?}` **or** `{abort_reason}` |
| review | `PUT` | `/test-results/{id}/verdict` | `{test_result, verdict_by, retest_required, rationale?}` |
| attempt-level photo | `POST` | `/test-results/{id}/photos` | multipart: `file`, optional `note` |
| correct | `POST` | `/test-results/{id}/correct` | `{reason}` → a **new** attempt superseding this one |

**State transitions, and what each state offers:**

| State | Offer |
|---|---|
| `In Progress` | record evidence · **Finish** · **Abort** |
| `Completed` / `Aborted`, not yet reviewed | **Review** · **Correct** |
| reviewed | **Retest** (a new attempt) · **Correct**. **Nothing is editable** |

### ⚠️ Operator outcome and reviewer verdict are two different fields

Both are called "result" in casual speech. **Do not use one word for them in the UI.**

| | Operator outcome | Reviewer verdict |
|---|---|---|
| Field | `result` | `test_result` |
| Type | boolean | `Pass` · `Fail` · `Inconclusive` |
| Who | the **operator**, named in `operator_name` | the **reviewer**, named in `verdict_by` |
| When | at `finish` | at `verdict`, afterwards |
| Where it is entered | FE / ANSI: the finish body. **Impact: on the shot** — `POST …/shots` `{result}`, and the attempt copies it | the verdict body |
| Required? | yes for FE / ANSI; for Impact it is derived from the shot rather than sent | yes, once |
| Suggested label | **"Operator outcome"** — *the specimen resisted / it did not* | **"Reviewer verdict"** |

They are separate columns so that an operator cannot certify their own work, and `operator_name` /
`verdict_by` are stored separately even when the same person does both. Neither is authenticated — LabOS
has no user table — so remember the last name per device, but never imply proof.

**What Airtable receives, by phase:**

| Phase | `Test Result` | `Forced Entry Result` / `ANSI Result` | `Impact Classification` / `Target Impact Velocity` |
|---|---|---|---|
| create | `Pending` | `Pending`, own type only | — |
| **terminal** (finish) | **still `Pending`** | **still `Pending`**, own type only | sent, Impact only |
| **first review** (verdict) | `Passed` · `Failed` · `Inconclusive` | same value, own type only | unchanged |

`Pass` → `Passed` and `Fail` → `Failed` on the wire; `Inconclusive` is unmapped and goes as-is. The
per-standard column is **omitted entirely** on the other four types — an absent key, never a blank cell.
The operator's boolean `result` is **not** published as a scalar at all; it travels inside the JSON.

- `test_result` is `Pass` · `Fail` · `Inconclusive`. At terminal the published `Test Result` is `Pending`;
  the first review replaces it. Show `Pending` as a real state, not as missing data.
- **`retest_required` is required and not defaulted.** An unchecked box is not a decision.
- **Start is idempotent.** `POST …/trials` on a test with an open attempt returns **that** attempt — a
  double-click cannot become two certification records. A "Retest" button must finish or abort first.
- **One active run per rig → `409`**, naming the blocking attempt and its type: *"This rig is already
  running attempt N of another test (Cycles). One rig runs one test at a time; finish or abort that attempt
  first."* Surface it. **This applies to the manual tests too.** They command no hardware — `report-api`
  has no MQTT client — but they hold the same per-`device_id` lock as Static Load and Cycles, so an Impact
  attempt blocks a Cycles one and vice versa. They are forms that occupy the rig.

**Photographs:** `POST`-only, one call per photograph, `multipart/form-data`. **There is no delete** —
evidence is append-only until review, and cannot be added after it. Impact photographs attach to a *shot*;
Forced Entry and ANSI photographs attach to the *attempt*.

**Correction is not retest.** A retest is another go at the same test; a correction says the earlier record
is wrong. Both create a new attempt; only one means "disregard the previous row". Its three `400`s: the
original is still open (finish or abort it), the test already has an open attempt, or the attempt predates
the per-type tables. **Never offer "Correct" as a synonym for "try again"** — it writes
`Corrects Attempt ID` onto a row that supersedes nothing, and no route takes it back.

---

## 6. Screen 5 — Sync status

**Purpose.** Tell the operator whether a saved result reached Airtable, and give them the one action that
helps when it did not.

| Step | Method | Route |
|---|---|---|
| headline | `GET` | `/sync/status` |
| the queue | `GET` | `/sync/queue` — `?state=parked` is the useful filter |
| un-park one | `POST` | `/sync/queue/{id}/retry` |
| refusals | `GET` | `/sync/failures` |
| repair one | `POST` | `/sync/failures/{id}/repair` — `409` while still refused, with the current reason |

**`GET /sync/status` returns exactly these keys** — verified against the running app on 2026-09-11:

```json
{"led": "red", "status": "Sync Failed",
 "attachment_backlog": 0, "attachment_parked": 0,
 "artifacts_needing_reconciliation": 0, "failed_publications": 0,
 "worker_alive": false, "heartbeat_age_seconds": null,
 "queue_depth": 0, "parked": 0, "blocked_attempts": [], "revision": 0,
 "last_push_ok_at": null, "last_pull_ok_at": null,
 "last_push_error": null, "last_pull_error": null}
```

`status` is one of `Synced` · `Pending` · `Sync Failed` · `Retry Required` — the Airtable team's own four
words, which is why they are contractual values rather than ours.

**⚠️ Two things a screen gets wrong if nobody says them:**

1. **Liveness is `worker_alive` + `heartbeat_age_seconds`.** There is no `worker_heartbeat_at`; our own
   documentation named one until 2026-09-11 and it never existed. The worker has no health endpoint,
   deliberately — one answering its own health check would report healthy from inside a process whose
   database connection had gone.
2. **A dead worker reads as `Sync Failed` with a completely empty queue.** That is correct and it is not a
   data problem. **Check `worker_alive` before presenting the headline as a failed result**, or the first
   thing an operator sees on a quiet morning is a red light about nothing.

**`/sync/failures` needs its own surface.** These are results saved correctly that LabOS *refused to
queue* — they never got a queue entry, so they are invisible in `/sync/queue` by construction. Before this
route existed the headline read `Synced` for an attempt that had never been published.

**Show `attachment_backlog` separately from `failed_publications`.** A photograph still in flight is not a
result that failed, and a parked attachment must not drag the headline to `Retry Required`.

---

## 6a. The whole thing on one page

| | Impact — SMI | Impact — LMI | Forced Entry | ANSI Z97.1 |
|---|---|---|---|---|
| **Test object** | imported → **select**; LabOS-only → `POST …/impact-tests/` | same | imported → **select**; LabOS-only → `POST …/manual-tests/` | same |
| **Family / type** | `impact_family = SMI`, **frozen by the importer. No control** | `LMI` frozen; operator picks **level D or E** (required) | `type = "Forced Entry"` | `type = "ANSI Z97.1"` |
| **Operator inputs** | `target_velocity`, `operator_name`, per-impact `result` (+ `area`/`velocity`/`note`) | same, **plus `impact_level`** | `required_option` (LabOS-only), `operator_name`, `result`, note | same |
| **Start** | `POST …/impact-tests/{id}/trials` — **once per physical impact** | same | `POST …/manual-tests/{id}/trials` | same |
| **Evidence** | `POST /shots/{sid}/photos` — **≥1 required** | same | `POST /test-results/{aid}/photos` — optional | optional |
| **Attempt finish** | `PUT /test-results/{aid}/finish` — needs exactly 1 impact, ≥1 photo, classification, target velocity. `result` derived from the shot | same | `PUT /test-results/{aid}/finish` — **`result` required** | same |
| **Review** | `PUT /test-results/{aid}/verdict` — once, `verdict_by` + `retest_required` required | same | same | same |
| **Logical-test finish** | `PUT …/impact-tests/{id}/finish` — once, after the last impact. **Count not enforced** | same | `PUT …/manual-tests/{id}/finish` | same |
| **Airtable-bound restrictions** | no family control; `impact_family` is `400` on `PATCH`; do not create the test | same | do not create the test; `required_option` is read-only | same |
| **Airtable row** | one per impact; `Impact Number`, `Impact Result`, `Impact Classification`, `Target Impact Velocity` | same | one; **`Forced Entry Result`** beside `Test Result` | one; **`ANSI Result`** beside `Test Result` |
| **Important errors** | `409` second shot · `409` `PATCH` after a completed attempt · `400` finish gates | same · `400` level on SMI | `422` bad `type` · `400` finish without `result` | same |

**LabOS-only work differs in exactly three ways**, and nowhere else: the test is created by `POST` instead
of selected; `impact_family` is the operator's (write-once, fixed by the first attempt of any kind,
aborted included); and `required_option` is typed rather than pre-filled. The attempt lifecycle,
the gates, the verdict and the Airtable projection are identical — an unbound test simply publishes
nothing.

---

## 7. Backend findings from this verification pass

Re-run 2026-09-11 as a contract-alignment audit against code, tests and generated OpenAPI.

| Finding | Classification | Action |
|---|---|---|
| `/sync/status` documented as returning `worker_heartbeat_at`; it returns `worker_alive` + `heartbeat_age_seconds` | **documentation defect** — the API was always right | Fixed in `MANUAL_TESTS_API.md` and stated above |
| **Neither UI document said the importer already creates the FE / ANSI / Impact tests.** Both presented `POST` as the way to obtain one | **documentation defect, highest consequence** — following it on an imported job creates a duplicate test and a parallel group of Airtable rows | §0.1 added here; §7 rewritten in `MANUAL_TESTS_API.md` |
| `MANUAL_TESTS_API.md` §4 still described **one attempt containing several impacts**, with `shot_number` restarting at 1 per attempt and "at least one impact" at finish | **documentation defect** — code has enforced exactly one since TC1h | §4 rewritten |
| `MANUAL_TESTS_API.md` §9 still said **no dedicated Airtable scalar** exists for Forced Entry or ANSI | **documentation defect** — reversed by the product owner 2026-09-10, built as TA6 | §9 rewritten |
| This document claimed an unrecognised grade leaves a Forced Entry / ANSI test **non-executable** | **documentation defect** — `FORCED_ENTRY` / `ANSI_IMPACT` are kind `Not Applicable`; `required_option` is optional free text and no vocabulary exists | §3 corrected |
| `MANUAL_TESTS_API.md` carried **"not yet deployed"** and "the fields do not exist in any base" | **stale temporal language** — both TA7 fields are live in the Testing base | §0.2 here; §7 there |
| `projects.impact_count` gates nothing — the logical-test finish accepts any number of impacts | **behaviour, correctly implemented, previously undocumented** | Stated in §4; the warning is the screen's |
| A correction of impact *N* publishes as `Impact Number` *N+1* | **consequence of `Impact Number` = `Attempt Number` (§4.5a), not a defect** | Stated in §4 |
| All 28 routes cited resolve against the live app; the manual-test surface is now **20 routes**, not the 18 of 2026-09-08 | — | Count corrected in `MANUAL_TESTS_API.md` |
| Running all 14 suites in one pytest process exhausts `postgres:13`'s connections and fails ~45 unrelated tests | **test-harness limitation, not product** | Run per file; noted in `MANUAL_TESTS_API.md` |

**No REQUIRED INTEGRATION GAP was found. The backend remains frozen — nothing in this pass changed code.**
Every capability the five screens need already exists. If you hit one that does not, raise it and we will
classify it as **REQUIRED INTEGRATION GAP** or **UI CONVENIENCE** before any code changes — convenience
goes to backlog while the backend stays frozen.

---

## 8. Acceptance — TC5 closes when these pass with a real operator

Against the Testing environment, performed by someone who is not the developer. Scenarios, expected API
calls and pass conditions are in
`../testing/five-workflow-e2e-acceptance-2026-09-11.md`.

| # | | Pass condition |
|---|---|---|
| 1 | Import an Airtable job | refused sections visible with reasons; re-import returns the same project |
| 2 | **Start a static stage before verifying** | **refused**, §3.3 reason shown |
| 3 | Verify the pair correctly | released; static and cyclic run |
| 4 | **Verify with a wrong pair** | **refused**, both pairs shown, nothing stored, still not executable |
| 5 | Forced Entry end to end | one row; `Test Result` **and** `Forced Entry Result` carry the verdict; no `ANSI Result` |
| 6 | ANSI Z97.1 end to end | mirrored |
| 7 | Impact, five impacts | five attempts, five rows, `Impact Number` 1–5 |
| 8 | Impact on an `IMPACT_SMI` section | **no family control offered** |
| 9 | Abort one attempt of each type | accepted with a reason; no evidence required |
| 10 | Correct a reviewed attempt | new attempt; original row unchanged; `Corrects Attempt ID` set |
| 11 | Stop the worker, complete a test, restart | nothing lost; status honest; row appears once |
| 12 | Re-publish the same attempt | **same** record id, no duplicate |

---

## 9. What not to build

- **No second interface for Static Load and Cycles.** Those screens exist. Screen 2 is the only addition
  they need.
- **No verification pre-fill and no override.** §2.
- **No client-side derivation.** §0.
- **No editing after review.** Terminal measurements, identities and requirement snapshots are immutable by
  contract §4. The correction route is the only path.
- **No credential in `config.json`.** Both `deployment/config/config.json` and
  `src/ifet_ui_react/config.json` are served to the browser. The Airtable token is server-side only, and
  the UI never talks to Airtable — it talks to LabOS.
