# What LabOS actually stores — real types, real derivations, real units

**Author:** Abdelrahman · **Date:** 2026-08-31 · **Method:** source of record + live read (§6 pending)
**Trigger:** the Airtable team asked us to specify `Required Value` and the unit per protocol section. This
document is the evidence the answer is built on, so the specification is *derived*, not preferred.

> **Why this exists.** Our first draft answered their question from the write contract — that is, from what we
> had *designed*. That is the weaker answer. LabOS has been running real fenestration tests since before this
> integration, and its database already types every quantity in question. Asking Airtable's schema to match
> columns that already hold real data is a different conversation from asking them to adopt our preferences.

Sources: `ifet-management` `app/data/models.py` (schema), `app/domain/*_pressure_calculator.py` (derivation),
`app/main.py` `create_project` / `update_project` (what is generated from what), `REPORT_DATA_STRUCTURE.md`
(the report contract those feed), and the live `report_db` on `management` (§6).

---

## 1. The finding that changes the ask

**LabOS derives the entire test programme from exactly two numbers.**

`POST /projects` takes `inward_design_pressure` and `outward_design_pressure` — both
`Float, nullable=False`, PSF — and generates, immediately and without further input:

| Generated | How many | From what |
|---|---|---|
| Static stages | **6** | `design_load × [0.75, 0.75, 1.0, 1.0, 1.5, 1.5]`, alternating inward/outward, hold **30 s** fixed |
| Cyclic stages | **8** | high `× [0.5, 0.6, 0.8, 1.0 ǀ 1.0, 0.8, 0.6, 0.5]`, low `× [0.2, 0.0, 0.5, 0.3 ǀ 0.3, 0.5, 0.0, 0.2]`, cycles `[3500, 300, 600, 100 ǀ 50, 1050, 50, 3350]` — first four from **inward** DP, last four from **outward** |
| Water infiltration stage | 1, when requested | `inward_design_pressure × 0.15`, duration **900 s** |

`update_project` recalculates all of it whenever a design pressure changes, skipping any stage already
`finished`. So fourteen-plus pressures, every cycle count and every hold time are **functions of the pair**.

### What follows for their schema — and it makes their job smaller

1. **Airtable does not need to model ranges, sequences, cycle counts or hold times at all.** We do not want to
   read them; we compute them. Their `Cyclic (PSF)` section does not have to express eight
   (cycles, low, high) triples — it cannot, and it should not have to.
2. **The one thing that must be exactly right is the design-pressure pair.** Everything downstream is a
   multiple of it. That is the entire read-side dependency for structural and cyclic work.
3. **Which is precisely the value their extractor corrupted.** Not a coincidence worth glossing over: the
   single number the whole programme is derived from is the number that arrived wrong.

### 1.1 An independent arithmetic proof of the column shift

The proposal's row reads `DP (+) = +60/60` and `Water (PSF) = 9`. Airtable holds `DP (+) = 9` and `Water`
blank.

LabOS computes its water-infiltration stage as **`inward DP × 0.15`**. And `60 × 0.15 = 9`.

So the `9` sitting in Airtable's `DP (+)` column is arithmetically identifiable as the **water** requirement —
15% of the real design pressure, exactly as this lab's own formula produces it. **The shift is now confirmed
twice, by two independent methods:** glyph-coordinate extraction from the PDF (2026-08-23), and the internal
consistency of the numbers themselves against a formula neither team wrote for this purpose. It also explains
why the value is so plausible: `9` is not a random corruption, it is a real requirement from the same row.

**And it sharpens the severity.** A rig driven from `DP = 9` would run the *structural* test at the *water*
pressure — 15% of design — and pass it.

---

## 2. Every field we are asking for already exists as a typed column

This is the table to put in front of them. The left column is not a wish list; it is `models.py`.

### 2.1 Requirements — what LabOS needs to read

