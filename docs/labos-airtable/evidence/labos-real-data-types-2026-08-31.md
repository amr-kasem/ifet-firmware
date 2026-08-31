# What LabOS actually stores — real types, real derivations, real units

**Author:** Abdelrahman · **Date:** 2026-08-31 · **Method:** source of record + live read of production (§6, run 2026-08-31)
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
| Infiltration duration | **s** (not minutes — see §7.2) | `infiltration_tests.duration` — `Float` |
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

**`kg`, `m/s`, `m²` and `cfm/ft²` deliberately do not get columns.** They belong to impact and
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

## 6. Live value ranges — production, read 2026-08-31

Read-only, against `report_db` on `management`. Queries kept verbatim as `probe-real-data-2026-08-31.sql` beside this file. `alembic_version` = **`3a65a83e0463`** — unchanged, so P1 is
still undeployed (§7.1).

| Table | Rows |
|---|---|
| `projects` | **78** |
| `static_tests` | 501 |
| `cyclic_tests` | 626 |
| `test_results` | **637** (was 623 on 2026-08-23 — production is live and accumulating) |
| `deflections` | 1082 |
| `infiltration_tests` | 37 |
| `missile_impact_tests` / `shots` | 39 / 114 |

### 6.1 The headline number — asymmetric design pressures are the norm, not an edge case

| | |
|---|---|
| Projects | 78 |
| Inward design pressure | **5 → 395.01 PSF** |
| Outward design pressure | **3 → 491.05 PSF** |
| **Projects where inward ≠ outward** | **36 — 46% of all real jobs** |

**Nearly half of every job this lab has run has a different inward and outward design pressure.** So
`+60/60` collapsing into a single `Required Value` is not a theoretical loss of fidelity — it is a loss of real
data in 46% of cases, and the two halves are not recoverable from each other.

It also shows why `9` was individually plausible: real design pressures span 3 → 491 PSF. Nothing about a `9`
looks wrong.

### 6.2 The derivation, confirmed to full float precision

Every factor in §1 reproduces the live maxima **exactly** — not approximately:

| Live value | Derivation | Match |
|---|---|---|
| `static_tests` max inward `592.5077713931231` | `395.00518092874876 × 1.5` | **exact** |
| `static_tests` max outward `736.5791671374297` | `491.0527780916198 × 1.5` | **exact** |
| `static_tests` min inward / outward `3.75` / `2.25` | `5 × 0.75` / `3 × 0.75` | **exact** |
| cyclic inward, 3500 cycles, high `197.50259046437438` | `× 0.5` | **exact** |
| cyclic inward, 600 cycles, high `316.004144742999` | `× 0.8` | **exact** |
| cyclic inward, 300 cycles, high `237.00310855724925` | `× 0.6` | **exact** |
| cyclic inward, 100 cycles, high `395.00518092874876` | `× 1.0` | **exact** |
| cyclic outward, 3350 cycles, high `245.5263890458099` | `× 0.5` | **exact** |
| cyclic outward, 1050 cycles, high `392.84222247329586` | `× 0.8` | **exact** |
| cyclic outward, 50 cycles, high `491.0527780916198` | `× 1.0` | **exact** |
| `static_tests` holds | 30 s throughout, **900 s** present on inward only | the water stage |

Cycle counts as stored are exactly `[3500, 300, 600, 100]` inward and `[3350, 1050, 50, 50]` outward — the
`50` appearing on 156 rows because two of the eight stages carry it. `8 × 78 = 624` of the 626 cyclic rows are
preset.

**So §1 is not a reading of the source. It is arithmetically verifiable in 1127 production rows.** That is the
form of the claim to make to the Airtable team: not "our code does this", but "this is what the lab's data
is".

### 6.3 Retests, quantified — the §10.14 argument stops being theoretical

| | Tests with attempts | Tests with **more than one** attempt | Max attempts |
|---|---|---|---|
| Static | 255 | **41** | 2 |
| Cyclic | 252 | **65** | 3 |
| **Total** | **507** | **106 — 21%** | **3** |

**One test in five already has more than one attempt, and some have three.** Today nothing in the data says
whether attempt 2 was a second physical test or a correction of a mis-recorded first — because
`corrects_attempt_id` has nowhere to land. This is the number to put in front of them: the ambiguity they are
proposing to accept already applies to 106 real tests.

`test_results.result` is `191 true · 84 false · 362 NULL`. The NULL majority is consistent with contract §4.3
— `Test Result` is omitted while an attempt is not terminal — and it means a required `Test Result` on every
row would be wrong.

### 6.4 The rest, briefly

