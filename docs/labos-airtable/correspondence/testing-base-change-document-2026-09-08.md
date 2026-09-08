# Testing Base — your three questions, and the changes made

**From:** LabOS (Abdelrahman) · **To:** the Airtable team · **Date:** 2026-09-08
**Base changed:** Testing `app4oXS3Kd5IKWgJ7` — **142 → 160 fields**
**Base NOT changed:** Production `app0OCunbmuXl7Hc9` — **unchanged at 142, verified live**

This is two things in one: **answers to the three clarifications you raised**, and the document requested at
the 2026-09-06 meeting — *"Prepare and share a document outlining all changes made & explanation/reason of
that changes in the Testing Base."* Your questions are answered first, because they are what you are waiting
on; §2 onward is the reference behind the answers.

---

## 0. Your three questions

### 0.1 `Required Value` — it never holds a range, a sign or a symbol

The short answer: **a value like `+110/110` is not encoded into `Required Value`. It is split across the
fields beside it.** `Required Value` is a plain `number` and stays empty whenever the requirement is not a
single scalar.

| The proposal says | How it is represented |
|---|---|
| `+110/110` | `Requirement Kind = Directional Pair` · `Required Value Inward = 110` · `Required Value Outward = 110` · `Required Unit = PSF` · **`Required Value` empty** |
| `11.25` | `Kind = Magnitude` · `Required Value = 11.25` · `Unit = PSF` |
| `2` impacts | `Kind = Count` · `Required Value = 2` · `Unit = impacts` |
| `Full` | `Kind = Enum` · `Required Option = Full` · **no number at all** |
| blank, `N/A`, `—` | `Kind = Not Applicable` · every numeric field empty. **Blank is never zero** |

**No negative numbers, ever.** Magnitudes are positive and direction comes from the *field name*
(`…Inward` / `…Outward`), not from a sign. This is deliberate: it removes the "is `-60` outward or an error?"
question completely.

**This matters more than it looks.** If ranges or signs go into `Required Value`, LabOS is back to parsing
strings — and string parsing is exactly where the extractor defect lives. The typed fields exist so that
never has to happen again.

### 0.2 Unit per protocol section — already determined by `Requirement Code`

You do not need to decide this per section. The code fixes it:

| `Requirement Code` | `Requirement Kind` | `Required Unit` |
|---|---|---|
| `STATIC_PRESSURE` · `CYCLIC_PRESSURE` | Directional Pair | `PSF` |
| `WATER_PRESSURE` | Magnitude | `PSF` |
| `IMPACT_LMI` · `IMPACT_SMI` | Count | `impacts` |
| `GAUGE_COUNT` | Count | *blank* |
| `STATIC_PROGRAMME` | Enum | *blank* |
| `FORCED_ENTRY` · `ANSI_IMPACT` | Not Applicable | *blank* |

`Missile Weight` (pounds) and `Impact Velocity` (ft/s) carry their own units in their own fields and do not
use `Required Unit`.

**Where a unit and a kind disagree, LabOS refuses the section rather than assuming** — a wrong unit is not a
rounding error, it is a different test. An earlier draft of this document told you that check was specified
and not yet built; it is built now, and a section it refuses is reported to the operator with the reason,
because that is the one thing they can fix. Blank is never read as zero, and blank `Applicability` is never
read as `Not Required`.

### 0.3 Retests — your model is right, but please keep `Corrects Attempt ID`

**Your description of a retest is exactly ours, and we confirm it:** a new record, new `LabOS Attempt ID`,
incremented `Attempt Number`, the four Airtable IDs unchanged, and **the same `LabOS Test ID`**. That is
precisely what `LabOS Test ID` is for.

**But it is not a replacement for `Corrects Attempt ID`, because they answer different questions.**

| Field | Answers | Present on |
|---|---|---|
| `LabOS Test ID` | *which test are these attempts of?* | **every** attempt |
| `Corrects Attempt ID` | *which attempt does this one supersede?* | **only** a correction |

