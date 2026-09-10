> # ⛔ SUPERSEDED 2026-09-10 — `production-change-spec.csv` MUST NOT BE APPLIED TO PRODUCTION
>
> That file still lists **`Missile Type`, `Missile Weight` and `Impact Velocity` as `ADD` against
> production.** On 2026-09-10 the product owner withdrew all three from the Airtable → LabOS input
> contract: the Impact requirement is now the **LabOS-owned Impact Classification**, published
> outbound. Applying the spec as it stands would create two permanently unread fields in the live
> base — the exact "harder to remove than to add" failure this document argues against elsewhere.
>
> **Production is untouched and stays at 142 fields.** The spec is regenerated as part of **TA7**,
> when the register, the generator and the code move together — regenerating it on its own would
> leave `check_register.py` red and hide the next real drift.
>
> Everything else in this record stands: it is what was applied to the **Testing** Base on
> 2026-09-06 and why. Decision record:
> `../../correspondence/po-answers-and-impact-remap-2026-09-10.md`.

# Testing Base schema changes — applied 2026-09-06

**Base:** Testing `app4oXS3Kd5IKWgJ7` · **Production `app0OCunbmuXl7Hc9` was not touched.**
**Result:** 14 fields added across 2 tables. **142 → 156 fields.** No field was renamed, retyped or removed,
and no record was created, edited or deleted.
**Applied by:** `ifet-management` `app/airtable/apply_schema.py --apply` (additive only; production refused
unconditionally; re-running is a no-op).

This is the document IFET asked for: what changed, and why each change exists. It is written from the
before/after schema captured at the moment of the change, not from intent.

| Evidence file | What it holds |
|---|---|
| `before-*.json` | Full Testing Base schema immediately before the first write |
| `after-*.json` | Full Testing Base schema immediately after the last write |
| `changes-*.json` | One entry per field: action taken and the field ID Airtable returned |

Machine-readable mapping for both bases: `../../contract/interface-schema.csv`.
Meaning and write rules: `../../contract/write-contract-v0.4.md`.

---

## Why these 14 and not others

Two problems drove every change.

**A requirement row could not describe itself.** `Protocol Sections` carried a human-readable `Section Name`
and a free-text `Value` such as `+110/110`. To execute against that, LabOS would have to parse prose and
guess at meaning — and the values arriving from the proposal extractor are known to be shifted, so a wrong
number reads as a plausible one. Eight typed fields make the row self-describing, so LabOS reads structure
instead of guessing, and an unrecognised requirement stays visible but **cannot start a test**.

**A result row could not express a correction, a reviewer, or when a test physically ran.** Six fields on
`LabOS Raw Data Table` close that: correction linkage, review identity and time, explicit execution start and
end, and an attachment channel for photograph previews.

`Section Name` and `Value` are untouched and stay as the human-readable original. Nothing existing changed.

---

## `Protocol Sections` — 8 fields

| Field | Type | Field ID | Why it exists |
|---|---|---|---|
| `Requirement Code` | singleSelect | `fld9Fzjj25ngrVIOB` | Stable code that decides which procedure a section means. **LabOS routes by this code, never by `Section Name`** — so renaming a section can never silently change what a rig executes. Options: `STATIC_PRESSURE`, `CYCLIC_PRESSURE`, `IMPACT_LMI`, `IMPACT_SMI`, `FORCED_ENTRY`, `ANSI_IMPACT`, `GAUGE_COUNT`, `STATIC_PROGRAMME`, `WATER_PRESSURE`. An unknown code is visible but not executable. `WATER_PRESSURE` is visible and deliberately unsupported this release |
| `Requirement Kind` | singleSelect | `fldWGpL9gJh89wSK8` | The **shape** of the requirement, so LabOS never parses `Value`. `Magnitude`, `Directional Pair`, `Count`, `Enum`, `Not Applicable`. Note `Not Applicable` means *no numeric requirement* (Forced Entry, ANSI) — it does **not** mean the test is unneeded |
| `Applicability` | singleSelect | `fldh3VS09fonTLHsS` | Whether the section is actually required for this specimen. `Required`, `Not Required`, `Unconfirmed`. **Only `Required` is executable, and blank is treated as `Unconfirmed`, never as `Not Required`** — LabOS will not infer that a test is unneeded from an empty cell or a historical result |
| `Required Value` | number | `fldpL2dyGzKj9xowY` | The numeric requirement for `Magnitude` and `Count`. **Blank is not zero:** blank means unknown and blocks execution, while a real `0` is data |
| `Required Value Inward` | number | `fld1wR9ojdmESax0m` | Inward design pressure, independent positive magnitude, PSF |
| `Required Value Outward` | number | `fld7GLStvnPnYJPpd` | Outward design pressure, held **separately and never copied from inward**. Production data shows **46% of jobs are asymmetric**, so one number cannot stand for both, and a sign convention cannot encode them |
| `Required Unit` | singleSelect | `fldTjNKeQe7oxxl33` | Unit for `Required Value`. `PSF`, `in`, `s`, `cycles`, `impacts`; blank for a unitless count, `Enum` or `Not Applicable`. Short forms only — LabOS rejects `Inches` as a token, so `in` is canonical on both sides |
| `Required Option` | singleLineText | `fldflOxCkAK1BkU9l` | The explicit enum value for `Enum` requirements, so it need not be parsed out of `Value`. `Full` is the initially supported static programme |

