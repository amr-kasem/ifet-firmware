# LabOS → Airtable Write Contract — `v0.3 DRAFT`

**Owner:** LabOS (Abdelrahman) · **Date:** 2026-08-22 · **Supersedes:** contract `v0.2 DRAFT`
**Counterparty doc:** *IFET Phase 2 · LabOS × Airtable API Integration Guide* **v2** (Airtable team, 2026-08-17)
**Target table:** `LabOS Raw Data Table` — `tblnc9SsbXU0C0FWh`, in `LabOS Testing Base` (`app4oXS3Kd5IKWgJ7`)
**Ratifies to `v1.0`** when §10's open items close. `Schema Version` on the wire tracks *this* document.

> **Scope.** This document specifies exactly what LabOS sends to Airtable and under what guarantees. It does
> **not** cover the read direction (requirements-IN) beyond §9, and it does not cover Airtable's internal
> automations or roll-ups — those are the Airtable team's, by agreement.

---

## 0. What changed in `v0.3`, and the environment it targets

`v0.3` folds in the Airtable team's **v2 integration guide (2026-08-17)**. That document moved the ground
under `v0.2` in four ways, so this revision is not cosmetic.

**Resolved by v2**

- **The writable table now lives in its own base** (§10.4 — closed). Two environments, both named below.
- **Real table IDs published** for all nine tables. LabOS no longer guesses at names.
- **Four of the eleven requested fields were granted** — `Schema Version`, `Max Pressure Achieved`,
  `Deflection Unit`, and the extensibility valve, shipped under their name `Complete LabOS JSON Response`.
- **The leaked PAT is gone.** v2 deliberately excludes tokens; delivery is out-of-band.

**Introduced by v2 — the reason this is a version bump and not an edit**

- `Testing Start Date` + `Testing End Date` were **collapsed into a single `Test Date`** (§10.13).
- `Test Name`, the correction fields, `Abort Reason` and the wall snapshot block are **absent** from their
  raw table (§10.14, §10.15).
- Their worked example writes `"Test Result": "Passed"`; this contract specifies `Pass` (§10.16).

**Still unanswered, and now the critical path:** the read-side parameter structure (§9.1, §10.3). v2 §6 step 5
says only *"perform testing in LabOS using the requirement values read from Airtable"* and gives no field
specification for Protocol Sections. **This gates W3.**

### 0.1 Environments and table IDs

| Environment | Base name | Base ID | LabOS PAT scopes (per v2 §2) |
|---|---|---|---|
| **Testing** (build here) | LabOS Testing Base | `app4oXS3Kd5IKWgJ7` | `data.records:read`, `data.records:write`, `schema.bases:read`, `schema.bases:write` |
| **Production** (gated) | IFET Airtable Base | `app0OCunbmuXl7Hc9` | `data.records:read`, `data.records:write`, `schema.bases:read` |

| Table | Table ID | LabOS access |
|---|---|---|
| IFET Projects | `tblLYcRC7q6Srjfk3` | READ |
| Mock-Ups/Specimens | `tblcrGv0WJn6FTTGO` | READ |
| Tests Protocols | `tblutO1Q8TNC4BLk0` | READ |
| Protocol Sections | `tblqpvuJlSdkeS9PS` | READ — the level results attach to |
| **LabOS Raw Data Table** | **`tblnc9SsbXU0C0FWh`** | **WRITE — the only writable surface** |
| Walls & Positions | `tblVUvcSPAoneG26W` | none |
| Wall Scheduling/Reservation | `tblYjF1AApzmRDMrY` | none |
| Wall Positions Calendar | `tbly6A3GB1GHdGocq` | none |
| Back Charges | `tbl0f2YxS3FHJ1dTD` | none |

> **The read-only promise is not token-enforced.** Airtable PAT scopes are **per base, not per table**, so the
> testing PAT carries `data.records:write` — and `schema.bases:write` — across *every* table in
> `app4oXS3Kd5IKWgJ7`, including the four hierarchy tables. Nothing on the Airtable side will stop a stray
> write. **LabOS therefore enforces it client-side:** the API client hard-codes a write allowlist of exactly
> `tblnc9SsbXU0C0FWh` and raises on any attempt to mutate another table. This is a LabOS obligation created by
> v2's design, not an Airtable one.