**Three** different events produce a new attempt row sharing one `LabOS Test ID`:

- **A retest** — the specimen was physically tested again. It counts as a test.
- **A correction** — a recorded result was wrong and is being superseded. **No physical test happened**, and
  it must not count as one.
- **Another impact of the same impact test** — new since 2026-09-08, and the reason for the eighteenth
  field. Our project owner respecified Impact as **one attempt per impact**, so a five-impact test now
  publishes five rows where it previously published one. Those five are one test, not five.

With only `LabOS Test ID`, those two are indistinguishable on your side. Any roll-up that counts attempts or
computes a pass rate would then be wrong — **and would look right**, which is the part that makes it
expensive. A specimen corrected twice would read as three tests.

`Corrects Attempt ID` is already in the Testing Base, it is **blank on every retest**, and it is populated
only on the rarer correction case. It costs nothing to keep and cannot be reconstructed later.

**`Impact Number` is the same argument applied to the third case.** `Attempt Number` already carries the
ordinal, so this field is not for our benefit — it is so that a roll-up can count **tests** by grouping on
`LabOS Test ID` and **impacts** by `Impact Number`, without needing to know a rule about which test type it
is looking at. It is blank on the other four types. Without it, a five-impact test reads as five tests, and
reads plausibly — which is the failure mode this section exists to prevent, and we would rather add one
number than ask you to special-case Impact in every view.

So: **keep both.** We are glad to drop any field you find unnecessary — this is the one we would ask you not
to.

#### The four IDs staying the same is a schema guarantee, not a convention

Worth stating precisely, because it is stronger than "we will be careful":

| Airtable ID | Lives on, in LabOS | So an attempt gets it by |
|---|---|---|
| `Airtable Project ID` | the **project** row | attempt → test → project |
| `Airtable Mockup ID` | the **project** row | attempt → test → project |
| `Airtable Protocol ID` | the **test** row | attempt → test |
| `Airtable Section ID` | the **test** row | attempt → test |

None of the four is stored on the attempt. They are read through the parent rows, so **two attempts at the
same test cannot carry different ones** — there is no code path that would let them diverge, because there is
no second copy to diverge from. Your statement is not something we have to agree to maintain; it is a
property of where the columns live.

What *is* per-attempt: `LabOS Attempt ID` (a fresh UUID on every insert), `Attempt Number` (allocated
server-side, never accepted from a client), and `LabOS Test ID` — reused from the first attempt at that test,
so every attempt in a group carries the identical value.

**What is implemented, precisely — because "implemented" was doing too much work in an earlier draft:**

| | State |
|---|---|
| The columns, and their placement on the parent rows | ✅ built, migrated, tested |
| Attempt ID minted per attempt; Test ID shared across a group | ✅ built for all five test types |
| The outbound mapper resolving the four Airtable IDs from an attempt | ✅ **all five types**, and every one published live against this base |
| Attempt Number allocation safe against two simultaneous starts | ✅ unique within a test at the database level, so a duplicated Start returns the attempt already running rather than opening a second |

**So the identity model we are confirming to you is not only agreed, it is
demonstrated.** Every phase of every one of the five types has been published
against this base, one row per attempt, with retries merging onto the same row
and a retest creating a separate one that keeps its `LabOS Test ID`.

Two more things we owe you honestly:

- **`Corrects Attempt ID` has no operator route yet.** The columns exist and the envelope maps them, but the
  screen that records a correction is not built. So today every attempt is a retest, and the field is
  correctly blank on all of them. That is a reason to keep the field, not to drop it: when the route lands we
  need somewhere to put the answer, and adding a field to production later is the expensive direction.
- **`LabOS Test ID` is opaque and you should treat it as such** — group and compare on equality, never parse
  it. Its internal format is ours and may change; its meaning, *"these attempts are of one test"*, will not.

### 0.4 `Test Date` as date **and** time — agreed, and already in place

`Test Date` is already a `dateTime` field in both bases; we verified it live again today. So there is nothing
to change unless you are adjusting how it *displays*, which is entirely yours.

