# Airtable team — what we need from you, 2026-09-11

**From:** LabOS (Abdelrahman) · **To:** the Airtable team
**Companion to:** `testing-base-change-document-2026-09-08.md` (the full change reference) and
`../runbooks/production-airtable-promotion-2026-09-11.md` (the field-by-field spec)

This is the short list: **what changes in your base, what your views and automations need to know, and what
we need you to approve.** Nothing here has been applied to your production base, and nothing will be until
you say so.

---

## 1. Who owns what — so the rest of this reads correctly

| | Owns |
|---|---|
| **Airtable (you)** | The hierarchy — jobs, mock-ups, protocols, sections. The requirements themselves. Everything commercial. All views, roll-ups and automations. Your own schema and its options |
| **LabOS (us)** | The validated local snapshot of a requirement, the test lifecycle, manual and rig result capture, review and verdict, durable local persistence, the outbox, and the rows we publish to `LabOS Raw Data Table` |
| **Firmware (the rigs)** | Running the test on the hardware, and the sensors |

Four boundaries that do not move:

- **Airtable does not command a rig.** No Airtable value reaches hardware directly; a requirement is
  validated and snapshotted first, and a test keeps what it was instructed to run even if the section is
  edited later.
- **The rigs never call Airtable.** They talk to LabOS over MQTT and nothing else.
- **LabOS never writes your hierarchy.** Not a job, not a mock-up, not a protocol, not a section. This is
  enforced in code by a single-table write allowlist and asserted on every live probe by snapshotting all
  four tables before and after.
- **LabOS writes exactly one table: `LabOS Raw Data Table` `tblnc9SsbXU0C0FWh`.** An Airtable token is
  scoped per *base*, not per table, so that allowlist — not the token — is what keeps us out of the rest.

---

## 2. The schema change we are asking for

**19 fields added. Nothing renamed, retyped or deleted. 142 → 161.**

| Table | Adds | Direction |
|---|---|---|
| `Protocol Sections` | 8 | **we read them** — the machine-readable form of a requirement |
| `LabOS Raw Data Table` | 11 | **we write them** — what a test produced |

Every field, with its exact type, choices and precision, is in the promotion spec. Three points that a type
check would not catch:

- **`Forced Entry Result` and `ANSI Result` must be created with the choices `Pending` · `Passed` · `Failed`
  · `Inconclusive`.** Those are *your* spellings, matching `Test Result`. A select created with `Pass`/`Fail`
  would accept nothing we send.
- **`Impact Classification` is exactly `SMI` · `LMI Level D` · `LMI Level E`.**
- **`Target Impact Velocity` is a number with precision 2.** Precision 0 silently truncates 50.25 ft/s.

**Three fields in your Testing base must not be created here.** `Missile Type`, `Missile Weight` and
`Impact Velocity` were added to Testing on 2026-09-08 and withdrawn from our contract on 2026-09-10. We have
left them in Testing rather than deleting them — removing a field from a base you share is your call, not a
side effect of our code change — and we would like to agree a cleanup with you separately. They have never
existed in production and must stay that way.

---

## 3. What your views, roll-ups and automations need to know

### 3.1 One physical impact is now one row ⚠️ **this one changes what your views see**

Previously a five-impact test published **one** row with a summary line. It now publishes **five** rows,
each with its own verdict and its own photographs.

- Count **tests** by grouping on `LabOS Test ID`.
- Count **impacts** with `Impact Number` (1, 2, 3…), which is blank on the other four test types.
- Any roll-up that counts rows to mean "tests" will over-count impact tests by the number of impacts unless
  it groups on `LabOS Test ID` first.

This was confirmed as intended by our project owner on 2026-09-08, and `Impact Number` exists specifically so
the distinction is available to you rather than having to be inferred.

### 3.2 `LabOS Attempt ID` is the merge key

Every write is an **upsert on `LabOS Attempt ID`**. A retry after a network failure updates the same record;
it never inserts a second one. An automation that fires "on record created" will see one creation per
attempt — but an automation that fires "on record updated" will see an attempt updated up to three times as
it moves create → terminal → verdict, plus once per photograph.