> **Production automation is OFF by design.** Per v2 §2 and §7, Airtable-side processing in the production base
> stays disabled until the Airtable team formally enables it after acceptance testing. LabOS must not treat a
> successful production write as an integrated result until that switch is thrown.

### 0.2 Verify before trusting this section

Every ID above is transcribed from a PDF. v2 §2 itself says to confirm live IDs against the schema endpoint
before any production cutover. The probe harness (§10.11) does exactly that and diffs the live schema against
this document — so the first thing that happens when the PAT arrives is that these tables get checked, not
assumed.

---

## 1. Separation of concerns (agreed both sides)

| Domain | Owner | Consequence |
|---|---|---|
| Projects, Mock-Ups, Protocols, Sections | **Airtable** | LabOS reads only. Never written by LabOS. |
| Walls, wall positions, capacity, reservations, scheduling | **Airtable** | LabOS reads and **snapshots** into results (§4). Never written back. |
| Project / Mock-Up / Protocol status roll-ups | **Airtable** (automations / Make) | LabOS writes **one attempt row** and nothing else. |
| Test execution, measurement, pass/fail determination | **LabOS** | Airtable does not compute results and never controls equipment. |
| `LabOS Raw Data Table` rows (`tblnc9SsbXU0C0FWh`) | **LabOS writes, Airtable consumes** | The only writable surface (§0.1). |
| Reports, Excel exports, photos | **LabOS hosts**, Airtable links | Links, not attachments (§7). |

**Invariant:** no field is written in both directions. Requirements flow in; results flow out.

---

## 2. Identity and idempotency

| Key | Type | Minted by | Stability |
|---|---|---|---|
| `LabOS Test ID` | text (UUID) | LabOS, at test creation | One per (protocol section × mock-up) test instance. Groups attempts. |
| **`LabOS Attempt ID`** | text (UUID) | LabOS, at attempt creation | **The unique key. The upsert merge key.** Never reused, never regenerated — not on retry, not after a reboot, not on offline-queue replay. |
| `Attempt Number` | number | LabOS | 1-based, monotonic within a `LabOS Test ID`. Display/ordering only — *not* an identity key. |

**Idempotency rule.** Every write is an **upsert on `LabOS Attempt ID`**:

```http
PATCH https://api.airtable.com/v0/app4oXS3Kd5IKWgJ7/tblnc9SsbXU0C0FWh
Authorization: Bearer {PAT}
Content-Type: application/json

{
  "performUpsert": { "fieldsToMergeOn": ["LabOS Attempt ID"] },
  "records": [ { "fields": { "LabOS Attempt ID": "…", … } } ]
}
```

Requirements this places on the Airtable side:
- `LabOS Attempt ID` must be a **plain text field** — computed fields (formula/rollup/lookup) cannot be used
  in `fieldsToMergeOn`.
- Airtable cannot enforce uniqueness; **LabOS guarantees it** (UUID minted once, persisted locally before the
  first send attempt). This is what makes a timed-out retry safe: the retry merges onto the same row instead
  of creating a second one.
- Batch limit **10 records per request**; LabOS batches at most 10.

**Why the ID is minted before the first send:** if it were assigned on success, a request that times out
*after* Airtable committed it would be indistinguishable from a failure, and the retry would duplicate. The
attempt ID exists in the LabOS database before any network call — always.

---

## 3. Attempt lifecycle and immutability

```
        (attempt created locally)
                  │
                  ▼
          In Progress ──────────────┐
                  │                 │
                  ▼                 ▼
            Completed            Aborted        ← TERMINAL. Record is final.
                  │                 │
                  └────────┬────────┘
                           ▼
              correction? → NEW attempt row, Corrects Attempt ID = <old>
```

- LabOS writes at most **two** upserts per attempt: one on start (`In Progress`, partial payload) and one at
  terminal state (`Completed` / `Aborted`, full payload). The start write is what gives Airtable live
  visibility; both carry the same `LabOS Attempt ID`, so the second merges onto the first.
- **Once terminal, that attempt ID is never written again by LabOS.** Enforced in the sync worker, not by
  convention: a terminal attempt is removed from the writable set.
- **Corrections are new rows.** A corrected result is a *new* `LabOS Attempt ID` with a new `Attempt Number`,
  carrying `Corrects Attempt ID` = the superseded attempt and `Correction Reason` = why. Airtable's automation
  may then mark the old row `Superseded` and exclude it from roll-ups; LabOS never writes `Superseded`.

