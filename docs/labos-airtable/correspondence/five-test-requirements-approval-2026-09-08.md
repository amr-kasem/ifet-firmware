# LabOS — what each of the five tests requires, and what it produces

**For approval by the project owner. Draft, not sent.** Every number and field name in this
document is generated from the LabOS source — the stage factors are read out of the calculators
that multiply them, the routing out of the importer that routes on it. It cannot describe a field
we do not have.

**Why you are being asked now.** The three new tests are built and the UI developer's next piece
of work is the screens for them. This is the last point at which a correction is a database change
rather than a database change plus a UI rewrite plus a migration against live rows. The Airtable
change document is written, verified against both live bases, and **held until you have approved
this**.

---

## What you are approving

The five test types LabOS runs — the `Test Type` option set, verbatim: **Static Load** · **Cycles** · **Impact** · **Forced Entry** · **ANSI Z97.1**.

| Test | What the proposal must supply | What LabOS produces |
|---|---|---|
| **Static Load** | one inward/outward design-pressure pair (PSF) | 6 stages, 30 s hold each, deflection readings per gauge |
| **Cycles** | the same pair — nothing further | 8 stages, 9,000 cycles in total |
| **Impact** | how many impacts — the classification is chosen in LabOS | one attempt per impact — each with its own pass/fail, photographs and verdict |
| **Forced Entry** | the grade to judge against — no numbers | one pass/fail verdict per attempt, with notes and photographs |
| **ANSI Z97.1** | the class to judge against — no numbers | one pass/fail verdict per attempt, with notes and photographs |

**What you are approving:** that this is the right set of information to require, to record and to
send back — per test. Not the screens, not the schedule, and not the Airtable team's own fields.

**What you are not approving:** anything that changes a production rig. None of the three new
tests touch rig hardware, there is no firmware change in this work, and nothing is deployed.

**Six answers are needed rather than a general yes** — **one still open** — listed after the five
pages, and each is a place where we made a call you may not want.

Approved by: ______________________________   Date: ______________

---

## Nothing the proposal already says is retyped

> *"The operator should not have to manually recreate information that already exists in HubSpot or
> Airtable."*

This is the principle these pages are built on, so it is worth stating what it amounts to in fields
rather than in intent. **Every row marked *from the proposal* on the five pages that follow is a field
the operator never types.**

**15 fields are read from Airtable and pre-filled today**, out of 17 the
integration reads in total — and that total is the whole of it. The read boundary is a list in the
code, not a convention: a field not on the list is not copied, which is also how the commercial
fields stay out.

| Where it applies | Pre-filled from Airtable |
|---|---|
| Every test — the job, specimen, protocol and requirement identity | `IFET job number` · `Project name` · `Mock-up/specimen name` · `Protocol Name` · `Section Name` · `Requirement Code` · `Applicability` · `Requirement Kind` · `Required Unit` |
| Static Load | `Required Value Inward` · `Required Value Outward` |
| Cycles | `Required Value Inward/Outward` |
| Impact | `Required Value` |
| Forced Entry | `Required Option` |
| ANSI Z97.1 | `Required Option` |
| How many deflection gauges *(a parameter, not a test)* | `Required Value` *(gap unreconciled)* |
| Water infiltration *(deferred — see the appendix)* | `Required Value` *(out of scope)* |

The three carrying a note are read but not yet fully acted on: the target impact velocity does not
reach the operator (question 3), the gauge count is not reconciled against what the rig takes at
start, and water infiltration is out of scope for this release. **None of them is a field anybody
retypes** — they are read; what is incomplete is what we do with them afterwards.

The design-pressure pair is the one worth pointing at twice: **two numbers pre-filled become fourteen
test stages**, none of which anybody types or checks.

**What the operator does still enter is not information that already exists** — it is what the test
produced: the outcomes, the measurements, the notes, the photographs, the verdict, and which rig ran
it. None of that is in Airtable to be recreated.

**On HubSpot specifically.** LabOS does not read HubSpot and does not need to. Contract §1 sets the
boundary — *HubSpot supplies approved commercial scope; Airtable owns the assigned
project/specimen/protocol hierarchy* — and HubSpot's own identity already arrives in Airtable on
`IFET Projects` as `Hubspot Deal ID` and `Hubspot Deal Stage`. So anything from HubSpot that an
operator would otherwise retype reaches us through Airtable, and what does not reach us is commercial
data a rig has no use for. **If you expect LabOS to read HubSpot directly, that is a new scope item
and not a gap in this document** — say so and it gets planned rather than assumed.

