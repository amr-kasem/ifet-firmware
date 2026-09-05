# LabOS integration design and planned Testing Base changes

**Author:** Abdelrahman · **Date:** 2026-09-06 · **Status:** DRAFT NOTICE — NOT SENT; NO CHANGES APPLIED
**Authority:** the user has authorized LabOS to define the required Testing Base fields/types and document them.
**Specification:** `../contract/write-contract-v0.4.md`; mapping: `../design/field-register-2026-09-05.csv`.
This replaces this file's earlier question list. It is a notice of decided design, not proof of delivery or
an assertion that the Airtable team has ratified its production automations. The August 31 draft stays historical.

## 1. Answers to the three earlier questions

**Required Value.** Preserve Value and add typed scalar/directional fields and units. Inward/outward pressure
fields each hold an independent positive magnitude in PSF. Add Requirement Code, Required Option and
Applicability so routing, enum values and missing/not-required inputs are explicit. LabOS does not parse legacy
slash strings, ranges or symbols. It validates supported codes/shapes and uses independently verified source
values while the extraction defect remains unresolved. No historical values will be silently converted.

**Retests.** New Attempt ID and number, same Test ID, one row per programme run. Stages/shots are child detail.
Corrections also get a new row but explicitly identify the superseded Attempt ID and reason; the original stays
unchanged. LabOS will add Corrects Attempt ID in the Testing Base and validate correction-aware roll-ups.

**Test Date.** Thank you for delivering dateTime. For the new contract Test Date means execution completion;
LabOS adds explicit Testing Start Date and Testing End Date, preserving both in JSON too. UTC on the wire;
America/New_York in lab reports. Airtable automation derives its section date from completion. Existing records
are not reinterpreted or rewritten by this change.

## 2. Planned additions and responsibilities

Protocol Sections: Requirement Code, Requirement Kind, Required Value, Required Value Inward, Required Value
Outward, Required Unit, Required Option, Applicability. No existing field is deleted or retyped.

Raw Data: Corrects Attempt ID, LabOS Verdict By, LabOS Verdict At, Testing Start Date, Testing End Date,
LabOS Photos. Existing Photos URL and all five Test Type options remain. Canonical schema/payload version is 0.4.

Static/Cycles produce one programme-run result; Impact, Forced Entry and ANSI use the same attempt model.
Gauge count and static-programme selection are parameters, not independent tests. Water integration is deferred.
LabOS records verdicts; Airtable owns their operational projection. Blanks and historical Passed values do not
establish applicability or a new measured verdict. Original photographs stay in LabOS; Airtable receives previews.

## 3. Delivery limitations and coordination

The extractor issue still requires source-data remediation. Until verified, rig inputs are independently
checked against the approved proposal. LabOS will omit uncalibrated deflection and unavailable achieved rig
pressure; these require separate LabOS measurement work. Manual measurements remain possible with explicit units.

Before production use, validate the UUID/run/correction/date/JSON mapping against Airtable automations, replicate
the Testing Base changes through the production deployment owner, and agree the maintenance window. Those are
delivery checks; LabOS no longer needs another field-design permission round. Existing production mappings remain
unchanged until cutover. Full-read polling avoids needing new modification-time fields in this phase.

## 4. Final change document

Maintain planned/applied/verified states per change. After Testing Base work, issue the actual before/after
fields/types/IDs/options, reasons, example synthetic payloads, validation results, automation impacts and rollback
instructions. Do not describe a planned field as already added. Keep customer records out of public git.

## 5. Paste-ready notice

Hi team,

With authorization to adapt the Testing Base to LabOS requirements, we have finalized the implementation
design. We will preserve existing fields and add explicit typed requirement values, units, requirement codes,
applicability and enum options. Inward/outward pressures are separate positive PSF magnitudes; legacy text is
preserved for reference and never silently parsed into rig settings.

Your retest model is retained. Each programme run has its own Attempt ID and number, grouped under one Test ID;
stage/shot detail stays within the run. Corrections get a new row identifying the superseded attempt and reason.

Test Date will represent completion for new version 0.4 records, with explicit start/end fields and UTC timestamps.
We are also adding reviewer identity/time and an attachment field for photo previews. LabOS retains original
evidence and owns verdicts; Airtable retains project/specimen/protocol operations and roll-ups.

These changes are planned, not applied yet. We will provide the actual change register, reasons, sample data,
validation and rollback notes after Testing Base implementation. Production schema/automation compatibility and
cutover will be coordinated separately. The known extraction and LabOS measurement issues remain explicitly
handled: independently verified rig inputs, and omission of unavailable/untrusted measurements.

Best,
Abdelrahman

## 6. Sent record

NOT SENT. Record recipient, channel, date and exact final wording only after an explicitly authorized send.