Two details worth stating:

- **LabOS sends `2026-08-04T19:00:00Z`** — ISO-8601, UTC, without milliseconds. Your `…T19:00:00.000Z` is the
  same instant and Airtable accepts either. No measurement in this lab is precise to the millisecond, so we
  do not send them.
- **`Test Date` is the *completion* instant, and is omitted entirely while a test is running.** Your
  `Protocol Sections` automation derives its date from this field, so that dependency is worth having in
  writing. The full span is in `Testing Start Date` and `Testing End Date`.

---

**Seventeen fields were added, all to the Testing Base only.** No field was renamed, retyped, deleted or
reordered. No table, view, relationship or automation was touched. Nothing in production was modified, and
the tooling that made these changes **refuses the production base unconditionally** — there is no flag or
environment variable that overrides it.

The accompanying `production-change-spec.csv` is the sheet to work from: **one row per field for all 160**,
saying `ADD` or `KEEP`, whether LabOS reads or writes it, and why. It is generated from both live bases, not
transcribed.

---

## 1. What LabOS does and does not touch

| | Count |
|---|---|
| Fields LabOS **reads** | **20** |
| Fields **bound to the write path** | **35** — all in `LabOS Raw Data Table`, the only writable table |
| Fields LabOS **deliberately ignores** | **104** |

**"Bound to the write path" is not "always populated", and the difference matters to you.** Airtable will
show empty cells for legitimate reasons, so here is the rule: **LabOS omits a field rather than sending an
empty string, a zero or a false** (contract §6). A blank cell therefore means *not applicable to this
attempt* or *not yet known*, never *zero*.

Presence depends on two things:

| | |
|---|---|
| **Which phase** | A field belongs to one delivery phase — creation, termination, or first review. `LabOS Verdict By` is absent until someone reviews; that is correct, not missing |
| **Whether it applies** | `Corrects Attempt ID` is populated only on a correction — blank on every ordinary attempt and every retest. `Impact Result` applies to Impact only. `LabOS Photos` requires photographs to exist |

And **3** of the 35 will stay permanently empty for now — `Max Pressure Achieved`, `Deflection Value`,
`Deflection Unit`. See §4 for what each is waiting on; they are different things.

The per-field detail — phase, and whether presence is conditional — is the `write_phase` and
`delivery_state` columns of the attached `interface-schema.csv`, which is generated rather than
hand-maintained.

**The 104 is the important number.** It is the machine-readable form of *no billing, pricing, invoices,
payments or scheduling crosses the boundary*: customer emails, `Approved Proposal Amount`, `Balance Due`,
QuickBooks IDs, `Wall Scheduling/Reservation` and `Back Charges` are all present in the base and all
explicitly not read. The runtime credential is scoped and the write allowlist is a single table.

**LabOS never writes** `Protocol Sections`. Your automation keeps exclusive ownership of `Result`, `Status`
and `Testing Date`; LabOS writes its verdict to the raw-results row and your automation projects it.

### 1a. All eight tables, one row each — what we touched and what we did not

Table IDs are the same in both bases; only field IDs differ. **Two of the eight tables were changed. Six
were not touched at all**, and for three of those LabOS has no access of any kind.

| # | Table | ID | Prod | Testing | Added | LabOS reads | writes | ignores |
|---|---|---|---|---|---|---|---|---|
| 1 | IFET Projects | `tblLYcRC7q6Srjfk3` | 35 | 35 | — | 2 | 0 | 33 |
| 2 | Mock-Ups/Specimens | `tblcrGv0WJn6FTTGO` | 13 | 13 | — | 2 | 0 | 11 |
| 3 | Tests Protocols | `tblutO1Q8TNC4BLk0` | 8 | 8 | — | 2 | 0 | 6 |
| 4 | **Protocol Sections** | `tblqpvuJlSdkeS9PS` | 16 | **27** | **+11** | 13 | 0 | 14 |
| 5 | Walls & Positions | `tblVUvcSPAoneG26W` | 8 | 8 | — | **0** | **0** | 8 |
| 6 | Wall Scheduling/Reservation | `tblYjF1AApzmRDMrY` | 19 | 19 | — | **0** | **0** | 19 |
| 7 | Back Charges | `tbl0f2YxS3FHJ1dTD` | 13 | 13 | — | **0** | **0** | 13 |
| 8 | **LabOS Raw Data Table** | `tblnc9SsbXU0C0FWh` | 30 | **37** | **+7** | 1 | **36** | 0 |
| | **Total** | | **142** | **160** | **+18** | **20** | **36*** | **104** |