---

## Static Load

*Requirement code `STATIC_PRESSURE` · read as Directional Pair, unit PSF · becomes `static` work in LabOS*

Hold a pressure against the specimen and measure how far it deflects, in both directions, at three multiples of the design pressure.

### What the proposal must supply

| Requirement | Airtable field | Where it lands in LabOS |
|---|---|---|
| Design pressure pair | `Required Value Inward` | `projects.inward_design_pressure` |
| Design pressure pair | `Required Value Outward` | `projects.outward_design_pressure` |

A requirement LabOS cannot read unambiguously is **refused and reported to the operator with
the reason**, never guessed at. A blank is never read as zero, and a unit that disagrees with
the requirement is treated as a different test rather than a typo.

### What LabOS works out for itself

**You supply one pair of numbers and LabOS produces all six stages.** The proposal's inward and outward design pressures are the only input; every stage is that pair times a fixed factor, alternating direction. Nothing about the sequence comes from Airtable, which is the single biggest difference from the flow as it was described to us.

The six stages, as factors of the pair — and worked through for a 60 / 45 PSF pair:

| Stage | Direction | Factor | 60 / 45 gives | Hold |
|---|---|---|---|---|
| 1 | inward | ×0.75 | 45.0 PSF | 30 s |
| 2 | outward | ×0.75 | 33.75 PSF | 30 s |
| 3 | inward | ×1 | 60 PSF | 30 s |
| 4 | outward | ×1 | 45 PSF | 30 s |
| 5 | inward | ×1.5 | 90.0 PSF | 30 s |
| 6 | outward | ×1.5 | 67.5 PSF | 30 s |

### What is recorded, and what reaches Airtable

| What | Kept in LabOS as | Sent to Airtable as | When |
|---|---|---|---|
| Permanent set and recovery | `deflections.permanent_deflection / .recovery` | **not sent yet** — see below | — |
| What was measured | — *(nothing holds it)* | **not sent yet** — see below | — |
| Peak pressure reached | — *(nothing holds it)* | **not sent yet** — see below | — |
| Deflection | `deflections.max_deflection` | **not sent yet** — see below | — |
| Deflection unit | — *(nothing holds it)* | **not sent yet** — see below | — |

**Everything specific to this test is currently withheld** — the reasons are below. What
does reach Airtable for it is on the last page: the attempt, its verdict, who ran it, the
photographs and the full JSON. The test is published; its measurements are not.

### What we cannot do yet, and why

**Deflection readings are not published.** The rigs return raw counts from the gauges that were never calibrated to a physical unit, so a number in a field named for inches would be a number we cannot stand behind. It needs bench time, and it is hardware work.

**`Max Pressure Achieved` is not published either, for a different reason.** The actual pressure exists on the rig's telemetry and renders live in our UI; nothing subscribes to it and stores the maximum. That is software work on our side and it is scheduled. We would rather send nothing than send a number we cannot stand behind — but the two are not the same admission.

**`recovery` is a configured constant, not a measurement.** It is the settling time the rig waits, taken from config; it is not the specimen's observed recovery.

---

## Cycles

*Requirement code `CYCLIC_PRESSURE` · read as Directional Pair, unit PSF · becomes `cyclic` work in LabOS*

Cycle the pressure between a low and a high value for a fixed number of cycles, eight stages, four inward then four outward.

### What the proposal must supply

| Requirement | Airtable field | Where it lands in LabOS |
|---|---|---|
| Design pressure pair | `Required Value Inward/Outward` | `projects.inward_design_pressure + projects.outward_design_pressure` |

A requirement LabOS cannot read unambiguously is **refused and reported to the operator with
the reason**, never guessed at. A blank is never read as zero, and a unit that disagrees with
the requirement is treated as a different test rather than a typo.

### What LabOS works out for itself

**The same one pair of numbers produces all eight stages** — the high and low pressure of each, and how many cycles it runs. Together with Static Load that is fourteen stages from two numbers.

If a protocol's Static and Cycles sections ever disagree about the design pressures, LabOS refuses rather than picking one: all fourteen stages come from a single pair, so two pairs cannot both hold.

