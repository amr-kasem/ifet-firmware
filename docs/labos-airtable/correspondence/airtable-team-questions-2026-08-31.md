# Airtable team's three questions — answer, and the agenda for tonight

**Author:** Abdelrahman · **Date:** 2026-08-31 · **Epic:** IFET-32 · **Status:** answer drafted, meeting tonight
**Trigger:** the Airtable team's reply to the 2026-08-28 verification report
(`correspondence/sent/2026-08-28-labos-airtable-live-base-verification-report.docx`).

> **What this document is.** The authoritative *wording* of our answer to their three questions, plus the
> agenda for tonight's call. Item **statuses** stay owned by contract §10 — this document is a view of it.
> The read-side field spec in §2 is a **proposal**, not yet agreed; when they accept it, it graduates into
> contract §9 and §10.3 / §10.15 / §10.23 close together.

---

## 0. The big picture in six lines

- **The five-day blocker cleared on 2026-08-28, and they replied within one working day.** Their response
  time has never been the problem; ours was.
- **The answer is argued from real columns, not from the contract.** Every field we ask for already exists as
  a typed column in LabOS with real data in it — evidence: `../evidence/labos-real-data-types-2026-08-31.md`.
- **Their message is better news than it looks.** Q1 hands us the read-side specification to write — the item
  that has been the critical path since 2026-07-23 (§10.3). They are asking us to define it.
- **Two of their three points we accept outright** (retest row model, `Test Date` → dateTime). Each closes an
  open item: §10.20 fully, §10.13 partially.
- **One point we have to push back on**, with the reason on the record: replacing `Corrects Attempt ID` with
  a shared `LabOS Test ID` does not carry the same information (§10.14). We already send the shared Test ID.
- **Their message does not touch the two P0 items** — the extraction shift (§10.19) and the missing
  `Test Type` options (§10.17). Tonight's job is to not let the schema conversation absorb them.
- **Q1's ask shrank.** LabOS derives 14+ test stages from the design-pressure pair, so Airtable needs to model
  no ranges, no cycle sequences, no hold times — just two numbers in PSF. And `60 × 0.15 = 9` proves the
  extraction shift from arithmetic alone.
- **Nothing on our side is waiting on them except the one test write.** 132 tests green, stage-3 script
  dry-run verified, deploy runbook written. The build continues regardless (roadmap R1–R3).

---

## 1. Their message, verbatim

> **@Mariam**
> A few quick clarifications before we finalize the schema:
>
> 1. **Protocol Sections:** Please confirm how you want Required Value represented in a machine-readable
>    format, considering values may contain positive/negative numbers, ranges, symbols, and special
>    characters. Also, please specify the unit required for each protocol section.
> 2. **Retests:** Each attempt will create a new record with a unique LabOS Attempt ID and updated Attempt
>    Number, while Project ID, Mock-Up ID, Test Protocol ID, and Protocol Section ID remain the same. Instead
>    of Corrects Attempt ID, we'll use the same LabOS Test ID for re-attempts. Please confirm this works for
>    you.
> 3. **Test Date:** We'll change Test Date to include date and time, using the format:
>    `2026-08-04T19:00:00.000Z`
>
> Please confirm these points so we can proceed. Thanks!

### How it maps onto contract §10

| Their point | Contract items it touches | Our position |
|---|---|---|
| **1** — `Required Value` machine-readable + units | **§10.3** (read structure, longest-open) · **§10.15** (`Required Value`/`Required Unit`) · **§10.23** (`+60/60`) · **§10.24** (unit vocabulary) | **Accept the invitation and specify.** §2 below is the spec. Four items close together. |
| **2** — retest = new row, shared Test ID replaces `Corrects Attempt ID` | **§10.14** (blocking) · §2 / §3.1 of the contract | **Row model: confirmed, it is already what we do.** The substitution: **decline, with the cost stated.** |
| **3** — `Test Date` becomes a dateTime with ms, UTC | **§10.20** (date vs dateTime) · **§10.13** (start/end collapse) · §10.8 (two-write lifecycle) | **Accept.** Closes §10.20. §10.13 survives it — one instant still cannot hold both ends. |

---

## 2. Answer to Q1 — the read-side specification