\* the 36 bound to the write path — 29 always, 4 conditional, 3 withheld, as §1 breaks down.

**Changed — 4 and 8, and only these.**

- **Protocol Sections `+11`.** The requirement had no machine-readable form; LabOS would have had to parse
  the `Value` text field, which is where the extractor defect lives. §2 covers each field. **LabOS reads this
  table and never writes it** — `Result`, `Status` and `Testing Date` stay yours.
- **LabOS Raw Data Table `+6`.** Six things LabOS produces that had nowhere to go: the execution span, who
  reviewed and when, the correction link, and photo previews. §3 covers each. This is the **only** table
  LabOS writes, and the runtime credential's allowlist is this table alone.

**Not changed — and the reason differs by table.**

- **1, 2, 3 — read-only joins.** **Six fields** in total: the job number and project name, the mock-up name
  and its project link, the protocol name and its mock-up link. That is the whole hierarchy LabOS needs to
  know which specimen a test belongs to. Every other field in these 56 is ignored, including `Approved
  Proposal Amount`, `Balance Due`, customer emails and the QuickBooks IDs.
- **5, 6, 7 — nothing is read or written.** `0` and `0`, all 40 fields: wall reservations, capacity
  conflicts, `Billable Amount`, `Internal Cost`, `Approval Status`. LabOS is a test executor and has no
  business reading any of it.

**Be precise about what enforces that, because we would rather you knew than assumed.** An Airtable PAT is
scoped **per base, not per table**, so our token *could* read all eight tables and write any of them.
Two things stand in the way, and both are ours:

| Layer | What it enforces | Strength |
|---|---|---|
| **Writes** | The client refuses any write to a table outside a single-table allowlist, before the request is made | Enforced in code, and tested |
| **Reads** | Nothing calls the read path for tables 5, 6 and 7 — there is no importer, mirror or query that names them | An application decision, not a credential restriction |

So the write boundary is a mechanism; the read boundary is a design decision plus this document. If you want
the read side enforced at the credential, that needs a table-scoped grant on your side, and we would welcome
it.

**The one field LabOS reads from its own results table** is `Raw Modified Time`
(`lastModifiedTime`) — Airtable-owned, used only for delivery reconciliation, never written.

**No table, view, relationship or automation was created, renamed, deleted or reordered in any of the
eight.** The eighteen changes are field additions to two tables, and every one of the 142 pre-existing
fields has the same type after as before.

---

## 2. The eleven fields on `Protocol Sections`

These exist so LabOS can be told **which test is required and against what** — machine-readably, without
parsing the `Value` text field.