**Why typed pressure fields rather than parsing `Value`.** Ranges, slashes and signs in the legacy string are
never execution inputs. Direction is carried by the *field name*, not by a sign. And while the extractor
defect is unresolved, LabOS still will not drive a rig from these numbers — an operator must enter the
independently verified pair from the trusted proposal. These fields make the requirement **legible and
comparable**; they do not by themselves make it trusted.

## `LabOS Raw Data Table` — 6 fields

| Field | Type | Field ID | Why it exists |
|---|---|---|---|
| `Corrects Attempt ID` | singleLineText | `fldV4ucQNEA0gYfMc` | On a correction row, the `LabOS Attempt ID` it supersedes. **The original row is never edited or deleted.** Roll-ups must exclude superseded attempts and must not count a correction as an extra physical test |
| `LabOS Verdict By` | singleLineText | `fldVedw9cOgne8UeX` | Declared identity of the reviewer who set `Test Result`. Kept **separate from `Operator Name` even when it is the same person**, because running a test and judging it are different acts. Nothing records this today |
| `LabOS Verdict At` | dateTime | `fldqCkqAh7aTckxSR` | UTC instant of the first review. Written once, with the verdict |
| `Testing Start Date` | dateTime | `fldYU1BtWVuWv5DBV` | UTC instant physical execution started. **`Test Date` remains the completion instant** — one field could not carry both, which is why start and end are now explicit |
| `Testing End Date` | dateTime | `fldTsjf78Y5fA85fz` | UTC instant execution completed or aborted; absent while running. **A correction preserves the original execution times** rather than stamping when the correction was written |
| `LabOS Photos` | multipleAttachments | `fldsEfhtH9wXPAl1Y` | Downscaled JPEG previews. Full-resolution originals stay in LabOS and are immutable. Each preview carries a stable artifact ID, content hash and deterministic filename, so an uncertain upload can be **reconciled rather than blindly re-appended** |

All five date/time fields are ISO, 24-hour, **UTC**. Reports render America/New_York with the offset;
Airtable's automation derives the local `Protocol Sections` `Testing Date` from the completion instant.
**LabOS never writes `Testing Date`, `Result` or `Status` on a Protocol Section.**

---

## Seven fields deliberately **not** created

IFET's 2026-09-06 workflow message raised seven more. They are recorded in the register as
`OPEN`/`PROPOSED` and the apply script **refuses to create them**, because an unwanted field is harder to
remove than to add — and now that the Testing Base is the template production will be built from, a
speculative field would propagate.

| Field | Table | What has to be decided first |
|---|---|---|
| `Missile Type` | Protocol Sections | The protocol normally fixes the missile. Does Airtable carry it at all, or only per-job deviations? |
| `Missile Weight` | Protocol Sections | Same question, plus the unit |
| `Impact Velocity` | Protocol Sections | Same question. Target only — achieved shot velocity stays in LabOS |
| `Impact Locations` | Protocol Sections | Its relationship to total impacts is unsettled; they are not the same number |
| `Forced Entry Result` | LabOS Raw Data Table | Standing decision is JSON-only with `Test Result` carrying pass/fail. **Which named report needs a dedicated column?** |
| `ANSI Result` | LabOS Raw Data Table | Same — decide with `Forced Entry Result` or not at all |
| `Failure Notes` | LabOS Raw Data Table | Today one `Notes` field carries both meanings. Separate field, or a structured section inside `Notes`? |

---

## Three things to settle before production