**Grounded in `../evidence/labos-real-data-types-2026-08-31.md`, not in this contract.** The first draft of
this answer argued from what we had *designed*. The stronger answer argues from what LabOS has *stored for
years*: every quantity in their question is already a typed column with real data in it. We are asking their
schema to match columns that exist, not to adopt our preferences.

Their framing is worth answering directly: *values may contain positive/negative numbers, ranges, symbols and
special characters.* That is true of the **display string**, and it is exactly why a single field cannot be the
machine-readable one. The principle:

> **Numbers go in number fields. Notation stays in `Value`. The shape is declared, never inferred from
> punctuation.**

`+60/60` is not a value with symbols in it — it is *two* values in proposal notation, and in LabOS it has
always been two columns: `projects.inward_design_pressure` and `projects.outward_design_pressure`, both
`Float`, both **`NOT NULL`**, both PSF. A specimen cannot exist in LabOS without both.

### 2.1 The ask is smaller than it looks — two numbers

**LabOS derives the entire preset test programme from that pair** (evidence §1): six static stages at
`× [0.75, 0.75, 1.0, 1.0, 1.5, 1.5]`, eight cyclic stages with their own low/high factors and cycle counts
`[3500, 300, 600, 100 | 50, 1050, 50, 3350]`, and the water stage at `× 0.15`. All of it recalculated whenever
a design pressure changes.

**Confirmed in production, to full float precision.** Every factor above reproduces the live maxima exactly
across 1127 rows — `395.00518092874876 × 1.5 = 592.5077713931231`, and so on for all ten stages
(evidence §6.2). So this is not "our code does this", it is what the lab's data *is*. *"Preset"* is the one
honest qualifier: operators can add ad-hoc stages, and 2 of 626 cyclic rows are hand-entered — but an
operator-authored stage has no Airtable requirement behind it either way.

**And the pair is genuinely two independent numbers in real jobs:** of 78 projects, **36 — 46% — have inward ≠
outward design pressure**, spanning 3 → 491 PSF (evidence §6.1). Collapsing `+60/60` into one value loses real
data in nearly half of all jobs, and the halves are not recoverable from each other.

So the read-side dependency is not "model our requirements". It is:

> **Give us the design-pressure pair as two numbers in PSF. We compute the rest.**

That deletes work from their side rather than adding it: **Airtable does not need to model ranges, sequences,
cycle counts or hold times at all.** We do not read them.

### 2.2 Fields requested on `Protocol Sections` (`tblqpvuJlSdkeS9PS`)

`Value` is **unchanged** and stays the human-facing display string. Once these exist, **LabOS never parses
`Value` again.**

| Field | Type | Populated when | Notes |
|---|---|---|---|
| `Requirement Kind` | single select | always | `Magnitude` · `Directional Pair` · `Count` · `Enum` · `Not Applicable`. Declares which fields below to read. |
| `Required Value` | number | `Magnitude`, `Count` | Signed. A genuine zero is `0`; absent is **blank**. |
| `Required Value Inward` | number | `Directional Pair` | Positive magnitude, PSF. `+60/60` → `60`. Maps to `projects.inward_design_pressure`. |
| `Required Value Outward` | number | `Directional Pair` | Positive magnitude, PSF. `+60/60` → `60`. Maps to `projects.outward_design_pressure`. |
| `Required Unit` | single select | any kind carrying a number | Vocabulary in §2.4. Blank for `Enum` / `Not Applicable`. |

Five fields, four of them numbers or selects. Nothing that exists today changes type or loses data. **Only the
`Directional Pair` case carries the blocking dependency** — the rest is hardening.

**Why `Requirement Kind` earns its place.** It is the field that makes the data self-describing. Without it,
LabOS infers the shape from `Section Name` — so the day someone adds or renames a section, our parser is
guessing again, silently. With it, a mismatch between the declared kind and what the fields hold is a *loud*
validation failure on our side before a rig moves.

**Ranges: withdrawn as a question.** Our earlier draft offered `Required Value Min` / `Max` if a real range
appeared. The evidence says no range is ever read — TAS-203's low/high pressures are computed from the pair, so
`Directional Pair` is the only multi-valued case that exists. One fewer thing for them to decide.

**Blanks must stay blank.** A requirement that does not apply must be an empty field, distinguishable from
`0`. `Water (PSF)` blank and `Water (PSF) = 0` are different statements, and one of them is a test.