| LabOS column | Type | Unit | Nullable | Their `Section Name` | What we ask Airtable for |
|---|---|---|---|---|---|
| `projects.inward_design_pressure` | `Float` | PSF | **NOT NULL** | `DP (+) (PSF)` | `Required Value Inward` (number) |
| `projects.outward_design_pressure` | `Float` | PSF | **NOT NULL** | `DP (+) (PSF)` | `Required Value Outward` (number) |
| *derived* — `static_tests.pressure` | `Float` | PSF | NOT NULL | — | **nothing** — computed from the pair |
| *derived* — `static_tests.duration` | `Integer` | s | NOT NULL | — | **nothing** — fixed 30 s (900 s water) |
| *derived* — `cyclic_tests.cycles` | `Integer` | cycles | NOT NULL | `Cyclic (PSF)` | **nothing** — TAS-203 sequence |
| *derived* — `cyclic_tests.low_pressure` / `high_pressure` | `Float` | PSF | NOT NULL | `Cyclic (PSF)` | **nothing** — computed from the pair |
| `missile_impact_tests.missile` | `String` | — | NOT NULL | `LMI` / `SMI (impacts)` | `Required Value` (count) + `Enum` for missile class |
| `infiltration_tests.pressure` | `Float` | PSF | NOT NULL | `Water (PSF)` | `Required Value` (number, PSF) |

**Two numbers.** That is the whole blocking read-side dependency, and both are `NOT NULL` in LabOS — a
specimen cannot exist without them, which is why a wrong one cannot be worked around.

### 2.2 Results — what LabOS writes back, and its real types

| LabOS column | Type | Unit | Airtable field | Status |
|---|---|---|---|---|
| `test_results.labos_attempt_id` | `String` unique, indexed | — | `LabOS Attempt ID` | ✅ present — **UUID, not `001`** (§10.22) |
| `test_results.labos_test_id` | `String` indexed | — | `LabOS Test ID` | ✅ present |
| `test_results.trial_number` | `Integer` NOT NULL | — | `Attempt Number` | ✅ present — predates the integration |
| **`test_results.corrects_attempt_id`** | **`String` indexed** | — | `Corrects Attempt ID` | ❌ **absent — §10.14** |
| **`test_results.correction_reason`** | **`Text`** | — | `Correction Reason` | ❌ **absent — §10.14** |
| **`test_results.testing_start_date`** | **`DateTime(timezone=True)`** | UTC | `Test Date` | 🟡 collapsing to one field — §10.13 |
| **`test_results.testing_end_date`** | **`DateTime(timezone=True)`** | UTC | — | ❌ **absent — §10.13** |
| `test_results.measured_value` | `Float` | per `unit` | `Measured Value` | ✅ present |
| `test_results.max_pressure_achieved` | `Float` | PSF | `Max Pressure Achieved` | ✅ present |
| `test_results.deflection_value` | `Float` | in | `Deflection Value` | ✅ present |
| `test_results.cycles_required` / `cycles_completed` | `Integer` | cycles | — | ❌ absent — JSON valve |
| `test_results.required_value` / `required_unit` | `Float` / `String` | — | — | ❌ absent — §10.15 |
| `test_results.result_detail` | **`JSON`** | — | `Complete LabOS JSON Response` | ✅ present |
| `test_results.required_params` | **`JSON`** | — | — | LabOS-side snapshot of what drove the test |

> **The point to make to them:** `corrects_attempt_id` is not a hypothetical. It is a `String` column, indexed,
> already migrated, already written by our envelope. What is missing is a destination for it.

### 2.3 The deflection finding — their JSON shape cannot hold our data

`deflections` stores **three** measurements per gauge, all `Float, NOT NULL`, in inches:

| Column | Meaning |
|---|---|
| `deflection_gauge` | `String` NOT NULL — the gauge identity |
| `max_deflection` | peak deflection under load |
| `permanent_deflection` | permanent set after release |
| `recovery` | recovered deflection |

Their sample row's JSON carries **one** number per gauge:
`"gauges": [ {"gauge": "G1", "deflection": 0.18, "unit": "Inches"} ]`.

**Permanent set is not a nicety — it is a required column of the IFET report** (`REPORT_DATA_STRUCTURE.md`,
static and cyclic sections both show *Deflection (in.)* and *Permanent Set (in.)*). So whichever JSON shape
wins (§10.25), it must carry all three per gauge. This converts §10.25 from a stylistic question into a
completeness one, and gives us a concrete reason to ask rather than a preference.

---

## 3. The real unit inventory — and a correction to our own list

Units in actual use across the LabOS model, read off the columns and the report contract:

