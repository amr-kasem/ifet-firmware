# Design decisions resolved — 2026-09-06

**Status:** DESIGN DECIDED under the user's instruction to close the design and authority to define the
Testing Base schema. **Not applied, deployed, sent or counterparty-ratified.** Filename retained for links.
Authoritative contract: `../contract/write-contract-v0.4.md`. Implementation: `integration-design-2026-09-05.md`.

- A1: One programme run per Airtable attempt; stages/shots are children; programme identity separate from run identity.
- A2: Omit unavailable rig pressure measurements; allow sourced manual measurements with units. Instrumentation is follow-on work.
- A3: Uncalibrated deflection stays local; data_quality explains missing values without publishing untrusted numbers.
- A4: Freeze terminal evidence; first review once; immutable new correction row with original reference and reason.
- A5: Selection warns; backend requires independently verified execution values and verification record, not a checkbox.
- A6: Typed supported requirement codes, explicit applicability and options; unknown/unsupported inputs cannot run.
- A7: Existing DB names remain; API speaks project/specimen; picker reads cached resources before import.
- A8: Water integration and UI remain outside this implementation scope.

Additional resolved choices: Test Date = completion; explicit UTC start/end; eight typed requirement fields
include Requirement Code, Required Option and Applicability; operational parameter rows receive no fake verdicts;
full reads every 60 seconds with configurable quota-aware interval; original photos local and previews in Airtable.

The outbox commits remain groundwork. Keeping a commit never implied approval of every behavior inside it;
implementation and tests must follow the current contract. No further design approval question is pending.
Schema additions are authorized work, and missing fields are marked PLANNED until applied and verified.
Hardware, source-data, automation and deployment checks remain delivery work with defined fallback behavior.

This session closes documentation only. Next implementation milestone is M1/M2 in the design, executed as a
separate task. The correspondence is a notice, not a prerequisite permission request, and remains NOT SENT.