- **Infiltration** — `Air Infiltration` (13) and `Water Infiltration` (24). Pressure 17.8 → 74.3 PSF.
  Leakage **0.25 → 4.98 cfm/ft²**, plausible for air leakage and consistent with the report contract.
- **Missile impact** — three real missile classes with fixed masses: `2x4 Lumber` **9 kg**,
  `Large Missile` **15 kg**, `Steel Ball` **2 kg**. Shots: velocity **15.3 → 49.9 m/s**, area
  **0.50 → 2.47 m²**, 72 of 114 passed. So `Impact Result` free text (§10.5) is backed by a small, stable set
  of missile classes — worth knowing if an option list is ever wanted.
- **Manual (non-preset) stages exist.** 10 of 501 static rows carry a blank `pressure_factor`, and 2 of 626
  cyclic rows hold hand-entered counts (`6` and `500`). See §7.3.
- **A real `0` measurement exists** — one static stage at 0 PSF with a 0 s hold. Contract §5's rule that `0`
  is data rather than a blank is not hypothetical.

---

## 7. What the live read corrected — including in this document

Three claims changed on contact with production. Recording them because two of them had already reached the
draft reply.

### 7.1 "The column is already migrated" — wrong, and it was in the reply

Live `test_results` holds **five columns**: `id`, `trial_number`, `result`, `note`, `image_path`. None of the
P1 attempt columns — `labos_attempt_id`, `corrects_attempt_id`, `correction_reason`, the datetimes, the
measurements — exist in production. `alembic_version` is still `3a65a83e0463`.

They are **built, tested and migrated on `feature/labos-airtable`, and not deployed.** The draft reply said
"already migrated", which is true of the branch and false of production. **Corrected in the reply** to "built
and tested, waiting on a deploy window", which is both accurate and still makes the point that the ask is for
a destination rather than a feature.

This is exactly the class of statement that would be indefensible if they checked, and the reason the standing
rule is that the node is ground truth rather than the repo.

### 7.2 `infiltration_tests.duration` is seconds, not minutes

`REPORT_DATA_STRUCTURE.md` annotates it `# minutes`. Live values run **321 → 1691**. As minutes that is 5 to
28 hours for an infiltration test; as seconds it is 5 to 28 minutes, which is the real procedure. **The
docstring is wrong and the data is right.** §3's unit inventory is corrected, and `minutes` is removed from
the unit vocabulary entirely — it was never a real unit here.

### 7.3 The derivation claim needs one honest qualifier

98% of stages are preset and derived (624/626 cyclic, 491/501 static), but **operators can and do add ad-hoc
stages** — two cyclic tests with hand-entered cycle counts, ten static tests with a blank `pressure_factor`,
one of them at 0 PSF.

That does not weaken anything said to Airtable: **the pair is still all they need to supply**, and an
operator-authored stage is a LabOS-side act with no Airtable requirement behind it. But "LabOS derives the
entire programme" should be stated as *the preset programme*, or a fair reader will find the counterexample.

### 7.4 ⚠️ A data-quality problem of our own — deflection values

Do **not** quote deflection ranges to the Airtable team. Live values:

| Column | Min | Max |
|---|---|---|
| `max_deflection` | **−1280.91** | **1288.86** |
| `permanent_deflection` | **−1274.17** | 1284.13 |
| `recovery` | 0.3 | **60** |

**These are not inches.** A fenestration specimen does not deflect 1288 inches, and a 60-inch recovery is not
physical either. Either some rows hold raw gauge counts rather than converted inches, or a scale factor is
missing on some path — the same class of defect as the PSI→PSF sensor bug of 2026-07-09, which is the worked
example in contract §3.1.

`deflection_gauge` is also inconsistent free text: **20 distinct labels in two naming schemes** — `1-1` … `2-8`
(16 labels) and `Gauge 1` … `Gauge 4`. So any JSON keyed on gauge identity inherits that inconsistency.

**Consequences, and they are ours not theirs:**

1. **The §2.3 argument stands** — deflection is structurally three measurements per gauge, and permanent set is
   a required column of the IFET report. That claim comes from the schema and the report contract, not from
   the values, so it is unaffected.
2. **The values are not evidence of anything yet.** Nothing in the message to Airtable should cite a deflection
   range or claim the unit is inches for existing rows.
3. **This is a new LabOS-side investigation**, not an integration item: which rows are affected, whether a
   scale factor is missing, and whether any of it reached a published report. It belongs on the R-week plan,
   and it must be understood **before** LabOS writes `Deflection Value` + `Deflection Unit` to Airtable — or
   we export the problem into someone else's base and it becomes certification evidence there.
4. **Normalise `deflection_gauge`** before the JSON shape is agreed, or the two naming schemes become two
   shapes in Airtable's long-text field.