### 3.1 Retest vs. correction — two different things that look identical without the reference field

This is the distinction the `Corrects Attempt ID` field exists to carry, and getting it wrong corrupts every
roll-up downstream.

| | **Retest** | **Correction** |
|---|---|---|
| What happened physically | The specimen **was tested again**. Two real test events. | **One** test event, recorded wrongly. |
| Typical cause | First attempt failed, or was aborted on an equipment fault, and the specimen was re-run. | Wrong mock-up selected, wrong operator, a unit mix-up, pass/fail computed against the wrong design pressure, or a gauge later found out of calibration. |
| Rows in Airtable | 2 rows, **both valid data** | 2 rows, **only the second is true** |
| `Attempt Number` | increments (1 → 2) | increments (1 → 2) |
| `Corrects Attempt ID` | **absent** | **set to the superseded attempt** |
| `Retest Required` on the earlier row | `true` | irrelevant — the earlier row is not a real result |
| How roll-ups must treat it | count both attempts; the specimen was tested twice | count only the correction; the specimen was tested **once** |

`Attempt Number` alone cannot distinguish them — attempt 2 is ambiguous. Without `Corrects Attempt ID`, a
mis-recorded test and a genuine second test are indistinguishable in the data, so any roll-up that counts
attempts, computes a pass rate, or reports "tests performed" is wrong in one of the two cases.

**Worked example (a real class of failure from this project).** On 2026-07-09 a rig's pressure sensors were
converting PSI→PSF with a scale factor; before that fix, a reading logged as `40` was in the wrong unit. Say an
attempt had already been written:

```
attempt a1 · Attempt Number 1 · Completed · Pass · Measured Value 40 · Unit PSF   ← wrong unit
```

- **Editing the row** destroys the evidence. A report has already gone out citing 40 PSF, and afterwards
  nothing in the base shows that the number changed, when, or why. For a testing lab whose output is
  certification evidence, that is the failure mode to design against.
- **A bare new row** leaves two contradictory Completed results for the same test with no explanation, and the
  roll-up counts both.
- **A new row with the reference** is the only complete answer:

```
attempt a2 · Attempt Number 2 · Completed · Pass · Measured Value 5760 · Unit PSF
           · Corrects Attempt ID  = a1
           · Correction Reason    = "sensor unit misconfiguration (PSI logged as PSF);
                                     value re-derived from the raw log, sensor re-scaled 2026-07-09"
```

Airtable's automation sees `Corrects Attempt ID`, marks `a1` `Superseded`, and excludes it from roll-ups.
Both rows survive, the reason is on the record, and an auditor can reconstruct exactly what happened.

**Corrections chain.** If a correction is itself wrong, the next one references *it* (`a3` → `a2` → `a1`), and
the authoritative result is the head of the chain — the row no other row supersedes. That's why this is a
reference field rather than a boolean "corrected" flag: a flag cannot express a chain, and cannot say which
row is current.

**Why LabOS cannot just do this itself.** The old row is locked, so LabOS is not permitted to touch it — which
means LabOS cannot mark it superseded. It can only write the new row *stating* what it supersedes. Marking the
old row is Airtable's automation, on Airtable's side of the boundary. That split is deliberate: the writer of
a record never gets to retroactively alter one.
- **Honest limitation:** a write-scoped PAT can technically PATCH a terminal row. The lock is a LabOS
  invariant plus Airtable revision history for audit — not an API permission. If Airtable wants defence in
  depth, an automation can revert edits to rows whose `Test Status` is terminal.

---

## 4. Field envelope

Legend — **R** always required · **C** conditionally required (see §5) · **O** optional ·
**S** snapshot at test time, never live.

**v2 column** — status in the Airtable team's `LabOS Raw Data Table` as published 2026-08-17:
✅ present under this name · ✏️ present under **a different name — theirs is the wire name** ·
❌ **not present**, requested from the Airtable team.

> Names in the **Field** column are LabOS's canonical vocabulary. Names in the **v2** column are what actually
> goes on the wire today. Where they differ, the client maps; it never sends the LabOS name.