The eight stages — and worked through for the same 60 / 45 PSF pair:

| Stage | Direction | High | Low | Cycles | 60 / 45 gives (high) |
|---|---|---|---|---|---|
| 1 | inward | ×0.5 | ×0.2 | 3,500 | 30.0 PSF |
| 2 | inward | ×0.6 | ×0.0 | 300 | 36.0 PSF |
| 3 | inward | ×0.8 | ×0.5 | 600 | 48.0 PSF |
| 4 | inward | ×1.0 | ×0.3 | 100 | 60.0 PSF |
| 5 | outward | ×1.0 | ×0.3 | 50 | 45.0 PSF |
| 6 | outward | ×0.8 | ×0.5 | 1,050 | 36.0 PSF |
| 7 | outward | ×0.6 | ×0.0 | 50 | 27.0 PSF |
| 8 | outward | ×0.5 | ×0.2 | 3,350 | 22.5 PSF |

**9,000 cycles in total.**

### What is recorded, and what reaches Airtable

| What | Kept in LabOS as | Sent to Airtable as | When |
|---|---|---|---|
| Cycles required | `cyclic_tests.cycles` | *in the JSON response* | terminal |
| Cycles completed | `cyclic_tests.current_cycle` | *in the JSON response* | terminal |
| What was measured | — *(nothing holds it)* | **not sent yet** — see below | — |

This is what is specific to this test. Everything sent on *every* attempt — the verdict,
the times, the operator, the photographs, the full JSON — is on the last page.

### What we cannot do yet, and why

`Cycles Required` and `Cycles Completed` have no columns of their own in Airtable and travel in the JSON response instead. Cycles completed is captured at the moment the attempt terminates, because a reset or a second run overwrites the live counter.

---

## Impact

*Requirement code `IMPACT_LMI · IMPACT_SMI` · read as Count, unit cycles or impacts · becomes `impact` work in LabOS*

Fire a missile at the specimen a required number of times and record, for each impact, whether it passed.

### What the proposal must supply

| Requirement | Airtable field | Where it lands in LabOS |
|---|---|---|
| How many impacts | `Required Value` | `projects.impact_count` |

A requirement LabOS cannot read unambiguously is **refused and reported to the operator with
the reason**, never guessed at. A blank is never read as zero, and a unit that disagrees with
the requirement is treated as a different test rather than a typo.

### What LabOS works out for itself

**One test type, not two.** Large missile and small missile are the same procedure with a different missile, so the missile is a field on the test and not a separate kind of test.

**The impact classification is chosen in LabOS, not supplied by Airtable — your decision of 2026-09-10.** One value covers the missile, its weight and the target velocity: *SMI*, *LMI Level D* or *LMI Level E*. Airtable's requirement code already says whether a section is large missile or small, so that half is filled in for you and cannot be contradicted; the only thing anyone chooses is D or E, and only on a large-missile test. The classification is then sent back to Airtable with the result.

**The target velocity is entered in LabOS too**, and it is not worked out from the classification: we hold no table that says which velocity each one means, and inventing one would put a number in every impact record that nobody had checked.

**One attempt per impact — as you specified on 2026-09-08.** An impact test contains one or more attempts and each attempt is exactly one impact, with its own pass/fail, its own photographs and its own verdict. Impact 1, 2, 3 are three attempts, not one attempt holding three impacts, and none of them ever overwrites another.

There is no separate notion of re-doing impact 3: a specimen already struck cannot have that impact repeated, so a further firing is impact 6, which is simply the next attempt. A result recorded *wrongly* is a different thing and is superseded rather than overwritten — see the last page.

### What is recorded, and what reaches Airtable

| What | Kept in LabOS as | Sent to Airtable as | When |
|---|---|---|---|
| Missile, free text (history) | `missile_impact_tests.missile` | — *(stays in LabOS)* | n/a |
| Missile mass (history) | `missile_impact_tests.missile_weight` | — *(stays in LabOS)* | n/a |
| Per-impact observations | `shots.area/velocity/note` | *in the JSON response* | terminal |
| Impact classification | `missile_impact_tests.impact_family + impact_level` | `Impact Classification` | terminal |
| Target impact velocity | `missile_impact_tests.target_velocity` | `Target Impact Velocity` | terminal |
| Each impact is its own attempt row | `test_results.trial_number` | `Impact Number` | create |
| Outcome of that one impact | `test_results.test_result` | `Impact Result` | terminal |
| Per-impact photographs | `test_photos.shot_id set` | `LabOS Photos` | attachment |

