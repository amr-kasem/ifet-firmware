# LabOS ↔ Airtable — Production schema requirements

**From:** LabOS (Abdelrahman) · **To:** the Airtable team · **Date:** 2026-09-11

**This document says exactly what to add or change in the Production base so it matches the LabOS
integration contract.** It is written for whoever edits the schema. It is not a status report.

| | |
|---|---|
| **Production base** | `app0OCunbmuXl7Hc9` — **142 fields today** |
| **Testing base** | `app4oXS3Kd5IKWgJ7` — **164 fields**, where all of this is already applied and proven |
| **Requested** | **19 ADD** · 0 rename · 0 retype · 0 option change · 0 delete |
| **Production after** | **161 fields** |
| **Working sheet** | `LabOS-Airtable-Production-Schema-Changes-2026-09-11.csv` — one row per field for all 164, **generated** from the two live bases and never hand-edited |
| **When LabOS starts writing them** | **not yet.** The integration is built and proven against the Testing base; it has **not been released to our production system**. Creating these fields is safe and changes nothing on your side until we tell you we are live — see §6 for what changes when we are |

Every number above was read from the live Meta API on 2026-09-11 and re-verified by our pre-send check,
which compares every row of the CSV against both bases and fails if any of them disagrees.

**Two separate actions, two separate owners.** Section 7 is a data-correction request that is **not** a
schema change and is not addressed to the schema engineer. Promoting the schema does not require it, and it
does not require the schema promotion. Please do not let either wait on the other.

---

## 1. Every table in the base, and what LabOS does with it

All eight tables, not only the one in the shared link.

| # | Table | Table ID | Production fields | LabOS access | Purpose for LabOS | Action needed? |
|---|---|---|---|---|---|---|
| 1 | IFET Projects | `tblLYcRC7q6Srjfk3` | 35 | **READ** | Identify which job a result belongs to. 2 fields read | **No** |
| 2 | Mock-Ups/Specimens | `tblcrGv0WJn6FTTGO` | 13 | **READ** | Identify the specimen, and its link to the job. 2 fields read | **No** |
| 3 | Tests Protocols | `tblutO1Q8TNC4BLk0` | 8 | **READ** | Identify the protocol, and its link to the specimen. 2 fields read | **No** |
| 4 | **Protocol Sections** | `tblqpvuJlSdkeS9PS` | 16 | **READ** | **The requirements themselves.** 10 fields read | **YES — 8 ADD** |
| 5 | Walls & Positions | `tblVUvcSPAoneG26W` | 8 | **NONE** | Not used | **No** |
| 6 | Wall Scheduling/Reservation | `tblYjF1AApzmRDMrY` | 19 | **NONE** | Not used | **No** |
| 7 | Back Charges | `tbl0f2YxS3FHJ1dTD` | 13 | **NONE** | Not used | **No** |
| 8 | **LabOS Raw Data Table** | `tblnc9SsbXU0C0FWh` | 30 | **WRITE** | **The only table LabOS writes.** 40 fields written | **YES — 11 ADD** |
| | **Total** | | **142** | | | **19 ADD → 161** |

### The ownership boundary, stated plainly

- **READ ONLY — tables 1, 2, 3, 4.** LabOS reads them and **never writes them**. Not a job, not a specimen,
  not a protocol, not a section. `Result`, `Status` and `Testing Date` on your side stay yours.
- **WRITE — table 8 only.** Every LabOS write in the entire integration goes to `LabOS Raw Data Table`.
- **NO ACCESS — tables 5, 6, 7.** All 40 fields. Wall reservations, capacity, `Billable Amount`,
  `Internal Cost`, `Approval Status`: LabOS is a test executor and reads none of it. Nothing in this
  request touches them.

**What enforces that, because we would rather you knew than assumed.** An Airtable PAT is scoped **per
base, not per table**, so our token *could* write any of the eight. Two things stand in the way and both
are ours: the client refuses any write to a table outside a one-table allowlist before the request is
made, and nothing in the code calls a read path for tables 5–7. The first is enforced in code and tested;
the second is an application decision. Every live verification run snapshots all four hierarchy tables
before and after and asserts that nothing was written to them.