### 4.1 Identity & linkage
| Field | Type | Req | v2 | Notes |
|---|---|---|---|---|
| `Airtable Project ID` | text | R | ✅ | `rec…`. Plain text vs. link-to-record still open (§10.2). |
| `Airtable Mock-Up ID` | text | R | ✏️ **`Airtable Mockup ID`** | Their spelling drops the hyphen. |
| `Airtable Protocol ID` | text | R | ✅ | `rec…` |
| `Airtable Section ID` | text | R | ✅ | `rec…` — the level results attach to. |
| `LabOS Test ID` | text | R | ✅ | |
| `LabOS Attempt ID` | text | R | ✅ | **merge key** |
| `Attempt Number` | number | R | ✅ | |
| `Schema Version` | text | R | ✅ **granted in v2** | Value = this contract's version: `0.3` now, `1.0` on ratification. |
| `Corrects Attempt ID` | text | C | ❌ | **Blocking — §10.14.** Without it §3.1 has no wire representation. |
| `Correction Reason` | long text | C | ❌ | **Blocking — §10.14.** Required when `Corrects Attempt ID` present. |

### 4.2 Wall / reservation snapshot (**S** — as of test time, by design)
| Field | Type | Req | v2 |
|---|---|---|---|
| `Airtable Wall ID` | text | C | ❌ |
| `Wall Name` | text | C | ❌ |
| `Airtable Wall Position ID` | text | C | ❌ |
| `Wall Position Name` | text | C | ❌ |
| `Wall Reservation Start Date` | date (ISO 8601 UTC) | C | ❌ |
| `Wall Reservation End Date` | date (ISO 8601 UTC) | C | ❌ |

Required when the attempt occupied a wall position (all hardware tests do). If Airtable later moves the
reservation, this row keeps the old values **and must not be corrected** — it records where the test happened.

**The whole block is absent from v2**, which answers §10.9 implicitly as *no*. LabOS is not pressing this —
wall provenance is recoverable from Airtable's own reservation history — but §10.15 asks them to confirm that
is a deliberate decision rather than an omission, because after the fact the reservation may have moved.

### 4.3 Descriptors
| Field | Type | Req | v2 | Options |
|---|---|---|---|---|
| `Test Name` | text | R | ❌ | **§10.15.** Echoes the Protocol Section's `Test Name` verbatim. Without it every row is human-readable only by `rec…` ID. |
| `Test Type` | single select | R | ✅ | `Static Load` · `Cycles` · `Impact` · `Forced Entry` · `ANSI Z97.1` |
| `Test Status` | single select | R | ✅ | `In Progress` · `Completed` · `Aborted` (LabOS writes only these) |
| `Test Result` | single select | C | ✅ ⚠️ | `Pass` · `Fail` · `Inconclusive`. **Their v2 example sends `"Passed"` — §10.16.** Omitted while `In Progress`; required when `Completed`. |
| `Abort Reason` | single select | C | ❌ | **§10.15.** `Specimen Failure` · `Equipment Fault` · `Operator Stop` · `Power/Comms Loss` · `Other`. Required when `Aborted`; without it an aborted row carries no cause. |

### 4.4 Measurements
| Field | Type | Req | v2 | Notes |
|---|---|---|---|---|
| `Measured Value` | number | C | ✅ | The governing measured result — held/target pressure for Static Load. Unit per `Unit`. |
| `Unit` | single select | C | ✅ | `PSF` · `PSI` · `in` · `mm` · `lbf` · `N` · `cycles` · `s`. Required whenever `Measured Value` is sent. Pressure is **PSF**. |
| `Max Pressure Achieved` | number (PSF) | C | ✅ **granted in v2** | Peak pressure reached. Distinct from `Measured Value`; for a failure test this *is* the result. |
| `Deflection Value` | number | C | ✅ | Governing (maximum) deflection. Per-gauge detail goes in the JSON field. |
| `Deflection Unit` | single select | C | ✅ **granted in v2** | `in` · `mm`. Required whenever `Deflection Value` is sent. |
| `Required Value` | number | C · **S** | ❌ | §10.15. Snapshot of the section's requirement. |
| `Required Unit` | single select | C · **S** | ❌ | §10.15. Same option list as `Unit`. |
| `Cycles Required` | number | C | ❌ | §10.15. Cyclic tests. |
| `Cycles Completed` | number | C | ❌ | §10.15. Cyclic tests. |
| `Impact Result` | text / single select | C | ✅ | Impact tests. Option set still TBD (§10.5) — the probe answers it. |
| `Result Detail (JSON)` | long text | C | ✏️ **`Complete LabOS JSON Response`** — **granted in v2** | Test-type-specific structure, §6. **The extensibility valve:** new test types and new measurements land here without an Airtable schema change. Their name is the wire name. |

