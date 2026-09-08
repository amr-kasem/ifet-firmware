# Business I/O reconciliation — all five test types, 2026-09-08

**What this is.** Every business-required input and output for the five workflows, traced
`Airtable field → validated local storage → actual source or calculation → outbound field + delivery phase`.
64 rows in `reconciliation.csv`.

**Why it exists.** The change document and the delivery plan each described parts of this path, and an
independent audit showed both claiming coverage the code does not have. This traces the whole path once, per
field, and marks each row with what is actually true. **Requirements not covered by the 17 field additions
are included deliberately** — omitting them is how "we deliver everything except the measurements" becomes
invisible.

## The states, and what each means

| State | Rows | Meaning |
|---|---|---|
| `OK` | 16 | Path complete: stored, sourced, mapped to a phase |
| `OK-STORAGE` | 9 | Local column exists and is correct; **nothing populates it yet** (no import path) |
| `OK-JSON-ONLY` | 6 | No Airtable scalar by decision §10.15; travels in the JSON field |
| `OK-BY-DECISION` | 3 | Field deliberately not created; the value reaches Airtable another way |
| `OK-BASELINE` | 1 | Pre-existing field, path complete |
| **`GAP-*`** | **18** | **Our unbuilt work. Each blocks something specific** |
| **`UNMET-*`** | **6** | **A business requirement we cannot satisfy today, and why** |
| `OUT-OF-SCOPE` | 1 | Water infiltration, deferred by contract §0 |

## The gaps, grouped by what causes them

**No local mirror or programme tables — 5 rows + 1 JSON row.** `Requirement Code` and `Applicability` are
the two fields that decide *which test is required* and *whether it is required at all*, and neither has a
local column. The register targets `mirror.*`; `models.py` has no `at_mirror_*`, `test_programmes` or
`test_programme_runs`. **This is the largest gap and everything pre-fill depends on it.**

**No import path — 2 rows.** `POST /projects/import` is specified in plan §4.2 and unbuilt, so even the
columns that exist (`projects.airtable_mockup_name`, `project_parents.name`) are never populated from
Airtable. This is why nine rows read `OK-STORAGE` rather than `OK`.

**The outbound mapper resolves 2 of 5 test types — 4 rows.** `mapping.owning_test()` traverses
`static_test` and `cyclic_test` only, so all four Airtable IDs are unresolvable for Impact, Forced Entry and
ANSI. Every one of those four rows is a `create`-phase field, so this blocks publishing any manual attempt.

**No validator — 2 rows.** The kind/unit contradiction check the contract specifies, and the change document
claimed, does not exist. The only artifact is a field description inside Airtable.

**Identity and ordinal allocation — 2 rows.** `LabOS Test ID` has three formats (DG12).
`Attempt Number` uses `count()+1` / `len(trials)+1` with **no** uniqueness constraint — while `shots` has
exactly the constraint that is missing here (`UniqueConstraint(test_result_id, shot_number)`), so the
codebase already knows the pattern.

**No correction route — 2 rows.** `corrects_attempt_id` and `correction_reason` have columns, a property and
an envelope mapping, and nothing that sets them (DG13).

**Attachment channel — 2 rows.** Preview generation and independent dispatch are both unbuilt; the phase
constant exists but the upload workflow does not.

**One type confusion.** `Impact Velocity` is a **target** in Airtable and the register maps it to
`shots.velocity`, which is the **achieved** value of one impact. A requirement needs its own column on
`missile_impact_tests`. Left as-is, a pre-fill would overwrite an observation, or a target would be
published as an achievement — the same class of defect the envelope already refuses for
`Max Pressure Achieved`.

**One unreconciled parameter.** `GAUGE_COUNT` is a snapshotted programme parameter; firmware takes
`selectedSensors[]` live at MQTT start. A mismatch at start has no defined behaviour (DG6).

## The six UNMET rows — business requirements we cannot meet today

These are kept explicit rather than narrowed out of the acceptance tests.

| Requirement | Why unmet | What it needs |
|---|---|---|
| `Measured Value`, Static | Firmware sends no measurement for static load | A measurement source, or permanent omission by decision (A2) |
| `Measured Value`, Cycles | Same | Same |
| `Max Pressure Achieved` | **A source exists** — actual pressure is on the MQTT bus and renders live in the UI. Nothing subscribes and stores it | Software only, TC4 |
| `Deflection Value` | Raw SICK counts, never calibrated to a physical unit | Bench calibration — hardware |
| `Deflection Unit` | Same | Same |
| `recovery` | It is the `recovery_time` **config constant** (60 s), not an observation | Nothing — it must never be published as a measurement |

The last row is the one most likely to be mistaken for progress: a number is present, it is not a
measurement, and the firmware runtime audit of 2026-08-31 established that.

## What this changes about acceptance

An acceptance run that exercises only Static and Cycles would pass while three test types cannot resolve
their Airtable identity, and would say nothing about pre-fill. So the round-trip proof must cover **all
five types**, and must record the `UNMET` rows as expected absences rather than quietly omitting the fields.