---

## 2. `Protocol Sections` — 8 fields to add ⚠️ the machine-readable requirement

**This is the important half of the request.** Today a requirement is expressed in the human-readable
`Value` column — free text mixing a magnitude, an enum and a pressure pair, with the unit encoded in the
section name. **LabOS does not and will not parse it.** These eight fields are the typed form.

| Field | Airtable type | Options / precision | Direction | Why LabOS needs it | Testing field ID |
|---|---|---|---|---|---|
| `Applicability` | singleSelect | Required · Not Required · Unconfirmed | IN | Required/Not Required/Unconfirmed. Blank=Unconfirmed, never infer from Value or historical Result. Only Required is executable. | `fldh3VS09fonTLHsS` |
| `Required Option` | singleLineText | — | IN | READ. The named grade or class a pass/fail test is judged against - 'ASTM F588 Grade 40' for Forced Entry, 'Class A' for ANSI Z97.1, 'Full' for the static programme. Free text, so an unrecognised option is displayed and non-executable, neve… | `fldflOxCkAK1BkU9l` |
| `Required Unit` | singleSelect | PSF · in · s · cycles · impacts | IN | READ for validation only. PSF/in/s/cycles/impacts. LabOS refuses a value whose unit does not match the requirement kind rather than assuming PSF. | `fldTjNKeQe7oxxl33` |
| `Required Value` | number | precision 2 | IN | READ. The scalar for Count and Magnitude kinds - gauge count via GAUGE_COUNT, impact count via IMPACT_LMI/IMPACT_SMI. Blank is not zero: a missing requirement is absent, never 0. | `fldpL2dyGzKj9xowY` |
| `Required Value Inward` | number | precision 2 | IN | READ, and the single most load-bearing field in the integration. LabOS derives all 14 stages from the pair - 6 static factors [0.75,0.75,1,1,1.5,1.5] and 8 cyclic high/low factors with fixed cycle counts. Independent positive PSF magnitude;… | `fld1wR9ojdmESax0m` |
| `Required Value Outward` | number | precision 2 | IN | READ. The other half of the pair. Independent of inward and never copied from it - a transposition would be individually plausible and silently wrong. | `fld7GLStvnPnYJPpd` |
| `Requirement Code` | singleSelect | STATIC_PRESSURE · CYCLIC_PRESSURE · IMPACT_LMI · IMPACT_SMI · FORCED_ENTRY · ANSI_IMPACT · GAUGE_COUNT · STATIC_PROGRAMME · WATER_PRESSURE | IN | STATIC_PRESSURE/CYCLIC_PRESSURE/IMPACT_LMI/IMPACT_SMI/FORCED_ENTRY/ANSI_IMPACT/GAUGE_COUNT/STATIC_PROGRAMME/WATER_PRESSURE. Water visible but unsupported; names are labels. | `fld9Fzjj25ngrVIOB` |
| `Requirement Kind` | singleSelect | Magnitude · Directional Pair · Count · Enum · Not Applicable | IN | READ. Says how to interpret the requirement: Magnitude / Directional Pair / Count / Enum / Not Applicable. LabOS refuses a kind it does not support rather than guessing. | `fldWGpL9gJh89wSK8` |
### What each typed concept means, and how they fit together

`Requirement Code` says **which test**. `Requirement Kind` says **how to read the numbers**. The kind then
decides which of the value fields must be present. A section whose kind and code disagree is refused rather
than guessed at, and so is a unit that cannot mean anything for that kind.

| `Requirement Code` | `Requirement Kind` must be | Values it needs | Becomes, in LabOS |
|---|---|---|---|
| `STATIC_PRESSURE` | Directional Pair | `Required Value Inward` **and** `Required Value Outward`, unit `PSF` | 6 static stages |
| `CYCLIC_PRESSURE` | Directional Pair | the same pair, unit `PSF` | 8 cyclic stages |
| `IMPACT_SMI` · `IMPACT_LMI` | Count | `Required Value`, unit `impacts` | how many impacts |
| `GAUGE_COUNT` | Count | `Required Value` | how many gauges — a parameter, not a test |
| `FORCED_ENTRY` | Not Applicable | `Required Option` — the grade | a Forced Entry test |
| `ANSI_IMPACT` | Not Applicable | `Required Option` — the class | an ANSI Z97.1 test |
| `STATIC_PROGRAMME` | Enum | `Required Option` | a parameter. Only `Full` is supported; anything else is **refused, not run as Full** |
| `WATER_PRESSURE` | Magnitude | `Required Value` | visible, not executable in this release |

