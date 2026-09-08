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

**Updated 2026-09-08 after the inbound half landed.** 18 gaps → **4**.

| State | Rows | Meaning |
|---|---|---|
| `OK` | **53** | Path complete: stored, sourced, mapped to a phase — and demonstrated end to end against the live Testing base |
| `OK-JSON-ONLY` / `OK-BY-DECISION` / `OK-BASELINE` | (in the 53) | No Airtable scalar by decision; the value reaches Airtable another way |
| **`GAP-*`** | **4** | **Our unbuilt work** |
| **`UNMET-*`** | **6** | **A business requirement we cannot satisfy today, and why** |
| `OUT-OF-SCOPE` | 1 | Water infiltration, deferred by contract §0 |

### Closed since the first tally

| Was | Rows | What closed it |
|---|---|---|
| `GAP-MAPPER` | 4 | the outbound mapper covers all five test types |
| `GAP-FORMAT`, `GAP-ATOMICITY` | 2 | one derived `LabOS Test ID`; attempt numbers under a constraint |
| `GAP-NO-TABLE` | 5 | the `at_mirror_*` tables — allowlisted, with **no column for `Value`** |
| `OK-STORAGE` → `OK` | 9 | the importer populates them from the mirror |
| `GAP-NO-IMPORT` | 2 | `POST /airtable/import`, through the same create path a typed project uses |
| `GAP-NO-VALIDATOR` | 2 | `requirements.validate` refuses a kind/unit contradiction |
| `GAP-UPLOADER` | 2 | preview, direct upload, returned attachment id, ambiguous-response reconciliation |
| phase / builder defects | 3 | `LabOS Updated At`'s unknown phase; the JSON body; `Impact Result` |

### The remaining 4

| | Why it is still open |
|---|---|
| `GAP-NO-ROUTE` ×2 | **Corrections.** `corrects_attempt_id` and `correction_reason` have columns, a property and an envelope mapping, and no route sets them. Every attempt is a retest today |
| `GAP-TYPE-CONFUSION` | **`Impact Velocity`** is a *target* in Airtable and the register maps it to `shots.velocity`, an *achieved* per-impact observation. It needs its own column on `missile_impact_tests` — as it stands a pre-fill would overwrite a measurement, or a target would publish as an achievement |
| `GAP-UNRECONCILED` | **`GAUGE_COUNT`** is a snapshotted programme parameter; firmware takes `selectedSensors[]` live at MQTT start, and a mismatch at start has no defined behaviour (DG6) |

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

**That is what was then done, and the six UNMET rows were confirmed absent from a
real Airtable record** — see `../live-write-proof-2026-09-08/`. The absences are
now asserted in three places: the envelope refuses the values, the local suite
asserts the refusal, and the live probe reads the row back and checks the cells
are empty.

The inbound half was unbuilt when that was written and is not any more: the
mirror tables (`at_mirror_*`, migration `b9c1f60d4e27`), the allowlisted reader
and the importer all exist, and the `IN` rows above are closed against them.
What is still unproven is the inbound half **end to end against a live base** —
the fixture proves the read, not an operator's import.

## Kept honest by

`check_register.py` in the management repo re-runs this reconciliation and the
field register against the code, offline:

    python3 app/airtable/check_register.py

Every `table.column` in `local_storage` must resolve to a real column parsed out
of the models, so a rename breaks the check rather than the document. It exists
because a hand-authored trace naming a column that does not exist reads as
authoritative — on 2026-09-08 seven rows did, including
`test_results.rationale` for what is actually `result_rationale`.