| Field | Type | Why |
|---|---|---|
| `Requirement Code` | singleSelect | The stable code that routes work: `STATIC_PRESSURE`, `CYCLIC_PRESSURE`, `IMPACT_LMI`, `IMPACT_SMI`, `FORCED_ENTRY`, `ANSI_IMPACT`, `GAUGE_COUNT`, `STATIC_PROGRAMME`, `WATER_PRESSURE`. **Names change; codes must not**, so nothing routes on a section name |
| `Requirement Kind` | singleSelect | How to read the value: `Magnitude`, `Directional Pair`, `Count`, `Enum`, `Not Applicable`. LabOS refuses a kind it does not support rather than guessing |
| `Applicability` | singleSelect | `Required` / `Not Required` / `Unconfirmed`. Distinguishes *not needed* from *nobody has said yet*. **Blank means Unconfirmed, never Not Required** |
| `Required Value Inward` | number | Inward design pressure, PSF |
| `Required Value Outward` | number | Outward design pressure, PSF. **Independent of inward and never copied from it** |
| `Required Value` | number | The scalar for `Count`/`Magnitude` kinds — gauge count, impact count. **Blank is not zero** |
| `Required Unit` | singleSelect | `PSF`, `in`, `s`, `cycles`, `impacts`. Validation only — LabOS refuses a value whose unit contradicts its kind |
| `Required Option` | singleLineText | The named grade or class a pass/fail test is judged against — `ASTM F588 Grade 40`, `Class A`, `Full`. Free text, so an unrecognised option is shown but non-executable |
| `Missile Type` | singleLineText | The missile the protocol specifies, e.g. `Large Missile D` |
| `Missile Weight` | number | Missile mass, pounds |
| `Impact Velocity` | number | **Target** velocity, ft/s. A requirement, never a measurement — LabOS does not write an achieved velocity back |

### The single most important sentence in this document

> **LabOS reads these typed fields and never parses `Value`.**

`Value` is preserved verbatim and untouched. We do not read it, and no future release should be assumed to.

The reason is concrete. `Value` is populated by the PDF extractor, which drops blank cells, so a requirement
of `+60/60` can arrive as `9` — and every shifted value is individually plausible, so nothing downstream can
detect it. **A shifted value has already reached a record marked Passed.** Reading the typed fields instead
removes that failure path structurally rather than by care.

**This is what makes "the same information should not be entered twice" achievable.** These eleven fields
are how a requirement reaches LabOS without an operator retyping it. **They must be populated deliberately —
by hand, or from the trusted signed proposal — and never auto-filled from the extractor**, or the defect
simply moves into a new field.

`Inches` vs `in`: `Required Unit` uses the short forms above. LabOS validates the token and does not convert.

---

## 3. The seven fields on `LabOS Raw Data Table`

These are things LabOS produces that had nowhere to go.

| Field | Type | Why |
|---|---|---|
| `Testing Start Date` | dateTime | When execution began, UTC |
| `Testing End Date` | dateTime | When it ended, UTC |
| `LabOS Verdict By` | singleLineText | **Who** reviewed the result. Stored separately from the operator even when the same person, because the review is a distinct act |
| `LabOS Verdict At` | dateTime | **When** they reviewed it |
| `Corrects Attempt ID` | singleLineText | The attempt this one supersedes. **Without it a correction is indistinguishable from a genuine retest**, so any roll-up counting attempts or computing a pass rate would be wrong — and would look right |
| `LabOS Photos` | multipleAttachments | Downscaled previews. Originals stay in LabOS; the existing `Photos` URL field is unchanged |
| `Impact Number` | number (integer) | **Added 2026-09-08.** Which impact of the test this row records — 1, 2, 3. Populated only for `Test Type = Impact`, where one attempt is one impact; **blank on the other four types**. Count tests by grouping on `LabOS Test ID`, and impacts with this. See §0.3 |

**A note on `Test Date`, because your automation depends on it.** LabOS writes `Test Date` as the
**completion** instant and omits it while a test is running. `Testing Start Date` / `Testing End Date` carry
the full span. Your `Protocol Sections` automation derives its date from `Test Date`, so this dependency is
stated rather than left to be inferred.

---

## 4. What we deliberately did **not** create

An unwanted field is harder to remove than to add, and now that this schema becomes the basis for production,
a speculative field propagates rather than sitting harmlessly in a sandbox.

| Not created | Why |
|---|---|
| `Impact Locations` | Location is a per-impact observation LabOS records locally, not a requirement |
| `Forced Entry Result` · `ANSI Result` | No dedicated scalar needed: `Test Type` and `Test Result` are both single-selects, so your views filter and group both workflows natively. Sub-detail travels in the JSON field. **We will add one only if you name the report that needs it** |
| `Failure Notes` | Carried inside `Notes` and the JSON for this release |
| Any new table, relationship, or delta-cursor field | Not needed |