This is what is specific to this test. Everything sent on *every* attempt — the verdict,
the times, the operator, the photographs, the full JSON — is on the last page.

### What we cannot do yet, and why

**The new shape is built, and not yet deployed.** Everything above is your 2026-09-08 instruction, implemented the same day: an attempt refuses a second impact, a completed attempt must have exactly one, and the attempt's own outcome is taken from its impact. `Impact Number` was added to the Airtable schema and is published for Impact only, so a roll-up on their side can count *tests* and *impacts* separately — without it a five-impact test would read as five tests, and read plausibly.

**What is not done is the deployment.** The database migration that splits the impacts already recorded — 39 tests and 114 impacts on the live system — is written and rehearsed forward and back against a copy, and has not been run on the real database. Nothing in this integration is deployed yet.

**Five impacts become five rows in the Airtable base**, each with its own verdict and photographs, where today they are one row with a summary line. This follows directly from attempts being the unit we publish.

**The target impact velocity is entered in LabOS, not read from the proposal.** Answer 3 was *"we will be entering it"*, and the remark above the numbered answers says why that is enough: the target follows from the classification — SMI has one, LMI is Level D or E — so the operator choosing the classification is already stating the target. It is published outbound as `Target Impact Velocity` and nothing derives it.

**Impact location has no Airtable field, deliberately.** LabOS records where each impact landed; we did not create a field for it on their side, because location is an observation per impact and not a requirement. **Confirmed 2026-09-10** — answer 4: the physical locations are in the test plans and appear in neither system.

---

## Forced Entry

*Requirement code `FORCED_ENTRY` · read as Not Applicable, no unit · becomes `manual:Forced Entry` work in LabOS*

Attempt entry against the specimen and record pass or fail against a named grade, with notes and photographs.

### What the proposal must supply

| Requirement | Airtable field | Where it lands in LabOS |
|---|---|---|
| Grade judged against | `Required Option` | `manual_tests.required_option` |

A requirement LabOS cannot read unambiguously is **refused and reported to the operator with
the reason**, never guessed at. A blank is never read as zero, and a unit that disagrees with
the requirement is treated as a different test rather than a typo.

### What LabOS works out for itself

**No numeric requirement at all.** The proposal supplies the grade — *ASTM F588 Grade 40* — and nothing else; the verdict is the operator's. A grade LabOS does not recognise is displayed and the test stays non-executable rather than being guessed at.

This test does not touch the rig hardware.

### What is recorded, and what reaches Airtable

| What | Kept in LabOS as | Sent to Airtable as | When |
|---|---|---|---|
| Pass or fail | `test_results.result + .test_result` | `Test Result` | terminal+verdict |
| Failure detail | `test_results.note` | `Notes + JSON` | terminal |

This is what is specific to this test. Everything sent on *every* attempt — the verdict,
the times, the operator, the photographs, the full JSON — is on the last page.

### What we cannot do yet, and why

**Nothing outstanding.** A dedicated `Forced Entry Result` column was added on 2026-09-11, after answer 2 — *"they are different under different standards"*. It carries the same verdict as `Test Result`, gated to this test type and blank on the other four, so a report about Forced Entry alone no longer has to filter `Test Result` by `Test Type` first. `Test Result` is unchanged and still carries the lifecycle for all five types.

---

## ANSI Z97.1

*Requirement code `ANSI_IMPACT` · read as Not Applicable, no unit · becomes `manual:ANSI Z97.1` work in LabOS*

The bag-drop safety-glazing test: pass or fail against a named class, with notes and photographs.

### What the proposal must supply

| Requirement | Airtable field | Where it lands in LabOS |
|---|---|---|
| Class judged against | `Required Option` | `manual_tests.required_option` |

A requirement LabOS cannot read unambiguously is **refused and reported to the operator with
the reason**, never guessed at. A blank is never read as zero, and a unit that disagrees with
the requirement is treated as a different test rather than a typo.

### What LabOS works out for itself

**This is not the missile impact test.** It is a different procedure with a different apparatus, and it is kept as its own requirement code for exactly that reason — a reader who assumed "impact" meant one thing would route it to the wrong test.