> The granted JSON field is the most valuable thing v2 gave us. Six of the seven fields still marked ❌ above
> are *recoverable* through it — LabOS can carry `Required Value`, `Cycles Required/Completed` and the wall
> snapshot inside the JSON payload without another schema round-trip. It does **not** rescue
> `Corrects Attempt ID`: Airtable automations have to branch on that field, and a value buried in long text is
> not something a roll-up can filter or link on. That is why §10.14 is blocking and §10.15 is not.

### 4.5 Timing, people, disposition
| Field | Type | Req | v2 | Notes |
|---|---|---|---|---|
| `Testing Start Date` | datetime | R | ❌ **collapsed** | ISO 8601 **UTC**. See §10.13. |
| `Testing End Date` | datetime | C | ❌ **collapsed** | Required when terminal. See §10.13. |
| — *their* `Test Date` | date/datetime | — | ✅ **new in v2** | v2 replaces both fields above with this single one. LabOS writes the **start** instant into it pending §10.13. |
| `Operator Name` | text | R | ✅ | |
| `Retest Required` | checkbox | R | ✅ | Explicit `true`/`false` on terminal writes — **omission must not be read as `false`**. |
| `Testing Continued` | single select | C | ✅ | `Continued` · `Stopped`. Required when terminal. |
| `Notes` | long text | O | ✅ | Operator free text. Never load-bearing for automations. |

### 4.6 Artifacts & metadata
| Field | Type | Req | v2 | Notes |
|---|---|---|---|---|
| `Photos` | URL list / long text | O | ✅ | Newline-separated LabOS-hosted URLs. Field *type* still unconfirmed (§10.1) — the probe answers it. |
| `Excel File Link` | URL | O | ✅ | LabOS-hosted. |
| `Report Link` | URL | O | ✏️ **`LabOS Report Link`** | LabOS-hosted. |
| `LabOS Created At` | datetime | R | ✅ | Attempt creation, ISO 8601 UTC. |
| `LabOS Updated At` | datetime | R | ✅ | Last LabOS-side mutation. Doubles as the arrival/staleness signal (§8). |
| `Test Rig` | single select | O | ❌ | §10.15. `System 1` · `System 2`. Traceability. |
| `LabOS Version` | text | O | ❌ | §10.15. Build that produced the numbers. Metrology traceability. |
| `Result Rationale` | long text | O | ❌ | §10.15. How pass/fail was determined, e.g. `max deflection 0.42 in ≤ L/175 limit 0.55 in`. |
| ~~`Sync Status`~~ | — | — | — | **Withdrawn by LabOS** — see §8. Correctly absent from v2. |

---

## 5. Blank, null, and conditional-requirement rules

**Replaces their §5 in full.** Airtable's REST API rejects `""` on number and date fields
(`422 INVALID_VALUE_FOR_COLUMN`) and on single-selects unless `""` is a real option, so "send `\"\"`" is not
implementable as a general rule.

| Intent | Wire form | LabOS uses it? |
|---|---|---|
| Field does not apply / no value | **omit the key entirely** | ✅ always |
| Explicitly clear an existing cell | `null` | ❌ never (records are immutable once terminal) — reserved so the meaning stays unambiguous |
| Empty string | `""` | ❌ never |
| `"N/A"`, `"Not Available"`, `"-"` | sentinel text | ❌ never |
| A genuine zero measurement | `0` | ✅ **`0` is data, not a blank.** A 0 PSF reading is sent as `0`. |

- Required identifiers (§4.1) and the always-required set are never omitted.
- Booleans are always explicit on terminal writes (`Retest Required`).
- LabOS never invents a select option at runtime. An unmapped value is a **contract error**, logged and
  surfaced in the LabOS UI as `Retry Required`, not coerced into free text.
- **To be verified on the sandbox base and appended here:** exact 422 behaviour per field type, and whether
  `typecast: true` is needed for select fields. Evidence, not assumption — this table gets a verification
  column before `v1.0`.

### 5.1 Required-by-test-type matrix