### 2.3 If they would rather add one field than five

Equivalent for us, cheaper for them, worse for them downstream: a single long-text
`Required Testing Parameters (JSON)` per section, shape supplied by us —
`{"kind":"directional_pair","inward":60,"outward":60,"unit":"PSF"}`. We will build against either.

**The trade-off to state plainly:** JSON in a long-text field cannot be filtered, sorted, grouped or rolled up
in Airtable, and their own interface pages cannot show it. The five typed fields serve their side as well as
ours. **Recommend the typed fields; accept the JSON if they prefer.**

### 2.4 The unit answer — kind and unit per section

Their second half asks us to state the unit for each protocol section. Read as: *one unit per section record,
determined by the parameter the section represents.* The table below is keyed on the `Section Name` values
observed live on 2026-08-23.

> **Safe to build on.** These names come from the proposal's column **headers**, which the extraction defect
> (§10.19) does not disturb — it shifted the **values**, not the headers. So the mapping is sound even though
> the sample data is not.

| `Section Name` | `Requirement Kind` | `Required Unit` | Correct value, per the proposal PDF | LabOS destination |
|---|---|---|---|---|
| `LMI (impacts)` | `Count` | `impacts` | `9` | `missile_impact_tests` (large missile) |
| `SMI (impacts)` | `Count` | `impacts` | *(blank)* | `missile_impact_tests` (small missile) |
| `# Dials` | `Count` | *(none)* | `10` | `deflections.deflection_gauge` count |
| `Static / Type` | `Enum` | *(none)* | `Full` | test-programme selection |
| **`DP (+) (PSF)`** | **`Directional Pair`** | **`PSF`** | **inward `60`, outward `60`** | **`projects.inward/outward_design_pressure` — drives all 14+ derived stages** |
| `Water (PSF)` | `Magnitude` | `PSF` | `9` | `infiltration_tests.pressure` |
| `Forced Entry (*)` | `Enum` | *(none)* | *(blank)* | — |
| `Cyclic (PSF)` | `Directional Pair` | `PSF` | inward `60`, outward `60` | derived from the pair — nothing to read |
| `Impact` (ANSI Z97.1) | `Enum` | *(none)* | *(blank)* | — |

**Unit vocabulary — three lists, scoped to where each is used.** A single global list was our earlier answer
and it was wrong in both directions: it missed five units the lab actually measures in, and carried two
(`lbf`, `N`) that nothing in the model produces. Evidence §3.

| Field | Option set |
|---|---|
| `Required Unit` (Protocol Sections) | `PSF` · `in` · `s` · `cycles` · `impacts` |
| `Unit` (raw table, `Measured Value`) | `PSF` · `PSI` · `in` · `mm` · `cycles` · `s` · `impacts` |
| `Deflection Unit` | `in` · `mm` |

Stored value is the short form. Display (`Inches`, `pounds per square foot`) belongs to the interface, not the
column. **`kg`, `m/s`, `m²` and `cfm/ft²` deliberately get no column** — they belong to impact and
infiltration detail, which §5.1 already routes into `Complete LabOS JSON Response` with the unit declared per
value. Worth telling them that air leakage (`cfm/ft²`) is the one candidate for a first-class field later.

**This closes §10.24:** `in`, not `Inches`, and **as a single select**. Their own sample row
`recxZWiVa5Wuy0ZV6` writes `Deflection Unit = "Inches"` where this vocabulary says `in`, and because both
fields are live as free text nothing errors — the column just quietly holds two spellings of one unit. A single
select converts silent divergence into a loud rejection.

> **Our own contract needs correcting too:** §4.4's list adds `impacts` and drops `lbf` / `N` on ratification.
> Leaving units in the vocabulary that nothing produces is a claim we cannot back with data.

### 2.5 Two things to say out loud while we are here

**The shift is now provable from arithmetic alone.** LabOS computes its water stage as
**`inward DP × 0.15`**, and `60 × 0.15 = 9`. So the `9` sitting in Airtable's `DP (+)` column is identifiable
as the **water** requirement — 15% of the real design pressure, exactly as this lab's own formula produces it.
Two independent methods now confirm the same diagnosis: glyph-coordinate extraction from the PDF, and the
internal consistency of the numbers themselves. It also explains why the wrong value looked so plausible: it
is not noise, it is a real requirement from the same row.