Four rules that are not negotiable, because each one was a real defect:

1. **Blank is never zero.** A missing `Required Value` is a refusal. Zero is a requirement of zero.
2. **Blank `Applicability` means `Unconfirmed`, never `Not Required`.** Treating an empty cell as "not
   needed" silently drops a test nobody had got round to marking, and the drop looks like a decision.
   Only `Required` is executable.
3. **Inward and outward are independent.** Never copied from one another and never collapsed to one
   scalar — a transposition is individually plausible and silently wrong.
4. **A unit that contradicts its kind is refused**, not assumed to be PSF. A wrong unit is not a rounding
   error, it is a different test.

`Required Unit` is read for validation only. Its values are `PSF`, `in`, `s`, `cycles`, `impacts`.

**The `Value` column is untouched by this request.** Keep it for people. LabOS will not read it, now or
later, and §7 is why.

---

## 3. `LabOS Raw Data Table` — 11 fields to add

Everything LabOS produces that currently has nowhere to go. **LabOS writes these; nothing else should.**

| Field | Airtable type | Options / precision | Direction | Why LabOS needs it | Testing field ID |
|---|---|---|---|---|---|
| `ANSI Result` | singleSelect | Pending · Passed · Failed · Inconclusive | OUT | REOPENED with Forced Entry Result 2026-09-10; identical shape, gated to Test Type = ANSI Z97.1. APPLIED to the Testing Base 2026-09-11 fldmCKJV95N9uL7xt. Not in production, and guarded against reaching it by preflight check 2. | `fldmCKJV95N9uL7xt` |
| `Corrects Attempt ID` | singleLineText | — | OUT | Required on a new correction row; references original UUID. Never update original or disguise correction as retest. | `fldV4ucQNEA0gYfMc` |
| `Forced Entry Result` | singleSelect | Pending · Passed · Failed · Inconclusive | OUT | REOPENED by the product owner 2026-09-10: question 2 came back NO - 'they are different under different standards'. The Forced Entry verdict, projected from test_results.test_result and gated to Test Type = Forced Entry; omitted entirely on… | `fldAHuPzZHZEj0Cjt` |
| `Impact Classification` | singleSelect | SMI · LMI Level D · LMI Level E | OUT | DERIVED OUTPUT ONLY - no column holds this string and no API field sets it. SMI · LMI Level D · LMI Level E. For an Airtable-bound test the SMI/LMI half is frozen at import from the section's IMPACT_SMI/IMPACT_LMI requirement code and only … | `fldMY7DiiuP9kbQbL` |
| `Impact Number` | number | precision 0 | OUT | READ AS THE IMPACT ORDINAL. Populated only for Test Type = Impact, where one attempt is one impact (product owner 2026-09-08); blank on the other four types. Same column as Attempt Number by construction - for Impact the attempt ordinal IS … | `fldk52wf0SO9zYDjB` |
| `LabOS Photos` | multipleAttachments | — | OUT | Persisted immutable JPEG preview; artifact ID/full hash/deterministic filename. Single owner; reconcile uncertain remote uploads, park ambiguity instead of blind append. | `fldsEfhtH9wXPAl1Y` |
| `LabOS Verdict At` | dateTime | — | OUT | UTC first-review timestamp. Required with first review in scalars and detailed JSON; missing schema parks delivery. | `fldqCkqAh7aTckxSR` |
| `LabOS Verdict By` | singleLineText | — | OUT | Declared reviewer identity. Required with first review in scalars and detailed JSON; missing schema parks delivery. | `fldVedw9cOgne8UeX` |
| `Target Impact Velocity` | number | precision 2 | OUT | The target the operator entered, ft/s, precision 2. A target is never an achieved value (A2): the per-impact achieved velocity stays on shots.velocity and travels only in the JSON. NOT derived from the classification - no authoritative deri… | `fldhywP9YpsmoWWT1` |
| `Testing End Date` | dateTime | — | OUT | UTC completion/abort time; absent while running; also Test Date. | `fldTsjf78Y5fA85fz` |
| `Testing Start Date` | dateTime | — | OUT | UTC physical execution start; corrections preserve original. | `fldYU1BtWVuWv5DBV` |
### Three shapes where the type alone is not the contract