| Field | Static Load | Cycles | Impact | Forced Entry | ANSI Z97.1 |
|---|---|---|---|---|---|
| `Measured Value` + `Unit` | ✅ | ✅ | — | ○ | ○ |
| `Max Pressure Achieved` | ✅ | ✅ | — | — | — |
| `Deflection Value` + `Deflection Unit` | ✅ | ✅ | — | — | — |
| `Cycles Required` / `Cycles Completed` | — | ✅ | — | — | — |
| `Impact Result` | — | — | ✅ | — | — |
| `Test Result` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Result Detail (JSON)` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Photos` | ○ | ○ | ✅ | ✅ | ✅ |
| Wall snapshot (§4.2) | ✅ | ✅ | ✅ | ○ | ○ |
| `Required Value` + `Required Unit` | ✅ | ✅ | ○ | ○ | ○ |

✅ required when `Completed` · ○ optional · — omitted (key absent)

> **Reading this matrix against v2.** Five rows name fields that do not yet exist in their raw table:
> `Cycles Required` / `Cycles Completed`, `Required Value` / `Required Unit`, and the wall snapshot. Until
> §10.15 is answered, LabOS satisfies those rows by carrying the same values inside
> `Complete LabOS JSON Response` (§6) — the requirement holds, only its destination changes. `Result Detail
> (JSON)` in this matrix means that field. No row is dropped, because dropping one would silently reduce what
> a `Completed` attempt has to prove.

---

## 6. `Result Detail (JSON)` shapes

> **Wire name: `Complete LabOS JSON Response`.** The Airtable team granted this field in v2 under their own
> name; `Result Detail (JSON)` remains LabOS's internal vocabulary. The client maps on the way out (§4.4).

One long-text field, JSON object, always carrying `schema` matching §4.1's `Schema Version`. This is what
keeps the Airtable schema stable as test methods evolve.

**Static Load** — per-gauge deflection at each load step:
```json
{
  "schema": "1.0",
  "test_type": "Static Load",
  "pressure_unit": "PSF",
  "deflection_unit": "in",
  "design_pressure": { "inward": 40.0, "outward": 40.0 },
  "steps": [
    { "step": 1, "target": 20.0, "actual": 20.1, "hold_s": 10,
      "gauges": { "g1": 0.11, "g2": 0.19, "g3": 0.12 }, "at": "2026-07-29T14:05:12Z" },
    { "step": 2, "target": 40.0, "actual": 40.3, "hold_s": 10,
      "gauges": { "g1": 0.28, "g2": 0.42, "g3": 0.31 }, "at": "2026-07-29T14:07:44Z" }
  ],
  "max_pressure": 41.0,
  "max_deflection": { "gauge": "g2", "value": 0.42 }
}
```

**Cycles**:
```json
{
  "schema": "1.0", "test_type": "Cycles",
  "pressure_unit": "PSF",
  "cycles_required": 4500, "cycles_completed": 4500,
  "pressure_range": { "low": -20.0, "high": 20.0 },
  "recovery_time_s": 60,
  "aborted_at_cycle": null,
  "max_deflection": { "gauge": "g2", "value": 0.37 }
}
```

**Impact / Forced Entry / ANSI Z97.1** — attempt log, operator-entered:
```json
{
  "schema": "1.0", "test_type": "Impact",
  "impacts": [
    { "n": 1, "location": "center", "drop_height_in": 48, "outcome": "no penetration" },
    { "n": 2, "location": "corner", "drop_height_in": 48, "outcome": "no penetration" }
  ],
  "photo_urls": ["https://labos.…/p/1.jpg"]
}
```

Rules: keys are `snake_case`; units are declared in the object, never implied; timestamps ISO 8601 UTC;
unknown keys are **ignored** by consumers, never an error — that's what makes minor bumps additive.

---

## 7. Photos and artifact links

- **LabOS-hosted URLs, not Airtable attachments.** Attachments consume base storage, Airtable copies the
  binary, and attachment URLs are refreshed/expiring — none of which suits a lab archive that must stay
  readable for years.
- Multiple photos: newline-separated URLs in one long-text field (v1). If Airtable prefers a child table
  later, that's a minor bump.
- **Dependency (our side, gap B):** management needs a stable, externally reachable origin before the first
  real write, or every link resolves to `localhost`. Tracked in the internal plan as gap B, due **before**
  first production write.
- **Open:** must links be publicly reachable, or will Airtable users authenticate to LabOS? Decides whether
  URLs carry a signed, expiring token (§10.1).

---

## 8. Delivery, retries, and where sync state lives

- **Local-first, always.** The attempt is committed to the LabOS database before any Airtable call. Airtable
  is never on the testing critical path; a network outage cannot stop or corrupt a test.
