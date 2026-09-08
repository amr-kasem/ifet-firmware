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

**Updated 2026-09-08, after the implementation and the live proof.** Seven gaps
closed and one narrowed; the tally below is what the CSV now says.

| State | Rows | Meaning |
|---|---|---|
| `OK` | **23** | Path complete: stored, sourced, mapped to a phase — **and 20 of these round-tripped against the live Testing base** |
| `OK-STORAGE` | 9 | Local column exists and is correct; **nothing populates it yet** (no import path) |
| `OK-JSON-ONLY` | 6 | No Airtable scalar by decision §10.15; travels in the JSON body, which is now built |
| `OK-BY-DECISION` | 3 | Field deliberately not created; the value reaches Airtable another way |
| `OK-BASELINE` | 1 | Pre-existing field, path complete |
| **`GAP-*`** | **15** | **Our unbuilt work — was 18** |
| **`UNMET-*`** | **6** | **A business requirement we cannot satisfy today, and why** |
| `OUT-OF-SCOPE` | 1 | Water infiltration, deferred by contract §0 |

### Closed on 2026-09-08

| Was | Field(s) | What closed it |
|---|---|---|
| `GAP-MAPPER` ×4 | the four Airtable record ids | `mapping._TEST_ATTRS` covers all five test types; identity round-tripped live for every workflow |
| `GAP-FORMAT` | `LabOS Test ID` | one derived allocator, migration `e5f3a71c8d92` normalising existing rows, retest-sharing proven live |
| `GAP-ATOMICITY` | `Attempt Number` | `UniqueConstraint(labos_test_id + trial_number)` plus a retrying allocator; rehearsed on populated tables |
| phase defect | `LabOS Updated At` | `write_phase` was `every`, which no worker dispatches — the field would silently never have shipped |
| marked OK before it existed | `Complete LabOS JSON Response` | `mapping.result_detail()` now builds the §6 body. **This row claimed OK while nothing built it** — the reconciliation was wrong here and the acceptance suite caught it |
| marked OK-BASELINE | `Impact Result` | derived from the numbered impacts, required on every Impact terminal write and previously unpopulated |

### Narrowed

`GAP-CHANNEL` → **`GAP-UPLOADER`** (2 rows, `LabOS Photos`). What is built: one queue
entry per photograph, on its own channel, so a stuck file cannot block a verdict;
and the production sender refuses an attachment with a truthful reason rather
than PATCHing a `photo` object as record fields — which is what it did until
today and which Airtable rejects, parking every photograph permanently. What is
missing: preview generation and the upload itself.

## The remaining 15 gaps, grouped by cause

**No local mirror or programme tables — 5 rows + 1 JSON row.** `Requirement Code`
and `Applicability` are the two fields that decide *which test is required* and
*whether it is required at all*, and neither has a local column. **This is now
the largest gap and everything about pre-fill depends on it.**

**No import path — 2 rows.** `POST /projects/import` is specified in plan §4.2
and unbuilt, so even the columns that exist are never populated from Airtable.
This is why nine rows read `OK-STORAGE` rather than `OK`.

**No validator — 2 rows.** The kind/unit contradiction check the contract
specifies, and the change document claimed, does not exist.

**No correction route — 2 rows.** `corrects_attempt_id` and `correction_reason`
have columns, a property and an envelope mapping, and nothing that sets them.

**No uploader — 2 rows.** Above.

**One type confusion.** `Impact Velocity` is a **target** in Airtable and the
register maps it to `shots.velocity`, the **achieved** value of one impact. A
requirement needs its own column on `missile_impact_tests`. Left as-is, a
pre-fill would overwrite an observation, or a target would be published as an
achievement — the same class of defect the envelope already refuses for
`Max Pressure Achieved`.

**One unreconciled parameter.** `GAUGE_COUNT` is a snapshotted programme
parameter; firmware takes `selectedSensors[]` live at MQTT start, and a mismatch
at start has no defined behaviour (DG6).

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
are empty. What remains unproven end to end is the **inbound** half, because the
mirror and the importer do not exist — and no amount of outbound testing
substitutes for it.