**It also sharpens the severity, and this is the sentence for the call:** a rig driven from `DP = 9` would run
the *structural* test at the *water* pressure. And because fourteen stages are derived from the pair, a wrong
pair is multiplied through every one of them.

**Typed fields help, but do not fix this.** A `Directional Pair` section arriving as a single number is a
structural mismatch we can reject. A wrong number in the right shape still passes every check we can write.
Second line of defence, **not** a replacement for the column-positional extractor fix.

---

## 3. Answer to Q2 — retests

### 3.1 The row model: confirmed

*"Each attempt creates a new record with a unique `LabOS Attempt ID` and an updated `Attempt Number`, while
Project / Mock-Up / Protocol / Section IDs stay the same."*

**That is exactly contract §2 and §3.** No change on either side. And the shared `LabOS Test ID` they propose
is already in every payload we send — §2 defines it as the field that groups attempts of one test instance.
So there is nothing to negotiate there: it is confirmed, and it is not new.

### 3.2 The substitution: we have to decline, and here is the reason

The shared `LabOS Test ID` is not an alternative to `Corrects Attempt ID`. It answers a **different question**.

| Question | Answered by |
|---|---|
| Which attempts belong to the same test? | `LabOS Test ID` — shared. **Already sent.** |
| Is attempt 2 a second real test, or a fix to a mis-recorded attempt 1? | **Nothing, without `Corrects Attempt ID`.** |

Both cases produce the identical row shape their Q2 describes: same four Airtable IDs, same `LabOS Test ID`,
new `LabOS Attempt ID`, `Attempt Number` 2. The physical reality behind them is opposite:

| | **Retest** | **Correction** |
|---|---|---|
| What happened | The specimen **was tested twice**. Two real events. | **One** event, recorded wrongly. |
| Rows in Airtable | 2 rows, **both valid data** | 2 rows, **only the second is true** |
| A correct roll-up must | count both attempts | count **one** — and exclude row 1 |

**The consequence, stated for their side of the boundary.** Any automation that counts attempts, computes a
pass rate, or reports "tests performed" is wrong in one of the two cases — and it will look right. That is the
expensive kind of wrong: it does not fail, it reports.

**The real worked example from this project** (contract §3.1): on 2026-07-09 a rig's pressure sensors were
found to be logging PSI as PSF. A reading already written as `40 PSF` was actually `5760 PSF`. Editing the row
destroys the evidence a report has already cited; a bare new row leaves two contradictory `Passed` results with
no explanation. The only complete answer is a new row that **states what it supersedes** — which is a field, on
the row, that their automation can branch on.

**Also worth saying out loud:** we cannot mark the old row ourselves. It is terminal and locked to us by
contract §3. We can only write a new row declaring what it corrects; marking the old one `Superseded` is
theirs. That split is deliberate — the writer of a record never gets to retroactively alter one — and it is
precisely why the reference has to be a real column rather than something buried in our JSON.

### 3.3 The ask, and two fallbacks — in order of preference

> **Worth saying, because it changes how the ask sounds.** `corrects_attempt_id` is not a hypothetical field
> we would like. It is a `String` column, indexed, with `correction_reason` as `Text` beside it, **built,
> migrated and tested on our integration branch** — and written by our envelope today. What is missing is a
> destination for it.
>
> ⚠️ **Say "built and tested", not "already migrated".** The live production database is still at
> `alembic_version = 3a65a83e0463` and `test_results` has five columns; none of the P1 attempt columns are
> deployed (evidence §7.1). Both statements are true of the branch; only the careful one is true of
> production.
>
> **And the ambiguity is already real, not prospective:** across 507 real tests, **106 — one in five — already
> have more than one attempt**, and some have three (evidence §6.3). Today nothing in that data distinguishes a
> retest from a correction.

1. **Preferred — two fields on `LabOS Raw Data Table`:** `Corrects Attempt ID` (**plain text**, not a
   computed field, not a link) and `Correction Reason` (long text). Blank on every retest; populated only on a
   correction. A correction of a correction references *its* predecessor, so the authoritative result is the
   row no other row supersedes.