- **Durable queue** (`sync_queue`) with an in-process worker; serialized to respect Airtable's **5 requests/s
  per base**; batches ≤10 records.
- **Retry classes:** `429` and `5xx` → exponential backoff with jitter, indefinite. `422` (bad value /
  unknown select option) → **do not retry**; mark `Retry Required` and surface in the LabOS UI, because a
  retry of a malformed payload is just a slower failure. `401/403` → halt the worker and alert; a bad token
  must not be hammered.
- **Sync state lives in LabOS** (`Pending` / `Synced` / `Sync Failed` / `Retry Required`), visible to the
  operator with a manual retry. It is **not** written to Airtable: a field whose values include `Sync Failed`
  can never be written at the moment the sync fails — if we could write it, there was no failure. Airtable
  gets arrival tracking for free from `LabOS Updated At` plus its own `Created time`; a missing or stale
  `LabOS Updated At` is the honest indicator of an unsynced attempt.

---

## 9. Read direction — the two things this contract depends on

Specified in full in the mapping doc; only the hard dependencies are recorded here.

1. **Test parameters must be machine-readable.** Discrete fields on Protocol Sections
   (`Design Pressure Inward (PSF)`, `Design Pressure Outward (PSF)`, `Hold Time (s)`, `Cycles Required`,
   `Deflection Points`, `Loading Sequence (JSON)`) **or** one versioned `Required Testing Parameters (JSON)`.
   Free text does not satisfy this contract — the operator would still re-type the numbers, which is the
   problem the integration exists to remove.
2. **Named views, not raw tables.** LabOS reads `?view=LabOS – Scheduled Tests` etc. Airtable owns the filter
   logic; their scheduling changes then never become a LabOS bug.

> **v2 did not answer either of these.** Its §6 step 5 says only *"perform testing in LabOS using the
> requirement values read from Airtable"*, and it publishes table IDs without a field specification for
> Protocol Sections (`tblqpvuJlSdkeS9PS`). Requirement **1** is therefore still the integration's critical
> path (§10.3), and it is the one item the schema probe **cannot** settle: the probe reveals what fields
> exist, but not whether their contents are machine-readable. A field called `Requirements` of type long text
> would pass a schema check and still fail this contract.

**Binding:** LabOS binds to **field IDs** (`fld…`), not names, using `schema.bases:read` +
`returnFieldsByFieldId=true`, with a schema snapshot committed to the repo and diffed at deploy time. A rename
on the Airtable side is then free; a *removal* or retype fails loudly at deploy instead of silently at test
time.

---

## 10. Open items before `v1.0` — **canonical list**

> **This table is the single source of truth for open integration items.** The review doc §6, the verification
> report §5, the Notion mapping §5, and the Notion response §9 are *views* of it, written for different
> audiences. When an item closes, close it **here first**, then update the views. If they ever disagree, this
> table wins.

**Reconciled against the Airtable team's v2 guide, 2026-08-17.** Items 0–12 carry their `v0.2` numbers so the
views stay traceable; 13–16 are new in `v0.3`.