Three fields **exist and LabOS will not write them yet** — and they are waiting on **two different
things**, which an earlier draft ran together:

| Field | Why it is empty | What unblocks it |
|---|---|---|
| `Deflection Value` · `Deflection Unit` | The rigs return **raw gauge counts** never calibrated to a physical unit. Publishing them would put an uncalibrated count in a field named for inches | Bench calibration — hardware work |
| `Max Pressure Achieved` | **A source exists.** Actual pressure is on the rig's telemetry bus and renders live in our UI; nothing subscribes to it and stores the maximum | Software work on our side, already scheduled |

**We would rather send nothing than send a number we cannot stand behind.** But we are not claiming the
second one is impossible — it is a measurement we do not yet persist, and that is a different admission
from one we cannot make.

If you want fewer fields still, `Requirement Kind` is the one to drop — it can be implied from
`Requirement Code`.

---

## 5. How this was verified

Not asserted — read back.

- **Schema probe against the live base**: all table IDs confirmed, all 35 expected result fields present,
  select option sets read from the API rather than assumed.
- **A synthetic proposal was written into the Testing Base and read back**: one job, one mock-up, one
  protocol, six Protocol Sections covering all five executable requirement codes plus `GAUGE_COUNT`. Every
  field read back correctly typed, with the right values.
  **And since then, the running feature.** The same fixture has been read through the import path: mirrored,
  selected, imported, its parameters pre-filled, a test run and reviewed against it, and the result published
  back onto the Protocol Section that specified it. What that still does not exercise is the operator's
  screens, which do not exist yet — the path runs, nobody can drive it by hand.
- **The design pressures drive the whole programme.** From an asymmetric `60 / 45` PSF pair LabOS derived
  all fourteen stages — six static `[45.0, 33.75, 60, 45, 90.0, 67.5]` and eight cyclic
  `[30, 36, 48, 60 | 45, 36, 27, 22.5]`. Asymmetric on purpose: a symmetric pair would pass even if inward
  and outward were transposed.
- **`Forced Entry` and `ANSI Z97.1` carried a class in `Required Option` and no numeric value**, confirming
  the `Not Applicable` kind behaves as intended.
- The fixture job is `IFET-FIXTURE-0001` and every value in it is synthetic. It can be deleted at any time.
- **The before/after chain joins, and that is checked rather than asserted.** Two changes were made — 142 →
  156 on 2026-09-06, then 156 → 159 and 159 → 160 on 2026-09-08 — and each change's *after* snapshot is
  byte-identical to the next change's *before*. So the four snapshots are one history, not four unrelated
  readings. The generator refuses to produce the CSV if that hash check fails, and refuses if any field
  present before is absent after.
- **Nothing was removed and nothing was retyped.** Every one of the 142 pre-existing fields has the same type
  after as before. That is the property that makes this change additive in the sense that matters to your
  automations.
- **Re-checked against both live bases immediately before sending**, rather than relying on the snapshots
  above: all 18 present in Testing and correctly typed · **none** of the 18 in production · production **142**,
  testing **160**, delta **18** · all **160** rows of `production-change-spec.csv` agree with the live bases,
  0 disagreements · the fixture still reads back with its six sections and all six codes. So every number in
  this document is true of the bases as they stand today, not only as they stood when the snapshots were taken.

**Loading sequences are not in this schema and do not need to be.** LabOS derives all fourteen stages from
the design-pressure pair using fixed factors. Sending them from Airtable would create a second copy to keep
in sync for no gain.

---

## 6. What we need from you

**1. Populate the eleven `Protocol Sections` fields — and never from the extractor.**
By hand, or from the trusted signed proposal. It is the one part of pre-filling we cannot do ourselves.

To be straight with you about the rest of it: **the import path is built and the operator screen is not.**
Populated sections are now read into LabOS, validated, and used to pre-fill a job — verified against this
base end to end. What is missing is the screen an operator drives it from, so until that lands, populating
these fields makes the path useful to us and not yet visible to them.