2. **If they will not add a field — one formula field.** We already carry `corrects_attempt_id` inside
   `Complete LabOS JSON Response`. A single Airtable formula field (`REGEX_EXTRACT` over that text) surfaces it
   as something filterable, with no workflow change and no new LabOS work. **Honest caveat:** it is brittle to
   the JSON shape, which is itself unagreed (§10.25) — so this fallback depends on closing that item too.
3. **If neither** — then we record in the contract, and report to IFET, that attempt counts and pass rates
   derived from the raw table are **not trustworthy**, and that the distinction lives only in LabOS. That is a
   defensible decision for them to take with the cost visible; it is not defensible for us to leave implicit.

---

## 4. Answer to Q3 — `Test Date`

**Accepted, and it closes §10.20.** A date-only field could not express a time at all; `dateTime` in UTC with
milliseconds is what we already produce internally. We will send exactly their format
(`2026-08-04T19:00:00.000Z`).

Two things to settle alongside it, both small:

1. **§10.13 survives this change.** One instant cannot record both when a test started and when it finished,
   so duration remains unrepresentable in any column. Two ways forward, either is fine:
   - **Preferred:** add a second dateTime, `Testing End Date`. Duration then becomes filterable, sortable and
     roll-up-able on their side — which is the only reason we keep asking.
   - **Otherwise:** confirm `Test Date` means the **start** instant. We keep end time and `duration_s` in
     `Complete LabOS JSON Response`, and the payload loses nothing — only Airtable's ability to report on it.
2. **Confirm the two-write lifecycle (§10.8)** while we are here, because a single `Test Date` only works
   cleanly if it means *start*: LabOS upserts **twice** per attempt — once at start (`In Progress`, partial
   payload) and once at terminal state (`Completed` / `Abborted`, full payload), both on the same
   `LabOS Attempt ID`, so the second merges onto the first rather than creating a row. The first write is what
   gives them live visibility of a test in progress.
3. **Set the field's time zone explicitly, identically in both bases.** Airtable dateTime fields carry a
   display time zone. We store and send UTC; we would rather that be a stated setting than a default someone
   changes later.

---

## 5. What their message does *not* answer — the agenda for tonight

Their three questions are all schema-shaped. The two items that gate go-live are not, and neither appears in
their message. **Order the call by blast radius, not by their agenda.**

| # | Item | § | Owner | Why it leads |
|---|---|---|---|---|
| **P0** | **Extraction shift** — column-positional fix, re-extract `IFET-26-0066`, and the **blast radius including jobs already marked tested** | §10.19 | Airtable | The only item that can produce a false `Passed` on a hurricane-rated assembly. One already exists (`SMI (impacts)`, `Passed` / `Completed`, against a value the proposal does not contain). |
| **P0** | **`Test Type` options** — add `Cycles`, `Impact`, `Forced Entry`, `ANSI Z97.1` **in both bases** | §10.17 | Airtable | Minutes of work. Until then four of five test types cannot be written back at all. |
| **P0** | **Approve one test write** into the **testing** base — one record, written then updated | — | Airtable / Luis | Script ready, dry-run verified, production base refused unconditionally. A one-line reply unblocks it. |
| **P1** | Make `Unit` + `Deflection Unit` **single selects** over §2.3's list; settle `in` vs `Inches` | §10.24 | Airtable | Both are free text today; their sample row and our envelope disagree, and neither side errors. Naturally closed by answering Q1. |
| **P1** | **Does anything on their side parse `Complete LabOS JSON Response`?** | §10.25 | Airtable | One yes/no. Decides whose JSON shape wins — and whether §3.3's fallback is viable at all. |
| **P1** | **Confirm the write model**: LabOS writes only `LabOS Raw Data Table`; their automation rolls up into `Protocol Sections` | §10.21 | Airtable | `Protocol Sections` already carries populated LabOS fields. If we are expected to write it, our client allowlist has to be widened deliberately. |
| **P2** | Rename `Abborted` → `Aborted` (a rename preserves cell values) | §10.18 | Airtable | We send their spelling today either way. |
| **P2** | Confirm `LabOS Attempt ID` is treated as **opaque UUID text** — their sample uses `001` | §10.22 | Airtable | A zero-padded counter collides the first time two rigs run at once, which is the normal case. |
| **P2** | `Schema Version` semantics; are `Retest Required` / `Testing Continued` genuinely optional? | §10.26 | Airtable | Decides whether their sample was incomplete or our required-set is wrong. |
| **P2** | **Seed the testing base** with one real job chain (ideally `IFET-26-0066` *after* the fix) | — | Airtable | The testing base is empty, so roll-up/linkage cannot be verified there at all. Same request serves both purposes. |
| **P2** | **Rotate both PATs** after acceptance testing | §10.10 | Airtable | They arrived as plaintext email. |