The proposal supplies the class — *Class A* — and nothing else. No rig hardware is involved.

### What is recorded, and what reaches Airtable

| What | Kept in LabOS as | Sent to Airtable as | When |
|---|---|---|---|
| Pass or fail | `test_results.result + .test_result` | `Test Result` | terminal+verdict |

This is what is specific to this test. Everything sent on *every* attempt — the verdict,
the times, the operator, the photographs, the full JSON — is on the last page.

### What we cannot do yet, and why

**ANSI Z97.1 is normally performed first on a specimen, and LabOS does not enforce that.** The expectation is recorded; the other tests are not blocked if it has not been done. A hard block would eventually stop legitimate work and there is no override in this design. **Approved 2026-09-10 — answer 1 was YES**, so this is a statement of an agreed design rather than an open question.

As with Forced Entry, a dedicated `ANSI Result` column was added on 2026-09-11 after answer 2, alongside `Test Result` rather than instead of it.

---

## The same for every test

None of this is per-test, and none of it is anything you have to supply — it is what LabOS
records around every attempt so that a result can be traced back to the requirement that asked
for it, and to the person who ran it.

### What identifies the work

| What | Read from Airtable as |
|---|---|
| Which job is this | `IFET job number` |
| Which job is this | `Project name` |
| Which specimen | `Mock-up/specimen name` |
| Which protocol | `Protocol Name` |
| Which section | `Section Name` |
| What test is required | `Requirement Code` |
| Is it required at all | `Applicability` |
| How to read the value | `Requirement Kind` |
| Unit of the requirement | `Required Unit` |

**Routing is by record id, never by name.** A renamed job or section still points at the same
work, and a job number typed twice cannot silently re-point one job's results at another.

### What LabOS sends back on every attempt

| What | Sent as | When |
|---|---|---|
| Airtable record linkage | `Airtable Project ID` | create |
| Airtable record linkage | `Airtable Mockup ID` | create |
| Airtable record linkage | `Airtable Protocol ID` | create |
| Airtable record linkage | `Airtable Section ID` | create |
| Group attempts of one test | `LabOS Test ID` | create |
| Merge key | `LabOS Attempt ID` | create |
| Which attempt | `Attempt Number` | create |
| Which workflow | `Test Type` | create |
| Execution state | `Test Status` | create+terminal |
| Verdict placeholder | `Test Result` | create+terminal+verdict |
| Who ran it | `Operator Name` | create |
| When it started | `Testing Start Date` | create |
| When it ended | `Testing End Date` | terminal |
| Completion instant | `Test Date` | terminal |
| Operator disposition | `Testing Continued` | terminal |
| Who reviewed | `LabOS Verdict By` | verdict |
| When reviewed | `LabOS Verdict At` | verdict |
| Retest needed | `Retest Required` | verdict |
| Supersedes which attempt | `Corrects Attempt ID` | create |
| Why superseded | `Correction Reason` | create |
| Evidence | `LabOS Photos` | attachment |
| Full detail | `Complete LabOS JSON Response` | create+terminal+verdict |
| Revision time | `LabOS Updated At` | create+terminal+verdict |
| Which rig ran it | *in the JSON response* | create |
| Software version | *in the JSON response* | create |
| Requirement snapshot | *in the JSON response* | create |
| Why aborted | *in the JSON response* | terminal |
| Review rationale | *in the JSON response* | verdict |

*When* is the moment the value is written: **create** when the attempt starts, **terminal** when
it finishes or is aborted, **verdict** when a reviewer first judges it, **attachment** when a
photograph settles. A value is never sent blank — an absent value is left out of the write
entirely, so an empty cell in Airtable never has to be read as a decision.

**Two rows say "not built yet".** Corrections — superseding an attempt rather than editing it —
are designed and specified but have no route yet: the columns exist in Airtable and LabOS has the
fields, and what is missing is the operator path that creates a correction. Until then a
correction cannot be recorded as one.

---

## The six answers we need

**1. ANSI ordering is recorded but not enforced.** ANSI Z97.1 is normally first on a specimen. LabOS records that and does not block the others. Is informational-only correct, or do you want it enforced — knowing a hard block has no override and will eventually stop legitimate work?