- **`Forced Entry Result` and `ANSI Result` must be created with exactly `Pending` · `Passed` · `Failed` ·
  `Inconclusive`.** Those are **your** spellings, matching `Test Result`. A select created with LabOS's
  internal `Pass`/`Fail` would accept nothing we send and would pass any type check while doing it.
- **`Impact Classification` is exactly `SMI` · `LMI Level D` · `LMI Level E`.** Three options, no others.
- **`Target Impact Velocity` is a number at precision 2**, in ft/s. Precision 0 truncates 50.25 to 50.

### `Forced Entry Result` and `ANSI Result` do **not** replace `Test Result`

`Test Result` is unchanged and still carries the verdict for **all five** test types, at create (as
`Pending`), at terminal and at first review. The two new columns are **additions beside it**: the same
value, projected onto its own standard, populated only for their own `Test Type` and **absent — not
blank — on the other four**.

This is the shape `Impact Result` already has in your base today. Our project owner asked for it on
2026-09-10 because Forced Entry and ANSI Z97.1 are judged under different standards, so a report about one
of them should not have to filter `Test Result` by `Test Type` first.

**We previously told you we would add these only if you named a report that needed them.** That statement
is withdrawn; the rule was ours.

### Impact — what LabOS sends you, and what it no longer asks for

| | |
|---|---|
| **You still supply** | how many impacts — `Required Value` with `Requirement Code` `IMPACT_SMI` or `IMPACT_LMI`. **Unchanged** |
| **LabOS will send back**, once the fields exist | `Impact Classification` · `Target Impact Velocity` · `Impact Number` · `Impact Result` |

Your `Requirement Code` already distinguishes large missile from small, so the only fact it never carried
was Level D versus Level E — and that is our operator's. Nothing about the missile is asked of you any
more.

---

## 4. Fields you must NOT create in production

These three were added to the **Testing** base on 2026-09-08 and withdrawn from the LabOS contract on
2026-09-10, when the impact requirement reversed direction. **LabOS does not read them.** They have never
existed in production and must stay that way.

| Field | Table | Airtable type | Testing field ID | Instruction |
|---|---|---|---|---|
| `Impact Velocity` | Protocol Sections | number | `fldJNfUVyqQEFOVWx` | **Do not create in production** |
| `Missile Type` | Protocol Sections | singleLineText | `fld5Bs0aQXXeVso2y` | **Do not create in production** |
| `Missile Weight` | Protocol Sections | number | `fldmhdhonyyLcx4Ex` | **Do not create in production** |
They are deliberately **left in place in Testing** rather than deleted — removing a field from a base you
share is your call, not a side effect of our code change. We would like to agree a cleanup with you
separately; see §8.

This is enforced rather than remembered: the generator omits any field the register marks deprecated, and
our pre-send check asserts on every run that all 22 guarded fields — the 19 additions **and** these three —
are absent from production.

---

## 5. What is already correct and needs no change

**`Test Type` in production already carries all five options** we publish: `Static Load` · `Cycles` ·
`Impact` · `Forced Entry` · `ANSI Z97.1`. **KEEP — no option change required.** Verified against the live
production schema on 2026-09-11.

Also verified correct as they stand, and listed because we send them:

| Field | Production today | Action |
|---|---|---|
| `Test Result` | singleSelect — `Pending` · `Passed` · `Failed` · `Not Applicable` · `Inconclusive` | **KEEP** |
| `Test Status` | singleSelect — `Not Started` · `In Progress` · `Completed` · `Abborted` | **KEEP** — we send your spelling verbatim, misspelling included. Do not "fix" it; changing an existing option breaks rows that hold it |
| `Test Date` | dateTime, local/client | **KEEP** — unchanged. The three dateTime fields we are adding are UTC/ISO and are separate columns |
| `Impact Result`, `Correction Reason`, `Notes`, `Photos` | as they are | **KEEP** |