**1. Four fields will arrive empty, by design.** `Max Pressure Achieved`, `Deflection Value`,
`Deflection Unit` and — for rig Static Load and Cycles — `Measured Value`.

The reference row `recxZWiVa5Wuy0ZV6` populates all four, so the expectation is already set and needs
correcting. The rigs report no pressure at all: static pressure is an open-loop operator slider, so the
configured setpoint is not an achieved value. Deflection readings are raw sensor counts mislabelled as
inches, spanning −1280 to +1288, which are not plausible deflections in any unit.

LabOS sends a machine-readable `data_quality` reason instead of a fabricated number. Both are tracked as
hardware work (plan M6, M7) and both need bench time. **Do not build a report that assumes these columns are
populated.**

**2. `Deflection Unit` divergence.** The reference row holds `Inches`. LabOS emits `in` / `mm` and rejects
`Inches` as a token. `Required Unit` above already uses the short form. When deflection is unquarantined,
the existing `Deflection Unit` field needs its options aligned.

**3. `LabOS Attempt ID` is a UUID, not a sequence.** The reference row holds `001`. It is the **upsert merge
key** on every phase and retry, so it must be a persisted, globally unique, plain-text value — not a
computed field and not a counter. `Attempt Number` carries the human-readable ordinal instead.

---

## Effect on the existing Airtable automations

The Airtable developer team's automations run on this schema. **We cannot see them** — the Meta API returns
`403 INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND` for `/meta/bases/{base}/automations`, so this section is a
structural argument, not a verified one. Their team should confirm it.

**Every change was additive.** No field was renamed, retyped, reordered or removed, no select option was
added to or removed from an existing field, and no record was touched. That rules out the ways a schema
change normally breaks an automation: a trigger bound to a field that no longer exists, a condition testing
an option that changed spelling, or a script reading a field whose type moved underneath it.

Two things still deserve their eyes:

| Risk | Why it matters |
|---|---|
| **A "when record updated" trigger with no field filter** | LabOS writes in phases — create, terminal, first review — and now writes more fields per record. Such a trigger will fire more often than before. If one exists on `LabOS Raw Data Table`, scope it to the fields it actually cares about |
| **An automation that writes `Protocol Sections`** | LabOS never writes `Result`, `Status` or `Testing Date` there, so there is no collision by design. Worth confirming their automation still owns those exclusively once it starts reading `Applicability` and `Requirement Code` |

**What we are asking their automations to do that is new**, once the schema is confirmed: link a result to its
test by `LabOS Test ID`, derive the section completion date from `Testing End Date` in America/New_York,
project the LabOS verdict into the operational views, exclude superseded corrections from roll-ups, and
exclude parameter rows such as gauge count from test counts. None of that is assumed to work merely because
the fields now exist — it is acceptance work before production cutover.

## Kept deliberately small

The brief was a simple design, not an over-engineered one. What that ruled out:

- **No new tables and no new relationships.** Everything is a field on a table that already exists.
- **No dedicated scalar for every outcome.** `Test Type` and `Test Result` are both `singleSelect`, so
  Airtable already filters and groups all five workflows natively; per-test detail rides in the existing
  JSON field. That is why Forced Entry and ANSI got no column of their own — see the seven above.
- **No parsing, no backfill, no migration of `Value`.** The legacy string is preserved untouched.
- **No delta-cursor or change-tracking field.** LabOS re-reads the four tables in full every 60 seconds and
  hashes the content, so Airtable needs no extra column to support synchronisation.
- **One writable table.** LabOS writes `LabOS Raw Data Table` and nothing else.

**One field is worth challenging: `Requirement Kind`.** Per contract §3.2 every `Requirement Code` implies
exactly one kind — `STATIC_PRESSURE` is always a Directional Pair, `GAUGE_COUNT` is always a Count. So the
field is derivable, and a derivable field that must agree with its source is a place for the two to
disagree. It was added as an explicit self-description rather than a shared lookup table both sides must
keep in step. **If the Airtable team prefers fewer fields, this is the one to drop** — it is the only one of
the 14 that carries no information the code does not already imply.

---

## Production

**The 14 fields above are exactly the production delta.** `../../contract/interface-schema.csv` is
generated from both live bases and marks each row `in_testing` / `in_production`, so the delta is queryable
rather than transcribed.

Production replication is a separately coordinated release step (plan M5) and is **not** performed by this
script — the production base is refused unconditionally, with no flag to override it. Once the shared
Airtable view becomes editable and is confirmed as the agreed schema, this document is what production
should be built from.