> **Answered 2026-09-10 — YES**, recommended first and not blocking. No schema, no code and no document change; the design is approved as it stands.

**2. Forced Entry and ANSI share one result column.** Both verdicts land in `Test Result`, with detail in `Notes` and the JSON, rather than in dedicated `Forced Entry Result` and `ANSI Result` columns. Is that enough, or does a named report need them separately?

> **Answered 2026-09-10 — NO**: *"they are different under different standards"*. Both dedicated columns were built and applied to the Testing Base on 2026-09-11, **in addition to `Test Result`, not instead of it** — the shared column still carries create, terminal and verdict for all five types. `Failure Notes` was not added: he named two fields and we do not add a third on inference.

**3. The target impact velocity is never shown to the operator.** It is read from the proposal and frozen onto the attempt, so it is in the record, but it is not on the screen at the rig. Does the operator need to see it?

> **Answered 2026-09-10 — *"we will be entering it"***. It reverses direction: the target is no longer read from the proposal at all, it is LabOS-owned and operator-entered, and it is published outbound as `Target Impact Velocity`. Nothing is pushed at the operator because the classification they pick already determines it.

**4. Impact location stays a LabOS-side observation.** LabOS records where each impact landed; Airtable has no field for it, because location is an observation and not a requirement — and an unwanted field in a shared base is much harder to remove than to add. Confirm that is right.

> **Confirmed 2026-09-10** — *"the physical Locations … will not be shown on LabOS or Airtable, that is in the test plans"*. No Airtable field, and the per-impact `shots.area` observation stays LabOS-side evidence in the JSON.

**5. `Static / Type` is read and then changes nothing.** The proposal's static programme value — *Full* — is read and validated, but LabOS derives the same six-stage programme regardless. If a proposal ever specified a different programme, LabOS would run the full one without saying so. Is *Full* the only static programme in practice? If not, we should make LabOS refuse the others out loud rather than ignore them. **Still open — this one was never actually asked**: it was in the unsent follow-up of 2026-09-08 and is re-asked in the 2026-09-10 reply. LabOS no longer ignores an unsupported programme in the meantime — it refuses to run rather than silently substituting *Full*, so an unanswered question cannot become a wrong test.

**6. A five-impact test will appear as five records in the Airtable base.** This follows from one attempt per impact: attempts are what we publish, so five impacts are five rows, each with its own verdict and photographs, where today they are one row with a summary line. It changes what the Airtable team's views, groupings and automations see, and it needs one field added on their side — `Impact Number` — so a roll-up can count five impacts of one test rather than five tests. Confirm that is what you intend, because it is the half of the instruction that lands on somebody else's base.

> **Confirmed 2026-09-08.** So `Impact Number` is being added to the Airtable schema, and the Airtable team is told before the change goes to their production base.

---

## Appendix — five tests, nine requirement codes

The proposals carry nine requirement codes and LabOS runs five tests. The difference is not an
omission:

| Code | Kind | What LabOS does with it |
|---|---|---|
| `ANSI_IMPACT` | Not Applicable | Runs as **ANSI Z97.1** |
| `CYCLIC_PRESSURE` | Directional Pair | Runs as **Cycles** |
| `FORCED_ENTRY` | Not Applicable | Runs as **Forced Entry** |
| `GAUGE_COUNT` | Count | **A parameter, not a test.** How many deflection gauges the setup uses. Stored on the project; produces no test of its own |
| `IMPACT_LMI` | Count | Runs as **Impact** |
| `IMPACT_SMI` | Count | Runs as **Impact** |
| `STATIC_PRESSURE` | Directional Pair | Runs as **Static Load** |
| `STATIC_PROGRAMME` | Enum | **A parameter, not a test.** Which static programme the proposal names, e.g. *Full*. Read and validated, and currently changes nothing — see question 5 |
| `WATER_PRESSURE` | Magnitude | **Deferred.** Water infiltration is out of scope for this release. Known to LabOS so a section carrying it is reported as non-executable, rather than hitting the unknown-code refusal |

**Routing is by code, never by section name.** Renaming a section in Airtable can therefore never
silently change which procedure gets run, and a code LabOS does not know stays visible but cannot
start a test.

---

*Generated from the LabOS source by `app/airtable/test_requirements_doc.py`. Regenerate rather
than edit: `check_register.py` fails when this document and the code have parted company.*
