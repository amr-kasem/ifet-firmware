# Testing Base changes applied, and how LabOS will use them

**Author:** Abdelrahman · **Date:** 2026-09-06 · **Status:** **READY TO SEND — not yet sent**
**Authority:** LabOS is authorized to define and add the required Testing Base fields, with a documented
change register. This is a change *report* plus a scope narrowing — it asks no blocking questions.
**Specification:** `../contract/write-contract-v0.4.md` · **Mapping:** `../contract/field-register.csv`
**Change document:** `../evidence/testing-base-changes-2026-09-06/`

> **What changed in this draft, and why.** Two rewrites on 2026-09-06. First, the earlier version still said
> the additions were "planned, not applied yet" — untrue once the 14 fields went in — so it understated the
> work and asked for permission we already had. Then **decision A9** narrowed the integration: LabOS runs
> standalone and reads no requirement values, which withdrew all three of the questions this document had
> been written to ask. What is left is a report and three requests. The August 31 draft stays historical.

---

## 1. Answers to their three earlier questions

Unchanged and still accurate.

**Required Value.** Preserve `Value` and add typed scalar/directional fields and units. Inward and outward
pressures each hold an independent positive magnitude in PSF. `Requirement Code`, `Required Option` and
`Applicability` make routing, enum values and missing/not-required inputs explicit. LabOS does not parse
legacy slash strings, ranges or symbols; it validates supported codes and shapes. No historical value is
silently converted.

**Retests.** New Attempt ID and number, same Test ID, one row per programme run. Stages and shots are child
detail. Corrections also get a new row that explicitly identifies the superseded Attempt ID and the reason;
the original stays unchanged.

**Test Date.** Thank you for delivering `dateTime`. Under contract 0.4 `Test Date` means execution
completion, with explicit `Testing Start Date` and `Testing End Date` alongside it. UTC on the wire,
America/New_York in lab reports. Existing records are not reinterpreted or rewritten.

---

## 2. What we changed — applied, with evidence

**14 fields added, 142 → 156. Production `app0OCunbmuXl7Hc9` was not touched.** No field was renamed,
retyped or removed; no record was created, edited or deleted. Re-running the tool is a no-op.

| Table | Fields |
|---|---|
| `Protocol Sections` (8) | `Requirement Code`, `Requirement Kind`, `Applicability`, `Required Value`, `Required Value Inward`, `Required Value Outward`, `Required Unit`, `Required Option` |
| `LabOS Raw Data Table` (6) | `Corrects Attempt ID`, `LabOS Verdict By`, `LabOS Verdict At`, `LabOS Photos`, `Testing Start Date`, `Testing End Date` |

Full before/after schema, the field ID Airtable returned for each, and the reason each one exists:
`../evidence/testing-base-changes-2026-09-06/`. `Section Name` and `Value` are untouched and remain the
human-readable original.

**Three fields stay deliberately absent** — `Max Pressure Achieved`, `Deflection Value`, `Deflection Unit`.
No validated measurement source exists for them yet, and we would rather omit a number than publish one we
cannot stand behind. Tracked as our own work (M6/M7).

**Seven further fields were requested by the workflow message and deliberately NOT created**, and under A9
(§3) they are no longer wanted at all. An unwanted field is harder to remove than to add, and now that this
schema becomes the shared source of truth for production, a speculative field would propagate rather than
sit harmlessly in a sandbox.

---

## 3. How LabOS uses this schema — narrowed, 2026-09-06

**Decision A9: LabOS runs standalone, and Airtable is management's mirror.** LabOS is fully functional
without Airtable and stays that way. The integration exists so management can see jobs and reports without
chasing the lab — it is not a dependency of testing, and an Airtable outage cannot affect a test.

That narrows what we read to almost nothing:

| We read (14 fields) | Table |
|---|---|
| `record_id`, `IFET job number`, `Project name` | IFET Projects |
| `record_id`, `Project Name`, `Mock-up/specimen name` | Mock-Ups/Specimens |
| `record_id`, `Mock-Up`, `Protocol Name` | Tests Protocols |
| `record_id`, `Test Protocol`, `Section Name`, `Requirement Code`, `Applicability` | Protocol Sections |

`Requirement Code` is the only one that is not pure identity, and it is there to say **which of the five
tests a section is**. Everything else is the join and the display names.

**We do not read any requirement values.** Not `Required Value`, not the inward/outward pair, not `Value`,
not units or options. The operator sets a test up in LabOS exactly as they do today. Those fields stay in
both bases and we simply do not consume them.

**Three earlier questions therefore withdraw**, and none of them needs your answer:

- **Impact requirements** (missile type, weight, target velocity) — not needed. Operators enter these in
  LabOS. We have not created those fields and will not.
- **Forced Entry and ANSI result fields** — not needed. `Test Type` and `Test Result` are both single
  selects, so you can filter and group both workflows already, and the detail travels in the JSON. We will
  add a dedicated field only if a specific report of yours turns out to need one — tell us and we will.
- **Loading sequences** — LabOS derives them and needs nothing from Airtable.

**The join key.** Everything hangs off `IFET job number`, with the Airtable `rec…` record IDs carried
alongside. The record ID is what actually routes a result; the job number is what a person reads. That is
deliberate — the job number is hand-typed, so if it were the only key a renumber or a typo would silently
re-point a job's results and nothing would notice.