**2. Confirm your `Protocol Sections` automation still owns `Result`, `Status` and `Testing Date`.**
LabOS never writes them. We cannot see your automations — the Meta API returns `403` for them — so this
needs your eyes, not ours.

**3. Confirm no unfiltered "when record updated" trigger is disturbed by eighteen new fields.**
Every change was additive, which rules out the usual breakages, but an unfiltered trigger will now fire more
often than before.

**4. Tell us what six fields on `Protocol Sections` are for — they are named for LabOS and we have never
written them.** `Latest LabOS Attempt Number`, `LabOS Attempt ID`, `LabOS Retest Required`,
`LabOS Report Link`, `Excel File Link` and `Notes` are present and **writable** in both bases. They are not
rollups or lookups, and nothing in our field register accounts for any of them, so the read/write boundary
this document describes has a hole in it that neither side has looked at.

We are not going to start writing them on a guess: a section-level summary beside the per-attempt rows is a
different ownership model from the one §1 sets out. Three possibilities and we cannot tell which — legacy
from an earlier design, maintained by hand today, or waiting on us.

One of them changes meaning because of this release: with one attempt per impact, whatever writes
`Latest LabOS Attempt Number` will read *5* for a five-impact test. If that field is live in a view or an
automation, that is worth knowing before the first five-impact job lands.

**And one that is yours, not ours:** the extractor defect is unresolved on your side. It no longer affects
LabOS, because we read the typed fields instead — but it still affects **your** data, and a shifted value has
already reached a record marked Passed. A blast-radius review of jobs already marked tested is a quality
decision for IFET rather than an engineering one.

---

## 7. Three different kinds of statement in this document — which is which

An earlier draft of this document mixed these together, and one sentence claimed as *implemented* something
that was only *specified*. So the three are separated here explicitly, and every claim above belongs to
exactly one of them.

### ✅ Verified — read back from the live bases, today

- **The schema.** 160 fields in Testing, 142 in production, 18 added, all correctly typed, all select
  options as listed. Every one of the 142 pre-existing fields has the same type after as before; nothing was
  renamed, retyped, deleted or reordered, and no table, view, relationship or automation was touched.
- **Production is untouched**, checked against the live base rather than assumed, with tooling that refuses
  the production base unconditionally.
- **The before/after chain joins** — the first change's *after* snapshot is byte-identical to the second's
  *before*, so the three snapshots are one history.
- **A requirement expressed in these fields is sufficient to drive a test programme** — an asymmetric 60/45
  pair derived all fourteen stages, and the pass/fail types carried a class with no numeric value.
- **The attached CSVs agree with both live bases**, all 160 rows, 0 disagreements.

### 🔧 Implemented in LabOS — and demonstrated end to end against the Testing base

Written earlier on 2026-09-08 and **revised the same evening**, because most of
what this section listed as remaining work now runs. It is revised rather than
quietly reworded: a document that understates progress is safer than one that
overstates it, but it is still inaccurate, and you are being asked to replicate
this schema on the strength of what we say about it.

- **All five test types** — local storage, numbered impacts each with their own
  photographs, and the review step.
- **Identity.** One attempt ID per attempt, one test ID shared across a group,
  the four Airtable IDs resolved from the parent records for **every** type.
  Attempt numbers are unique within a test at the database level, so two
  simultaneous starts cannot produce two records for one physical test.
- **The outbound envelope and queue** — which field belongs to which phase, the
  refusal of anything not permitted for that phase, ordering, and recovery from
  an outage or a restart.
- **Reading your requirements.** The eleven `Protocol Sections` fields are
  mirrored locally and drive a LabOS job: the design-pressure pair derives all
  fourteen stages, the gauge and impact counts pre-fill, and each test is linked
  to the Protocol Section that specifies it.