**Across all 142 existing production fields: 0 renamed, 0 retyped, 0 option changes, 0 deleted.** That is
what makes this change additive in the sense your automations care about, and it is checked rather than
asserted — the CSV carries production's own type and options per field and the check fails if any of them
has diverged from Testing.

---

## 6. What changes for your views, roll-ups and automations

Adding a field changes nothing on its own. **Three of these change what your existing base sees**, and one
of them changes it materially.

| Field | What changes for your views, roll-ups and automations |
|---|---|
| `ANSI Result` | New reporting axis, as Forced Entry Result. Blank on the other four types. |
| `Corrects Attempt ID` | Distinguishes a correction from a retest. A roll-up that picks the current result should prefer a row that is not superseded by a later correction. |
| `Forced Entry Result` | New reporting axis. A view or report about Forced Entry alone no longer has to filter Test Result by Test Type first. Blank on the other four types. |
| `Impact Classification` | New reporting axis for Impact. Populated by LabOS on the results row; blank on the other four types. |
| `Impact Number` | CHANGES WHAT EXISTING ROLL-UPS SEE. One physical impact is now one row, so a five-impact test publishes five rows where it published one. Count tests by grouping on LabOS Test ID; count impacts with this field. A roll-up that counts rows to mean tests will over-count impact tests. |
| `LabOS Photos` | Attachment field. An automation that fires on record update will see it populated separately from the result, because attachments are delivered on their own channel and may land after the verdict. |
| `LabOS Verdict At` | Set once, at first review. Useful as the trigger for anything that should fire on a reviewed result rather than on a recorded one. |
| `LabOS Verdict By` | Set once, at first review, alongside LabOS Verdict At. |
| `Target Impact Velocity` | Populated by LabOS for Impact only. **Precision 2 matters**: precision 0 truncates 50.25 ft/s to 50 and would pass a type check while doing it. |
| `Testing End Date` | As Testing Start Date. |
| `Testing Start Date` | UTC instant, ISO, 24-hour. Distinct from your existing Test Date, which is unchanged and stays local/client. |
### ⚠️ The one that needs a decision from you: one impact is now one row

Previously a five-impact test published **one** row with a summary line. It now publishes **five**, each
with its own verdict and its own photographs.

- Count **tests** by grouping on `LabOS Test ID`.
- Count **impacts** with `Impact Number` — 1, 2, 3 — which is blank on the other four test types.
- **Any roll-up that counts rows to mean "tests" will over-count impact tests** by the number of impacts,
  unless it groups on `LabOS Test ID` first.

Our project owner confirmed this consequence on 2026-09-08, and `Impact Number` exists precisely so the
distinction is available to you rather than having to be inferred. **Please tell us if any existing
roll-up, view or automation counts rows as tests**, so it can be re-pointed before the model changes under
it.

### And one behaviour worth knowing before you write an automation

Every LabOS write is an **upsert on `LabOS Attempt ID`**. A retry after a network failure updates the same
record; it never inserts a second one. So an automation triggered on *record created* sees one creation per
attempt, while one triggered on *record updated* sees an attempt updated up to three times as it moves
create → terminal → verdict, plus once per photograph — photographs are delivered on their own channel and
may land after the verdict.

---

## 7. Separate action — extraction and data correction

> **Owner: IFET / the Airtable ingestion owner.** **Not the schema engineer, and not a blocker for §2–§4.**
> The schema promotion can be done today without any of this, and this can be done without the schema
> promotion.

**The defect.** The proposal extractor that populates your base reads **values in order rather than by
column**. When a cell is blank, every value after it slides one position to the left. We have column-position
evidence from the source PDF: a design pressure of `+60/60` arrived as `9`, the value belonging to
`# Dials`, and the run of blanks at `Water` / `Forced Entry` re-anchored it further down. This has already
reached at least one record marked Passed/Completed.

