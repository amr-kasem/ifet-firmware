# Testing Base changes applied, and three decisions we need

**Author:** Abdelrahman · **Date:** 2026-09-06 · **Status:** **READY TO SEND — not yet sent**
**Authority:** LabOS is authorized to define and add the required Testing Base fields, with a documented
change register. This is a change *report* plus three open questions — not a permission request.
**Specification:** `../contract/write-contract-v0.4.md` · **Mapping:** `../contract/field-register.csv`
**Change document:** `../evidence/testing-base-changes-2026-09-06/`

> **What changed in this draft, and why.** The earlier version of this file said the additions were
> "planned, not applied yet." That is no longer true — **the 14 fields were applied to the Testing Base on
> 2026-09-06** and the change document exists. Sending the old wording would have understated what we had
> already done and would have asked for permission we already had. It also never asked the three questions
> that are actually blocking us. The August 31 draft stays historical.

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

**Seven fields were requested by the workflow message and deliberately NOT created.** They are §3 below.
An unwanted field is harder to remove than to add, and now that this schema becomes the shared source of
truth for production, a speculative field would propagate rather than sit harmlessly in a sandbox.

---

## 3. Three decisions we need from you — this is the blocking part

Your workflow message asked for things that are not yet in the mapping. We have not created any of these
fields, because each one needs an answer first.

### 3.1 Impact requirements — what should Airtable actually carry?

The register carries only a **count** of impacts. Missile type, missile weight and target velocity — the
values our own tables hold — are nowhere in it, so an LMI operator still types them by hand, which is
exactly the double entry you asked us to remove.

**Our question:** the protocol normally fixes the missile and the velocity. Should Airtable carry these at
all, or only where a specific job **deviates** from the protocol default?

| Candidate field | Type | Our assumption |
|---|---|---|
| `Missile Type` | singleSelect | Blank means "use the protocol default" |
| `Missile Weight` | number | Unit to be agreed **before** creation |
| `Impact Velocity` | number | Target only. Never an achieved value |
| `Impact Locations` | number | Count of distinct impact points |

**`Impact Locations` needs care:** it is **not** the same number as the total impact count already in
`Required Value`. Before we create it, we need to know which of the two your reports use.

### 3.2 Forced Entry, ANSI Z97.1 and failure notes — which report needs a dedicated field?

`Test Type` and `Test Result` are both `singleSelect`, so Airtable can already filter and group both
workflows natively, and the sub-detail travels in JSON. Our standing decision is to add a dedicated scalar
only when a **named operational report** requires one.

**Our question:** is your message asking for dedicated fields, or describing what you want *visible* — which
`Test Result` plus the JSON already satisfies? If a report needs them, name it and we will add them.

- `Forced Entry Result` and `ANSI Result` — decide **both together or neither**; splitting them would leave
  the schema inconsistent.
- `Failure Notes` — the most likely to be genuinely wanted. Today one `Notes` field carries both general
  commentary and failure description. Separate field, or a structured section inside `Notes`?

### 3.3 Loading sequences — who owns them?

Your message lists loading sequences as flowing **from** Airtable **into** LabOS. Nothing in Airtable holds
them today. LabOS derives 14+ stages from the verified inward/outward pair, and that derivation is validated
to full precision against production data.

**Our recommendation: LabOS keeps deriving them, and Airtable supplies only the pressure pair.** It works
today, it is already proven, and it removes something that would otherwise have to stay in sync between two
systems. But this is currently an assumption on our side and a different assumption on yours, and it changes
what a `Protocol Section` has to carry — so we would like it settled in writing before we build further.

---

## 4. Three things we need you to do

1. **Validate your automations against the new mapping.** We cannot see them — the Meta API refuses
   `/meta/bases/{base}/automations` with `403`. Every change we made was additive, which rules out the usual
   breakages, but two things need your eyes: **an unfiltered "when record updated" trigger will now fire more
   often**, and your `Protocol Sections` automation must keep exclusive ownership of `Result`, `Status` and
   `Testing Date`. We are not assuming production's automations are compatible merely because the fields
   exist; that gets verified before cutover.
2. **The extractor defect still needs remediation on your side.** It remains the only true gate on running a
   rig from Airtable requirement values. See §5.
