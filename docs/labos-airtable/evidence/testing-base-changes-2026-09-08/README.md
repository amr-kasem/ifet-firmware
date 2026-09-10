# Testing Base change — three Impact requirement fields, 2026-09-08

**Delta on top of the 14 fields applied 2026-09-06.** Testing Base
`app4oXS3Kd5IKWgJ7`: **156 → 159 fields**. Production `app0OCunbmuXl7Hc9` is
untouched and remains at 142.

Applied with `python -m app.airtable.apply_schema --apply`, the same tool and the
same safety rules as the 14: production refused unconditionally with no flag that
overrides it, dry run by default, idempotent (the existing 14 reported `SKIP`),
and before/after schema captured to this directory.

## What was added, and why

| Field | Type | Field ID | Why |
|---|---|---|---|
| `Missile Type` | singleLineText | `fld5Bs0aQXXeVso2y` | The missile the protocol specifies, e.g. *Large Missile D*. Free text because the standard's set is open and LabOS does not invent an option set the requirement side does not have. Pre-fills `missile_impact_tests.missile` |
| `Missile Weight` | number (2dp) | `fldmhdhonyyLcx4Ex` | Missile mass in pounds. Pre-fills `missile_impact_tests.missile_weight`. **A requirement, never a measurement** — LabOS never writes an achieved value back here |
| `Impact Velocity` | number (2dp) | `fldJNfUVyqQEFOVWx` | Target impact velocity, ft/s. Mirrored and frozen into the requirement snapshot; pre-fills no test column. The *achieved* velocity stays local on `shots.velocity` and is not published: a target is never an achieved value (decision A2) |

All three land on **Protocol Sections**, and all three read into columns that
already exist in the LabOS database — so nothing new had to be modelled to
consume them. Two of them pre-fill a test: `importer.bind` sets
`missile_impact_tests.missile` and `.missile_weight` when it creates the impact
test. `Impact Velocity` does **not** pre-fill a test column — it is mirrored on
`at_mirror_sections.impact_velocity` and frozen into the attempt's requirement
snapshot (`airtable/requirements.snapshot`), where it rides in the JSON response.
It is never written to `shots.velocity`, which is the operator's achieved value.

## Why these three and not four

`Impact Locations` was proposed alongside them and is **deliberately not
created**. Location is a per-shot observation LabOS already records on
`shots.area`, not a requirement. And now that the shared Airtable view is
becoming the schema production is built from, a speculative field propagates
rather than sitting harmlessly in a sandbox — an unwanted field is harder to
remove than to add.

## Why they came back at all

A9 closed these as `OMITTED` on 2026-09-06, when the decision was that LabOS
would read **no** requirement values, because the PDF extractor shifts columns
and a 60 PSF requirement can read as 9.

That was refined on 2026-09-08 rather than reversed. The extractor corrupts the
**legacy `Value` text field**. The eight typed fields added on 2026-09-06 are
separate fields that the extractor does not write. So:

> **LabOS reads the typed fields and never parses `Value`.**

Pre-fill is therefore delivered *and* the shift stays structurally out of the
execution path. That single sentence is the core of the change document, and it
is what makes these three fields safe to add.

Impact was the one test type pre-fill could not yet serve: the count already
arrived via `Required Value` + `IMPACT_LMI`/`IMPACT_SMI`, but the missile did not.

## Verified by the fixture, not asserted

`python -m app.airtable.fixture --apply` seeded a synthetic proposal into the
Testing Base — which had **zero records** until this point — and read it back the
way LabOS will. Job `IFET-FIXTURE-0001`, one mock-up, one protocol, six Protocol
Sections covering all five executable requirement codes plus `GAUGE_COUNT`.

Confirmed on read-back:

- every field LabOS claims to read is readable and correctly typed;
- the **asymmetric** design pair 60/45 PSF derives all fourteen stages —
  6 static `[45.0, 33.75, 60, 45, 90.0, 67.5]` and 8 cyclic
  `[30, 36, 48, 60 | 45, 36, 27, 22.5]` — from the pair alone;
- the three new Impact fields read back exactly as written;
- `FORCED_ENTRY` and `ANSI_IMPACT` carry a class in `Required Option`
  (`ASTM F588 Grade 40`, `Class A`) and **no** numeric `Required Value`;
- no section carries a legacy `Value`, because the fixture must not populate the
  field LabOS never parses.

The pair is asymmetric deliberately: a symmetric pair would pass even if inward
and outward were transposed, and contract §3.1 requires the two magnitudes to
stay independent. The fixture asserts this rather than trusting it.

`GAUGE_COUNT` is included even though it produces no test of its own, so that a
reader which assumed every section is executable fails here rather than in front
of an operator.

**Every value is synthetic and the job number says so.** Contract §3.3: fixture
requirements are never eligible for production execution.

## Register

`../../contract/field-register.csv`: 73 rows, all DECIDED —
44 BASELINE, **17 APPLIED**, 4 CONDITIONAL, 7 OMITTED, 1 PLANNED local-only.
Read surface is 23 `IN` rows, of which 4 are Airtable record-id metadata rather
than schema fields: **19 named fields**, which is exactly what `mirror.py`
allowlists (2 project + 2 specimen + 2 protocol + 13 section).

## Evidence in this directory

`before-*.json` · `after-*.json` · `changes-*.json` — the schema either side of
the write, and the applied diff.

---

## Postscript — 2026-09-10: the product owner has superseded two of these three

**This record stands as written.** It says what was applied on 2026-09-08 and why, and that is still what
happened. What follows is what happened next, so that a later reader does not build on the mapping above.

On 2026-09-10 the product owner replied to the five-test approval request and, without being asked,
answered the design question behind these three fields:

> "Not sure what weight is there for. once we now the type, LMI or SMI, we know the rest. Target velocity
> is either SMI, which is just one option, or LMI Level D or E. I think it would be easier if i tell
> LabOS which one it is, D or E, and that info goes to AirTable."

If the impact classification determines the mass and the target velocity, then:

| Field | Applied here as | Becomes |
|---|---|---|
| `Missile Type` `fld5Bs0aQXXeVso2y` | an inbound requirement on Protocol Sections | **outbound** — entered in LabOS, published with the result, on the results table instead |
| `Missile Weight` `fldmhdhonyyLcx4Ex` | an inbound requirement | **unread** — a parameter of the impact classification |
| `Impact Velocity` `fldJNfUVyqQEFOVWx` | mirrored, frozen into the requirement snapshot | **unread** — a parameter of the impact classification. Also closes TC1f: question 3 came back *"We will be entering it"* |

The reasoning above is not wrong so much as overtaken. **`Requirement Code` already carries `IMPACT_LMI`
versus `IMPACT_SMI`**, so the one fact Airtable never held is Level D versus Level E — and that is exactly
the fact he is offering to enter. The Impact read surface therefore goes from four fields to the one it
already had, and the read boundary shrinks from 19 named fields to 16.

**Nothing needs undoing in a live base.** All three are Testing Base only; production `app0OCunbmuXl7Hc9`
is still at 142 and never received them. The cost is register rows and the change document, not a
migration.

**The section above headed "Why these three and not four" is now confirmed rather than argued.** The
product owner answered question 4 on the same day: *"That will not be shown on LabOS or Airtable.
that is in the test plans."* `Impact Locations` stays uncreated by his decision as well as by ours.

Full decode, the corrected mapping, the register consequences and the reply:
`../../correspondence/po-answers-and-impact-remap-2026-09-10.md`.