| Quantity | Unit | Where |
|---|---|---|
| Pressure — design, static, cyclic, infiltration | **PSF** | `projects`, `static_tests`, `cyclic_tests`, `infiltration_tests` |
| Deflection — max, permanent set, recovery | **in** | `deflections` |
| Hold / stage duration | **s** | `static_tests.duration` (30, 900) |
| Infiltration duration | **minutes** | `infiltration_tests.duration` — `Float` |
| Air leakage | **cfm/ft²** | `infiltration_tests.leakage` |
| Cycle count | **cycles** | `cyclic_tests.cycles` |
| Impact count | **impacts** | `LMI` / `SMI` sections |
| Missile weight | **kg** | `missile_impact_tests.missile_weight` |
| Missile velocity | **m/s** | `shots.velocity` |
| Impact area | **m²** | `shots.area` |

**Our contract §4.4 list was `PSF · PSI · in · mm · lbf · N · cycles · s` — which misses five units the lab
actually measures in**, and includes two (`lbf`, `N`) that nothing in the model currently produces. Worth
correcting before we hand anyone a vocabulary.

The right resolution is not one giant option list, it is **three lists scoped to where they are used**:

| Field | Option set | Why this set |
|---|---|---|
| `Required Unit` (Protocol Sections) | `PSF` · `in` · `s` · `cycles` · `impacts` | requirements are only ever pressures, deflection limits, holds or counts |
| `Unit` (raw table, `Measured Value`) | `PSF` · `PSI` · `in` · `mm` · `cycles` · `s` · `impacts` | the governing measured result |
| `Deflection Unit` | `in` · `mm` | unchanged |

**`kg`, `m/s`, `m²`, `cfm/ft²` and `minutes` deliberately do not get columns.** They belong to impact and
infiltration detail, which §5.1 already routes into `Complete LabOS JSON Response` with the unit declared
per value. If Airtable later wants air leakage as a first-class field, that is when `cfm/ft²` earns a column —
worth flagging to them, not worth asking for now.

This is also the concrete answer to §10.24: `in`, not `Inches`, and **as a single select**, so the divergence
becomes an error instead of two spellings living in one free-text column.

---

## 4. What this changes in our answer to them

| Our 2026-08-31 draft said | The evidence says | Net effect |
|---|---|---|
| Five typed fields incl. `Requirement Kind` | Still right, but the **`Directional Pair` case is the only one that carries the blocking dependency** | Sharpen the ask: two numbers, in PSF, on the DP section |
| "If a real range appears we'll add Min/Max" | **No range is ever read.** Cyclic low/high are derived from the pair | Withdraw the range question entirely — it reduces their work |
| Unit list of eight | Five units missing, two unused; scope differs per field | Three scoped lists (§3) |
| §10.25 is "whose shape wins" | Their shape **cannot carry permanent set**, which the IFET report requires | Reframe as completeness, not style |
| Typed fields would "partly contain" the shift | `60 × 0.15 = 9` — the shift is provable from arithmetic alone | Add it as independent corroboration |

---

## 5. What we are *not* claiming

- **This does not reduce the extractor fix.** Deriving fourteen stages from two numbers makes a wrong pair
  worse, not safer: the error is multiplied through every stage. Typed fields catch a *shape* mismatch, never
  a plausible wrong number in the right shape.
- **Hold times are fixed in LabOS today (30 s / 900 s), not read from anywhere.** If a protocol ever specifies
  a different hold, that is a LabOS change and a new read-side field — out of scope for this exchange, and we
  should not imply we consume one.
- **`lbf` / `N` appear in our contract but nothing produces them.** Left in the vocabulary would be a claim we
  cannot back with data.

---

## 6. Live value ranges — pending

The queries are written and read-only: `scratchpad/probe-real-data.sql` (row counts and the alembic head,
design-pressure ranges and how many pairs are asymmetric, real static factors and holds, the cyclic sequence
as stored, deflection ranges across all three measurements, infiltration and impact units, retest frequency,
and the live `information_schema` types for `test_results`).

They must be run by hand — the auto-mode classifier blocks `docker exec` against a production node, correctly.

**What each answer is for, so the numbers are not collected idly:**

| Query | The claim it evidences |
|---|---|
| asymmetric design-pressure pairs | that inward ≠ outward happens in real jobs — so `+60/60` collapsing to one number is a real data loss, not a theoretical one |
| static factors + holds as stored | that §1's derivation is what production actually contains, not just what the code says |
| deflection ranges, all three columns | that permanent set is populated in real rows — §2.3's argument |
| retest frequency (attempts per test) | how often the retest/correction distinction actually fires — the §10.14 argument, quantified |
| `information_schema` on `test_results` | which P1 columns are live vs. pending deploy |

Fill this section in, then re-check §2 and §3 against it before the numbers go into a message.