3. **A blast-radius report — including jobs already marked tested.** A shifted value has already reached a
   Passed/Completed record, so this is not hypothetical. Which results are affected is a quality and business
   call, not an engineering one.

---

## 5. One thing our design does that you should hear from us, not discover

**We are adding a step that contradicts your "no double entry" requirement, deliberately, and only until the
extractor is fixed.**

Before a rig can start, the operator must enter the actual inward/outward pair from the trusted proposal,
along with the proposal reference, who verified it and when. Airtable's values are shown next to it for
comparison, but **they cannot start a rig.**

The reason is that the extractor drops blank cells, so a `+60/60` requirement can arrive as `9`. LabOS cannot
detect that — every shifted value is individually plausible, which is precisely what makes it dangerous. We
are not willing to drive a physical test from a number we cannot trust.

This costs the operator real work, and it is the one thing we cannot remove from our side. **It relaxes to a
one-click confirmation the day the extraction is fixed.** The typed `Protocol Sections` fields above are what
make that verification expressible in the first place.

---

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

To close out your three earlier questions: `Value` is preserved and never parsed — the new typed fields carry
inward and outward pressures as separate positive PSF magnitudes, plus a requirement code, kind, unit,
applicability and enum option. Your retest model is retained: one row per programme run with its own Attempt
ID under a shared Test ID, corrections as a new row identifying the superseded attempt and reason, original
untouched. `Test Date` now means execution completion, with explicit start and end timestamps in UTC.

**Three things we need decided before we build further.**

1. **Impact requirements.** You asked us to stop the operator retyping them. The protocol normally fixes the
   missile and velocity — should Airtable carry missile type, weight and target velocity at all, or only
   where a job deviates from the protocol default? And `Impact Locations` is not the same number as the total
   impact count: which one do your reports use? We have not created these fields yet.
2. **Forced Entry and ANSI Z97.1 results, and failure notes.** `Test Type` and `Test Result` are both
   single-selects, so you can already filter and group both workflows, with the detail in JSON. Are you
   asking for dedicated fields, or for those results to be *visible*? If a specific report needs dedicated
   fields, tell us which report and we will add them — Forced Entry and ANSI together. `Failure Notes` is the
   one we think you genuinely want, since today a single `Notes` field carries both meanings.
3. **Loading sequences.** Your message has these flowing from Airtable into LabOS, but nothing in Airtable
   holds them, and LabOS already derives the full stage sequence from the verified pressure pair — validated
   against production data. **We recommend LabOS keeps deriving them and Airtable supplies only the pair**,
   which avoids keeping the same thing in sync in two systems. We would like that confirmed in writing, since
   it changes what a Protocol Section needs to carry.

**Three things we need from you.**

- **Please check your automations against the new fields.** We cannot see them — the API returns 403 for
  automations — so we cannot verify this ourselves. Everything we added was additive, but an unfiltered
  "when record updated" trigger will now fire more often, and your `Protocol Sections` automation should keep
  sole ownership of `Result`, `Status` and `Testing Date`.
- **The proposal extraction issue still needs fixing at source.** It is the one genuine blocker on trusting
  requirement values.
- **A blast-radius report, including jobs already marked tested.** A shifted value has already reached a
  Passed record, so deciding what to do about previously reported results is a quality call on your side.

**One thing we want you to hear from us directly.** Until the extraction is fixed, our operators must enter
the verified inward/outward pair from the approved proposal before a rig will start, with the proposal
reference and who checked it. Airtable's values are displayed alongside for comparison but cannot start a
test. This does contradict the "no double entry" goal, and we are doing it deliberately: the extractor drops
blank cells, so a +60/60 requirement can read as 9, and every shifted value looks individually plausible. We
are not willing to drive a physical pressure test from a number we cannot verify. **It becomes a one-click
confirmation the day extraction is fixed.**

Production replication and the cutover window we will coordinate separately.

Best,
Abdelrahman

---

## 8. Sent record

**NOT SENT.** Record recipient, channel, date and the exact final wording here only after an authorized send,
then copy the artifact into `sent/` — that folder is append-only and is never edited afterwards.