- **The kind/unit validator.** A section whose `Required Unit` contradicts its
  `Requirement Kind` is refused rather than assumed — the §0.2 promise, now a
  check. Blank is never read as zero, and blank `Applicability` is never read as
  Not Required.
- **Photographs.** Downscaled previews uploaded directly, with the attachment ID
  you return recorded so a retry after a lost response reconciles against your
  record instead of attaching the same file twice.
- **A requirement is frozen when a test starts**, so editing a section afterwards
  cannot change what a finished test reports having been run against.

**Verified against this base, not asserted:** every phase of every one of the
five types published, one Airtable row per attempt, retries merging onto the same
row, a retest creating a separate row that keeps its `LabOS Test ID`, and
photographs arriving on the records. Also verified from your side of the
boundary: an unknown select option is rejected rather than created, an empty
string is refused where a number or a date belongs, and a genuine `0` stores as
`0`.

Probe rows from those runs are tagged `Operator Name = LABOS-PROBE`, with
`LabOS Test ID` values beginning `probe`. **LabOS never deletes**, so clearing
them is the one piece of housekeeping we cannot do ourselves.

### ⬜ Specified but not yet built — our remaining work, stated so you can hold us to it

- **The operator interface.** Everything above is reachable through the API and
  none of it has screens yet. This is now the largest remaining piece of our
  work, and it is the one you would notice.
- **The correction route.** `Corrects Attempt ID` still cannot be populated, so
  today **every** new attempt is a retest. This is the strongest reason to keep
  that field: the day corrections exist, a roll-up that cannot tell them from
  retests would be wrong and would look right.
- **`Max Pressure Achieved`** — actual pressure is on the rig's telemetry bus and
  renders live in our UI; nothing subscribes to it and stores the maximum. §4.
- **`Impact Velocity` is read but not yet shown to the operator.** An earlier
  draft of this document told you our mapping pointed it at a *measured*
  per-impact value. **That was wrong about our own code** and is corrected here:
  nothing points it there. It is copied into our local mirror and frozen onto
  the attempt, so it travels in the JSON — it simply does not appear on the
  screen the operator is looking at. Nothing wrong has been published; we do not
  send an achieved velocity. Whether the target should be on that screen is a
  question for our project owner, not a schema change on your side.
- **Deflection** remains uncalibrated; §4.

**None of these change what this document asks of you**, which is a schema change
and its reasoning. They are listed because a schema you are asked to replicate
into production should come with an honest account of what does and does not yet
run against it.

### And three things that can only be verified at cutover, by both of us

- that your existing automations behave correctly against the new fields **in production**;
- that roll-ups exclude superseded results and do not count corrections as extra physical tests;
- that upsert-on-`LabOS Attempt ID` behaves as expected against real records at volume.

These need the production base and a scheduled window. **This document is a schema change and its reasoning;
it is not a claim that the integration is delivered.** Nothing is deployed.

---

## Attachments

| File | What it is |
|---|---|
| `evidence/testing-base-changes-2026-09-06/production-change-spec.csv` | **The working sheet.** One row per field for all 160: `ADD`/`KEEP`, reads, writes, why. Regenerated 2026-09-08 — it carries all 160, not the 156 of the folder it sits in |
| `evidence/testing-base-before-after-2026-09-08.csv` | **Before and after, as a spreadsheet.** All 160 fields: unchanged or added, the type either side, the field ID, and which of the three dates it was added on. **142 unchanged · 18 added · 0 removed · 0 retyped.** Generated, and it refuses to run if the three changes do not chain |
| `evidence/testing-base-changes-2026-09-06/` | The first 14 fields — before/after schema, field IDs, per-field reasons |
| `evidence/testing-base-changes-2026-09-08/` | The three Impact fields — same, plus the fixture verification |
| `contract/interface-schema.csv` | Every field in both bases joined to its LabOS use, including the 104 ignored |
| `contract/write-contract-v0.4.md` | What each field means and when LabOS writes it |

Questions to Abdelrahman. If any field above looks wrong for how you use the base, it is much cheaper to say
so now than after production is changed.