| # | Item | Owner | Status after v2 |
|---|---|---|---|
| 0 | `Testing End Date` in their always-required set vs. an `In Progress` attempt having no end date | Airtable | ⬛ **Moot** — v2 removed both date fields. Reopened in different form as **13**. |
| 1 | `Photos` field type = URL/long-text (not Attachment); must artifact links be publicly reachable? | Airtable | 🔎 Open — **type answered by the schema probe**; reachability still needs a human answer. |
| 2 | `Airtable … ID` fields: plain text or link-to-record? (LabOS proposes text) | Airtable | 🔎 Open — **answered by the schema probe**. |
| 3 | **Read-side parameter structure: discrete fields or versioned JSON? (§9.1)** | Airtable / Luis | 🔴 **Open — the critical path. Gates W3.** v2 §6 step 5 still says only "use the requirement values read from Airtable". No field spec for Protocol Sections. |
| 4 | Writable table in its own base vs. one base + write allowlist | Airtable | ✅ **CLOSED by v2 §2.** Testing `app4oXS3Kd5IKWgJ7`, production `app0OCunbmuXl7Hc9`. **Caveat in §0.1:** PAT scopes are per-base, so LabOS enforces the table allowlist client-side. |
| 5 | `Impact Result` option set — fixed list or free text? | Airtable / Luis | 🔎 Open — **answered by the schema probe**. |
| 6 | Approve the 11 requested fields and the option sets (§4.3–4.5) | Airtable | 🟡 **4 of 11 granted:** `Schema Version`, `Max Pressure Achieved`, `Deflection Unit`, `Complete LabOS JSON Response`. The remaining 7 split into **14** (blocking) and **15** (not blocking). |
| 7 | Is `Test Name` canonically the Protocol Section's `Test Name`? | Airtable | ⬛ **Moot** — no `Test Name` field exists in their raw table. Folded into **15**. |
| 8 | Confirm the two-write lifecycle (`In Progress` then terminal) is acceptable | Airtable | 🟠 Open — now **coupled to 13**. A single `Test Date` only works cleanly if it means *start*. |
| 9 | Wall snapshot fields: required on every hardware test? | Airtable | ⬛ **Answered implicitly: no** — absent from v2. Confirmation folded into **15**. |
| 10 | Rotated PAT with `data.records:read` + `:write` + `schema.bases:read`, delivered out-of-band | Airtable | 🟠 **Open — gates everything LabOS can verify.** v2 states the scopes and correctly omits the token. **The leak is remediated:** no token appears in v2. Delivery still pending. |
| 11 | Verify the §5 null/blank table against the live base and add the evidence column | **LabOS** | 🟠 Open — **harness built ahead of the token** so this closes the day it arrives. |
| 12 | Reachable report/photo origin (gap B) before first production write | **LabOS** | 🟠 Open. |
| **13** | **The `Test Date` collapse.** v2 replaces `Testing Start Date` + `Testing End Date` with one `Test Date`. This removes test duration from the record entirely, and leaves the two-write lifecycle with no field that distinguishes "started at" from "finished at". **LabOS asks for both fields back.** Fallback if refused: `Test Date` means *start*, duration moves into `Complete LabOS JSON Response`, and item **8** must then be confirmed explicitly. | Airtable | 🔴 **NEW — blocking** |
| **14** | **`Corrects Attempt ID` + `Correction Reason` are absent.** These are the only two fields in §4 that the JSON valve cannot rescue, because Airtable automations must *branch* on them — a value buried in long text cannot be filtered, linked, or rolled up. Without them a correction and a genuine retest are indistinguishable in the data (§3.1), so any roll-up counting attempts or computing a pass rate is wrong in one of the two cases. | Airtable | 🔴 **NEW — blocking** |
| **15** | **Seven further fields absent**, all non-blocking because §6's JSON field can carry them: `Test Name`, `Abort Reason`, `Required Value`, `Required Unit`, `Cycles Required`, `Cycles Completed`, plus `Test Rig` / `LabOS Version` / `Result Rationale` and the six wall-snapshot fields (§4.2). LabOS asks for `Test Name` and `Abort Reason` as first-class fields — both are things a human reads off the row — and will carry the rest in JSON. Also: confirm the wall-snapshot omission is deliberate. | Airtable | 🟠 **NEW** |
| **16** | **`Test Result` option spelling.** Their v2 worked example sends `"Passed"`; this contract specifies `Pass`. A single-select mismatch either 422s or silently creates a junk option, and the same risk applies to every select field. | Airtable | 🔎 **NEW — answered by the schema probe**, then confirmed in writing. |

**Legend:** ✅ closed · 🟡 partially closed · 🔴 blocking · 🟠 open · 🔎 mechanically answerable from
`GET /v0/meta/bases/{baseId}/tables` · ⬛ moot/superseded.

### 10.1 What the schema probe closes without another round-trip

Items **1** (partly), **2**, **5**, **16** — and it verifies every ID in §0.1 — from a single authenticated
call. That is four open items and nine table IDs converted from correspondence into evidence, in one request.
The harness is built now, ahead of the token (item 10), so the answers land the same day the PAT does.

### 10.2 What genuinely blocks, once the token arrives

Only three things, and none of them are LabOS-side:

1. **Item 3** — read-side parameter structure. Gates W3. Escalate first; it has been open longest and v2 did
   not touch it.
2. **Item 13** — the `Test Date` collapse.
3. **Item 14** — the correction fields.

**Ratification:** when 1–10 and 13–16 close, this becomes `v1.0` and `Schema Version` on the wire reads `1.0`.
Additive changes → minor bump (`1.1`). Removals, retypes, or semantic changes → major bump (`2.0`).