## 4. Three things we need you to do

1. **Validate your automations against the new mapping.** We cannot see them — the Meta API refuses
   `/meta/bases/{base}/automations` with `403`. Every change we made was additive, which rules out the usual
   breakages, but two things need your eyes: **an unfiltered "when record updated" trigger will now fire more
   often**, and your `Protocol Sections` automation must keep exclusive ownership of `Result`, `Status` and
   `Testing Date`. We are not assuming production's automations are compatible merely because the fields
   exist; that gets verified before cutover.
2. **The extractor defect still needs remediation on your side.** It no longer gates *us* — A9 means we read
   no requirement values — but it still misstates requirements inside your own records. See §5.
3. **A blast-radius report — including jobs already marked tested.** A shifted value has already reached a
   Passed/Completed record, so this is not hypothetical. Which results are affected is a quality and business
   call, not an engineering one.

---

## 5. The extraction defect, and why it no longer blocks us

Earlier drafts of this document warned that our operators would have to re-enter the verified
inward/outward pair before a rig would start — a step that contradicted your "no double entry" goal.

**A9 removes that.** Because LabOS reads no requirement values from Airtable, there is no path by which a
shifted value could reach a rig, and therefore nothing for the operator to double-check. The operator's
workflow is exactly what it is today. No double entry is introduced.

The defect still matters, on your side: a shifted value has already reached a Passed/Completed record, and
deciding what to do about previously reported results is a quality call rather than an engineering one. It
just is not a gate on our delivery any more.

## 6. What happens next

We maintain planned/applied/verified state per change. The Testing Base work above is **applied**; the
verified column fills in as the integration exercises each field end to end. Production schema replication
and the maintenance window are coordinated separately with the deployment owner, and existing production
mappings are unchanged until cutover.

Canonical schema and payload version is **0.4**. Customer records stay out of git — both repositories are
public.

---

## 7. Paste-ready message

Hi team,

**The Testing Base changes are done.** We added 14 fields across two tables, 142 → 156 — eight on
`Protocol Sections` so a requirement row can describe itself, and six on `LabOS Raw Data Table` for
correction linkage, reviewer identity and time, explicit execution start/end, and photo previews. Nothing
was renamed, retyped or removed, no records were touched, and the production base was not modified. A full
change document is attached: before/after schema, the field ID for each, and why each one exists.

To close out your three earlier questions: `Value` is preserved and never parsed; your retest model is
retained, with one row per programme run under a shared Test ID and corrections as a new row naming the
superseded attempt; and `Test Date` now means execution completion, with explicit start and end timestamps
in UTC.

**One thing has changed on our side, and it makes this simpler for both of us.**

LabOS runs standalone. It is fully functional without Airtable and will stay that way — the integration
exists so you can see jobs and results without chasing the lab, not as something testing depends on. An
Airtable outage cannot stop or affect a test.

Concretely, that means **we read almost nothing from Airtable**: the record IDs, the IFET job number, the
project/specimen/protocol/section names, plus `Requirement Code` and `Applicability` on a section. Fourteen
fields, and only `Requirement Code` is more than identity — it tells us which of the five tests a section
is. Everything hangs off the IFET job number for people, with the Airtable record IDs carried alongside as
the key that actually routes a result.

**We do not read any requirement values at all** — not `Required Value`, not the inward/outward pair, not
`Value`, units or options. Our operators set a test up in LabOS exactly as they do today. Those fields stay
where they are; we simply do not consume them.

Three things we had been about to ask you therefore withdraw, and none needs an answer:

- **Impact requirements** (missile type, weight, target velocity) — not needed; operators enter these in
  LabOS. We have not created those fields and won't.
- **Forced Entry and ANSI result fields** — not needed. `Test Type` and `Test Result` are both single
  selects, so you can already filter and group both workflows, and the detail travels in the JSON. If a
  particular report of yours needs a dedicated field, tell us which and we'll add it.
- **Loading sequences** — LabOS derives these itself and needs nothing from Airtable.

This also settles the double-entry question. Earlier we were going to ask operators to re-key the verified
pressures before a rig would start, which cut against your "no double entry" goal. Since we now read no
requirement values, there is nothing to re-key and nothing to check — the operator's workflow is unchanged.

**Three things we do need from you.**

- **Please check your automations against the new fields.** We can't see them — the API returns 403 for
  automations — so we can't verify this ourselves. Everything we added was additive, but an unfiltered
  "when record updated" trigger will now fire more often, and your `Protocol Sections` automation should
  keep sole ownership of `Result`, `Status` and `Testing Date`.
- **The proposal extraction issue still needs fixing at source.** It no longer blocks us, but it still means
  some requirement values inside your own records are wrong.
- **A blast-radius report, including jobs already marked tested.** A shifted value has already reached a
  Passed record, so deciding what to do about previously reported results is a quality call on your side.

Production replication and the cutover window we'll coordinate separately.

Best,
Abdelrahman

---

## 8. Sent record

**NOT SENT.** Record recipient, channel, date and the exact final wording here only after an authorized send,
then copy the artifact into `sent/` — that folder is append-only and is never edited afterwards.