**Not Airtable's, and still ours to raise with IFET tonight if the room is right:**

- **A maintenance window** for the P0/P1 deploy — nothing is deployed, and the change set grows every week
  (runbook `runbooks/p0-p1-deploy-2026-08-28.md`, read §2 first).
- **The `test` node back online** — it is the only non-production rig. Without it the sync path is first
  exercised on production. Largest unmanaged risk in the plan.
- **Reviewing already-reported results** once the blast radius is known — a quality/business call for IFET,
  not an engineering one. We can supply the list.

---

## 6. What we commit to, so the exchange is not one-directional

- The §2 spec is ours and it is written — they can implement against it tonight.
- **The single test write runs within a day of their OK.** Testing base only; the client refuses the
  production base unconditionally.
- We bind to **field IDs**, not names, so anything they rename later is free; a removal or retype fails loudly
  at deploy rather than silently at test time.
- Results-out (roadmap R1–R3) needs nothing from them beyond that one approval, and continues regardless.
- Standing rule, unchanged and stated again: **no rig is driven from an Airtable requirement value, and no
  LabOS result is written against one, until §10.19 clears.**
- Pilot target **Friday 2026-10-09**. What moves it: the extractor fix past 18 Sep, or `Test Type` options
  past 25 Sep — see `status/revised-roadmap-2026-08-28.md` §2.

---

## 7. The reply — send as-is