### 3.3 Two new result columns beside the one you already have

`Test Result` is **unchanged** and still carries the verdict for all five test types, at every phase. The
two new columns are additions, not replacements:

- `Forced Entry Result` is populated only for `Test Type = Forced Entry`, and blank on the other four;
- `ANSI Result` only for `Test Type = ANSI Z97.1`.

They hold the **same value** as `Test Result`, so a report about one standard no longer has to filter
`Test Result` by `Test Type` first. This is the same shape as `Impact Result`, which already sits beside
`Test Result` today. Our project owner asked for them on 2026-09-10 because the two standards are judged
differently.

**We previously told you we would add these only if you named a report that needed them.** That statement is
withdrawn — it is struck through in the change document — and it was our rule, not yours.

### 3.4 The impact requirement changed direction

You used to be asked for the missile, its mass and a target velocity. You are not any more.

- **What you still supply:** how many impacts — `Required Value` with `Requirement Code` `IMPACT_SMI` or
  `IMPACT_LMI`. Unchanged.
- **What we now send you:** `Impact Classification` — the one value that determines the rest — and
  `Target Impact Velocity`, entered by our operator.

Your `Requirement Code` already distinguishes large from small missile, so the only fact it never carried was
Level D versus Level E, and that is the operator's.

### 3.5 Blank is never zero

A blank `Required Value` is refused as a section we cannot execute. It never becomes `0`. Likewise a blank
`Applicability` reads as `Unconfirmed`, never as `Not Required`.

---

## 4. What we need from you

| # | Ask | Why |
|---|---|---|
| 1 | **Acknowledge the change document**, including the three withdrawn fields left sitting in Testing | They are unread by us, and we would rather you knew than discovered it |
| 2 | **Approve and apply the 19 production additions** | The promotion spec is field-by-field; production stays at 142 until you act |
| 3 | **Confirm the multi-row impact model is acceptable to your views and automations** | It is the one change that alters what your existing base *sees* |
| 4 | **Tell us about any roll-up or automation that counts rows as tests** | So it can be re-pointed at `LabOS Test ID` before the model changes under it |
| 5 | **Confirm the six writable `LabOS`-named fields on `Protocol Sections` are yours, not ours** | We do not write them and want to be sure nobody expects us to |
| 6 | **Agree a separate cleanup** for `Missile Type`, `Missile Weight` and `Impact Velocity` in Testing | Deleting fields from a shared base should be deliberate and dated |

---

## 5. What we have already verified, in your Testing base

Not claims — runs, with the output kept:

| | |
|---|---|
| Schema read-back | Independent Meta API pull after every write, by a different tool from the one that wrote. Testing **164**, production **142** |
| TA7 — impact | **64/64** assertions on the real wire, one clean run |
| TA6 — per-standard results | **97/97** assertions on the real wire, one clean run, all five test types |
| Idempotency | Re-sending an attempt upserts onto the **same record id**, with no `createdRecords` |
| Write boundary | All four hierarchy tables snapshotted before and after every probe: **no writes** |
| Production isolation | Production schema read before and after every run and compared **byte for byte**: unchanged, and its record count unchanged |

**There are synthetic records in your Testing base**, tagged `Operator Name = LABOS-PROBE-TA6` and
`LABOS-PROBE-TA7`. They are listed in our evidence folders. We have **not** deleted them — we would rather
leave something explicable in a shared base than delete records without asking. Tell us if you would like
them removed and we will do it as a recorded operation.

---

## 6. What is not in this change

- **No deflection data reaches Airtable.** Not now and not as part of this. `Deflection Value`,
  `Deflection Unit` and `Max Pressure Achieved` are deliberately never written — they have no validated
  source, and their absence is a decision rather than an oversight.
- **No commercial field is read.** Not `Approved Proposal Amount`, not `Balance Due`, not customer contacts,
  not the QuickBooks ids.
- **Nothing is read from `Walls & Positions`, `Wall Scheduling/Reservation` or `Back Charges`.** All 40
  fields, untouched.