**Why it cannot be detected downstream.** `9` is a number, in the right column, with the right unit, of the
right kind. It validates. Every shifted value is individually plausible — that is the character of the
defect — so no range check, sanity band or heuristic on our side could distinguish it from a real
requirement without becoming a new way to be confidently wrong. We have deliberately not built one.

**What LabOS has built, so you know what is and is not covered — and when it takes effect.** The control
is written and proven, and it **goes live with our next release, not today**: an Airtable-imported Static
Load or Cycles job becomes **non-executable** in LabOS until a named person has read the design-pressure
pair off the trusted proposal and it **agrees** with what we mirrored from your base. A disagreement is
refused and nothing is recorded; LabOS does not choose between two sources that contradict each other.
**This makes an affected job stop rather than run wrong. It is a safe failure, not a fix** — and it costs an operator a manual verification on every imported job for as long as the defect
exists.

**What we need from the ingestion owner**, and none of it is a schema edit:

| # | Action |
|---|---|
| 1 | **Fix the positional extraction** so values are read by column rather than by order, with blanks preserved in place |
| 2 | **Report the affected scope** — which production records, over what date range, were populated by the affected extractor |
| 3 | **Re-extract those records** and **validate each against the source proposal**, by a person, not by a second pass of the same tool |
| 4 | **Confirm the typed fields in §2 will be populated from a trustworthy source** — the eight fields are only as good as what fills them. If the same extractor populates them, the defect moves rather than closes |
| 5 | Tell us when 1–4 are done, so we can review whether the manual verification step can be relaxed |

Until then the typed fields in §2 are still worth adding: they remove the *parsing* ambiguity even while
the *extraction* ambiguity is open, and they are what our verification compares against.

---

## 8. Two questions, neither blocking

1. **The three withdrawn fields in Testing** — `Missile Type`, `Missile Weight`, `Impact Velocity`. Would
   you like them removed, and if so, on what date? We have left them alone rather than deleting fields from
   a base you share.
2. **Our synthetic verification records in the Testing base.** Our end-to-end runs create a marked job with
   its own specimen, protocol and sections, and result rows tagged `Operator Name = LABOS-PROBE-TA6`,
   `LABOS-PROBE-TA7` and `LABOS-E2E-*`. **Would you prefer we retain them as acceptance evidence, or remove
   them after sign-off?** We have not deleted anything; we will do whichever you prefer, as a recorded
   operation. **Neither question blocks the schema promotion.**

---

## 9. How to apply this, and how we will both check it

1. Work from `LabOS-Airtable-Production-Schema-Changes-2026-09-11.csv`. Filter `action = ADD` — 19 rows —
   and create each in the named table with the type and the options/precision given.
2. **The `fld…` IDs in this document are Testing IDs.** Airtable mints a new one when you create the field
   in production and **they will not match**. Nothing in LabOS depends on a production field ID — we key on
   the field *name* — so please do not copy them anywhere.
3. When you are done, tell us. We re-read both bases through the Meta API and confirm **161 fields**, each
   new field's type, options and precision, and that the three withheld fields are still absent.
4. We will send back the read-back so you have our confirmation in writing.

**LabOS cannot apply any of this itself.** Our schema tool refuses the production base unconditionally,
with no flag or environment variable that overrides it. That refusal is deliberate and stays.

---

## 10. What is not in this request

- **No deflection data reaches Airtable**, now or as part of this. `Deflection Value`, `Deflection Unit`
  and `Max Pressure Achieved` are never written — they have no validated source, and their absence is a
  decision rather than an oversight.
- **No commercial field is read.** Not `Approved Proposal Amount`, not `Balance Due`, not customer
  contacts, not the QuickBooks IDs.
- **Nothing is read or written in tables 5, 6 and 7.** All 40 fields, untouched.
- **Nothing is renamed, retyped or deleted anywhere.**

---

**Verified against the live bases on 2026-09-11.** Testing `app4oXS3Kd5IKWgJ7` 164 fields · Production
`app0OCunbmuXl7Hc9` **142 fields, unchanged and never written by LabOS**. Evidence:
`../evidence/ta6-live-probe-2026-09-11/` (101/101) · `../evidence/ta7-live-probe-2026-09-11/` (64/64) —
both compare the production schema before and after every run, byte for byte.