> Hi — thanks, and thanks for turning this around so quickly. Answers to all three below. I've grounded them
> in what our database actually stores rather than in what we'd prefer, because on the first question that
> turns out to make your job smaller rather than larger.
>
> **1. Protocol Sections — `Required Value`.**
>
> You're right that the values carry signs, pairs and notation, and that's exactly why we'd rather not keep
> them in one cell: `+60/60` isn't one value with symbols in it, it's two values in proposal notation. On our
> side it has always been two columns — `inward_design_pressure` and `outward_design_pressure`, both numeric,
> both **NOT NULL**, both PSF. A specimen can't exist in LabOS without both of them.
>
> **The useful part: that pair is the only thing we need to read.** LabOS derives the whole test programme
> from those two numbers — six static stages at 0.75×, 1.0× and 1.5× design pressure, the eight TAS-203 cyclic
> stages with their own low/high pressures and cycle counts (3500, 300, 600, 100 inward; 50, 1050, 50, 3350
> outward), and the water stage at 0.15× — and it recalculates all of them whenever a design pressure changes.
>
> It's also worth saying the pair really is two independent numbers in practice, not a formality: across the 78
> specimens in our database, **36 of them — 46% — have a different inward and outward design pressure**, and
> they range from 3 to 491 PSF. So a single `Required Value` would lose real information on nearly half the
> jobs we've run, and the two halves can't be recovered from each other afterwards. It's also why a `9` doesn't
> look wrong on its own — it sits comfortably inside the range of real design pressures.
>
> So **you don't need to model ranges, cycle sequences, cycle counts or hold times at all.** We don't read
> them; we compute them. That removes most of what your question was worried about.
>
> What we'd ask for on `Protocol Sections`, with `Value` completely unchanged as the human-readable string:
>
> - `Requirement Kind` — single select: `Magnitude`, `Directional Pair`, `Count`, `Enum`, `Not Applicable`
> - `Required Value` — number (signed; for `Magnitude` and `Count`)
> - `Required Value Inward` — number, PSF (`+60/60` → `60`)
> - `Required Value Outward` — number, PSF (`+60/60` → `60`)
> - `Required Unit` — single select
>
> `Requirement Kind` is the one doing the real work: it makes each row self-describing, so when you add or
> rename a section later we aren't guessing at its shape. And please keep genuinely-absent requirements
> **blank** rather than `0` — a blank water requirement and a water requirement of zero are different
> statements, and one of them is a test.
>
> If five fields is more than you want to add, a single long-text `Required Testing Parameters (JSON)` per
> section works for us too and we'll supply the shape. The only reason we prefer typed fields is that they're
> filterable and roll-up-able on *your* side; JSON in long text isn't.
>
> **Units per section** — one unit per section record, determined by the parameter. Using the section names as
> they are live today:
>
> | Section Name | Kind | Unit | Where it lands in LabOS |
> |---|---|---|---|
> | `LMI (impacts)` | Count | `impacts` | large-missile impact count |
> | `SMI (impacts)` | Count | `impacts` | small-missile impact count |
> | `# Dials` | Count | — | number of deflection gauges |
> | `Static / Type` | Enum | — | which programme runs |
> | **`DP (+) (PSF)`** | **Directional Pair** | **`PSF`** | **design pressure — drives all 14+ derived stages** |
> | `Water (PSF)` | Magnitude | `PSF` | water-infiltration test pressure |
> | `Forced Entry (*)` | Enum | — | — |
> | `Cyclic (PSF)` | Directional Pair | `PSF` | derived from the pair — nothing to read |
> | `Impact` (ANSI Z97.1) | Enum | — | — |
>
> On the unit lists themselves, I'd suggest keeping them scoped rather than one long list, because the sets
> genuinely differ:
>
> - `Required Unit` — `PSF`, `in`, `s`, `cycles`, `impacts`
> - `Unit` on the raw table — `PSF`, `PSI`, `in`, `mm`, `cycles`, `s`, `impacts`
> - `Deflection Unit` — `in`, `mm`
>
> Short form as the stored value; long forms like "Inches" are a display choice for the interface. Our impact
> and infiltration measurements use units that deliberately get no column — kg, m/s, m², cfm/ft² —
> and travel inside `Complete LabOS JSON Response` with the unit declared per value. The one that might earn a
> real field later is air leakage in cfm/ft² — we measure it between 0.25 and 4.98 — if you ever want to report
> on it.
>
> While you're in there — **could `Unit` and `Deflection Unit` on the raw table become single selects over
> those lists?** Both are free text today, and your sample row has `Deflection Unit = "Inches"` where our spec
> says `in`. Free text accepts both, so the column ends up holding two spellings of one unit and nothing ever
> errors. A single select turns that into an error at the first write, which is where we'd rather find it.
>
> **2. Retests.**
>
> The row model is confirmed exactly as you describe it — new record, new `LabOS Attempt ID`, incremented
> `Attempt Number`, same four Airtable IDs. And the shared `LabOS Test ID` is already in every payload we
> send; that's what it's for, so nothing changes there.
>
> Where we'd ask you to reconsider is treating it as a **replacement** for `Corrects Attempt ID`, because the
> two answer different questions. `LabOS Test ID` tells you which attempts belong to the same test.
> `Corrects Attempt ID` tells you whether attempt 2 was a **second real test** or a **fix to a mis-recorded
> attempt 1** — and both of those produce the identical row you described.
>
> That distinction decides how the data should be counted:
>
> - **Retest** — the specimen really was tested twice. Two rows, both valid data. Count both.
> - **Correction** — one test, recorded wrongly. Two rows, only the second is true. Count one, and exclude the
>   first.
>
> So any automation that counts attempts or works out a pass rate is wrong in one of the two cases — and it
> will look right, which is the part that concerns us.
>
> This isn't a hypothetical shape, either: across 507 tests in our database, **106 — about one in five —
> already have more than one attempt**, and some have three. Right now nothing in that data says which of the
> two situations each one was.
>
> A real example from this project: in July we found a rig logging PSI as PSF, so a result already written as
> `40 PSF` was actually `5760`. We can't edit the old row — it's terminal, and a report had already cited it —
> so the only honest fix is a new row that states what it supersedes and why. Marking the old row `Superseded`
> is then yours, from that field. We deliberately don't want the ability to alter a record we already wrote.
>
> To be concrete about the size of the ask: **the column already exists on our side** —
> `corrects_attempt_id`, indexed, with `correction_reason` beside it, built and tested, and already written by
> our client. What's missing is somewhere to put it. Two plain fields on the raw table would do it:
> **`Corrects Attempt ID`** (plain text — not a formula or link, since it's a branch target) and
> **`Correction Reason`** (long text). Both blank on every retest; populated only on a correction, which is
> rare.
>
> If adding fields is awkward, there's a cheaper option: we already include `corrects_attempt_id` inside
> `Complete LabOS JSON Response`, so a single formula field on your side (`REGEX_EXTRACT` over that text)
> would surface it as something you can filter on, with no other change. That does depend on the JSON shape
> being settled — see the question below.
>
> **3. Test Date.**
>
> Yes — `dateTime` with `2026-08-04T19:00:00.000Z` is exactly right, and it's what we produce internally. Two
> small things to go with it:
>
> - Our side has always had two columns, `testing_start_date` and `testing_end_date`, both timezone-aware. A
>   single instant can't hold both, so test duration stops being reportable in Airtable. If you can add a
>   second dateTime (`Testing End Date`) it becomes filterable and roll-up-able for you; if not, we'll treat
>   `Test Date` as the **start** instant and keep end time and duration in the JSON field. Either is fine — we'd
>   just like it decided rather than assumed.
> - Related, and worth confirming: we write **twice** per attempt on the same `LabOS Attempt ID` — once when a
>   test starts (`In Progress`, partial payload) and once when it finishes (`Completed` / `Abborted`, full
>   payload). The second merges onto the first rather than creating a second row. The first write is what gives
>   you live visibility while a test is running. Just confirm that suits you.
> - Could you also set the field's time zone explicitly, and identically in both bases? We store and send UTC,
>   and we'd rather that be a stated setting than a default.
>
> **Still open from our side, in the order they matter:**
>
> 1. **The extraction shift** — the column-positional fix, the re-extract of `IFET-26-0066`, and how many other
>    jobs were loaded the same way, *including any already marked tested*.
>
>    One thing we found while preparing this answer, which I think settles the diagnosis independently of the
>    PDF: our water-infiltration test pressure is calculated as **15% of the inward design pressure**. The
>    proposal says DP `+60/60` and Water `9` — and 60 × 0.15 = 9 exactly. So the `9` currently sitting in
>    Airtable's `DP (+)` column is arithmetically identifiable as the **water** value, which is what you'd
>    expect if the row shifted one column left. It also explains why it looked so plausible: it isn't a
>    corrupted number, it's a real requirement in the wrong place.
>
>    That's also why it matters more than a single bad cell. Because we derive fourteen-plus test stages from
>    the design-pressure pair, a rig driven from `DP = 9` would run the *structural* test at the *water*
>    pressure, and the error is multiplied through every stage.
>
> 2. **`Test Type` options** — `Cycles`, `Impact`, `Forced Entry`, `ANSI Z97.1`, in **both** bases. Until they
>    exist we can only write back static-load results, and that job needs all five.
> 3. **The go-ahead for one test write** into the **testing** base — one record, written then updated, to
>    confirm the round-trip and the duplicate-prevention. Production untouched; our client refuses it outright.
>    A one-line reply is all we need and it doesn't have to wait for the call.
> 4. **Does anything on your side read `Complete LabOS JSON Response`?** Asking because of something specific:
>    we record **three** measurements per deflection gauge — maximum deflection, permanent set, and recovery —
>    and permanent set is a required column of the IFET report. Your sample row's JSON carries one number per
>    gauge, so whichever shape we settle on needs room for all three. If something on your side parses that
>    field we'll adopt your structure and extend it; if it's for human reading only we'll keep ours and note
>    that, so nobody builds an automation on it later.
> 5. **Just to confirm the boundary:** we write only to `LabOS Raw Data Table`, and your automation rolls that
>    up into `Protocol Sections`. We ask because `Protocol Sections` already has LabOS fields populated on it.
> 6. Smaller ones: renaming `Abborted` → `Aborted` (a rename keeps existing values); treating
>    `LabOS Attempt ID` as opaque UUID text rather than the `001` form, since two rigs running at once would
>    collide on a counter; and — whenever it suits — **seeding the testing base with one real job chain**, since
>    it's currently empty and we can't verify the roll-ups against it.
>
> Happy to go through any of this on the call.
>
> Best,
> Abdelrahman — LabOS

---

## 8. Sent record

> **Not yet sent.** Stamp here when it goes out, then close the affected items in contract §10 **first** and
> update the views. Per the filing rule, the artifact copy belongs in `correspondence/sent/` and is
> append-only once delivered.
