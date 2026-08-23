# LabOS ↔ Airtable — Integration Status & Verification Report

**From:** LabOS (Abdelrahman) · **Date:** 2026-07-29 · **Status:** historical sent record (see banner)
**Sandbox base:** ~~`appYBTqIL43pmS0xN`~~ — *retired 2026-08-22; see banner*
**Companion:** *LabOS Response — Airtable Schema Review & Write Contract v0.2*


> ### 📕 Historical — this is the 2026-07-29 sent record. Read this first
>
> Kept **verbatim** so the correspondence stays auditable. It reviews the Airtable team's **v1** schema doc and
> proposes a three-stage verification. Nothing below has been rewritten, and it should not be.
>
> **What actually happened since.** Their **v2 guide (2026-08-17)** changed the base IDs, published real table
> IDs, granted four of eleven requested fields, and removed several fields this document assumes. Then on
> **2026-08-23 they delivered both PATs**, and LabOS ran the plan in §4:
>
> | This document proposed | Outcome |
> |---|---|
> | **Stage 1** — offline contract tests, no access needed | ✅ **run** — 132 offline tests, no network, no token |
> | **Stage 2** — read-only requests against the base | ✅ **run 2026-08-23** against *both* `app4oXS3Kd5IKWgJ7` and `app0OCunbmuXl7Hc9`. GETs only; nothing was written to either |
> | **Stage 3** — a write round-trip into the results table | ⏳ **not yet run** — the last thing standing before W2 |
>
> The stage shapes held up; §5's asks are largely answered or overtaken. **This document no longer owns the
> "what we've verified" subject** — `labos-airtable-live-probe-findings-2026-08-23.md` does.
>
> For the current position, read:
> - **`labos-airtable-live-probe-findings-2026-08-23.md`** — what the live bases actually hold, six items closed, six opened, and the Monday agenda (§7)
> - **`labos-airtable-write-contract-v0.3.md` §10** — the canonical open-items list (this doc's §5 is a
>   stale view of it)
> - **`labos-airtable-write-contract-v0.3.md` §0** — the live base/table IDs, now confirmed against the API
>
> In particular: base `appYBTqIL43pmS0xN` and the table name `LabOS Raw Test Results` **no longer apply.**
> The testing base is `app4oXS3Kd5IKWgJ7` and the writable table is `LabOS Raw Data Table`
> (`tblnc9SsbXU0C0FWh`).
>
> **Of §5's six asks:** 1 and 2 (token + schema scope) ✅ closed · 3 (approval for stages 2–3) — stage 2 was
> invited and run, stage 3 still needs their go-ahead · 4 (machine-readable parameters) 🟡 answered with a
> defect, contract §10.3 + §10.19 · 5 (the 11 fields) 🟡 4 granted · 6 (`Testing End Date`) ⬛ moot, v2 removed
> both date fields and replaced them with a single `Test Date` — reopened as §10.13/§10.20.

---

## Purpose

This report does three things: it states clearly **which system owns what**, it shows **what LabOS has built
and verified so far**, and it lists **what we need from the Airtable side** to connect the two.

**One note first: we have not yet made a single request to your base.** The access token printed in your
document is treated as compromised and was never used or stored by LabOS. Everything described as *verified*
below happened inside our own system; everything described as *planned* is written out in full so you can
review it before it runs.

---

## 1. Who owns what

The boundary is deliberately narrow. Neither system reaches into the other's responsibilities.

| | **Airtable — your side** | **LabOS — our side** |
|---|---|---|
| **Owns** | Projects, job numbers, mock-ups and specimens, test protocols, protocol sections, walls, wall positions, reservations, scheduling | Test execution on the rigs, measurement, pass/fail determination, reports and photos |
| **Decides** | What is to be tested, when, and on which wall | What the test measured and whether it passed |
| **Roll-ups and status** | All Project / Mock-Up / Protocol roll-ups, via your automations | Nothing — LabOS writes one row per test attempt and stops there |
| **Access held by the other side** | LabOS reads; LabOS never edits or deletes | Airtable does not reach into LabOS at all |
| **Never does** | Control equipment or influence a running test | Create or modify a project, protocol, wall, or reservation |

Two consequences worth stating plainly, because they are what make the integration safe:

- **Airtable is never on the testing critical path.** Every test is saved in LabOS *before* any Airtable call.
  If your base is unreachable, testing continues normally and the results sync later.
- **No field is written in both directions.** Requirements only flow in; results only flow out. There is no
  case where the two systems disagree about who is right.

---

## 2. What crosses the boundary

**Direction 1 — requirements in (Airtable → LabOS, read-only).** The operator selects Project → Mock-Up →
Protocol → Section, and the test parameters load automatically. Nothing is re-typed. LabOS reads only; it
writes nothing back to these tables.

**Direction 2 — results out (LabOS → Airtable, one table).** When a test attempt finishes, LabOS writes a
single row to `LabOS Raw Test Results`: the four Airtable record IDs, our test and attempt identifiers, what
was measured, whether it passed, timestamps, the operator, and links to the report and photos. Your
automations read that row and update your own records.

That is the entire interface. One read path, one write path, one table.

---

## 3. What LabOS has built and verified — our side

All of the following was completed and checked in our own system. No production system and no Airtable base
was involved.

### 3.1 The token now has one single, safe way into our system

We did this work *before* asking for the replacement token, so there is nothing to leak when it arrives.

| What we checked | Result |
|---|---|
| Every credential moved out of source control into a server-side-only file | done |
| The system refuses to start if a credential is missing, rather than falling back to a default | confirmed — startup fails with a clear message |
| No credential of any kind remains in version control | confirmed — automated check passes |
| No Airtable token pattern anywhere in our repository | confirmed — zero matches |
| The two configuration files our web UI serves to browsers contain no secrets | confirmed — and an automated check now fails the build if that ever changes |

The last point is the important one for you: **the Airtable token cannot reach a file a browser can read.**
That is enforced by a check that runs before every commit, not by anyone remembering.

### 3.2 The integration service starts correctly and handles the token safely

| What we checked | Result |
|---|---|
| The service starts and connects to its database using only the secret store | confirmed |
| It receives the Airtable settings correctly | confirmed — base ID, table name, write allowlist, and sync flag all present |
| The token value is never printed — in logs, errors, or debug output | confirmed — the system reports only whether a token *is present* |
| The service runs normally with **no** Airtable token configured | confirmed — it simply does not sync |
| Sync cannot start by accident | confirmed — it requires an explicit switch *and* a complete configuration |

The fourth point matters practically: **issuing or revoking the token breaks nothing on our side.** There is no
pressure to hurry the rotation.

### 3.3 The write boundary is enforced in our code, not just promised

Your document says LabOS has read-only access to your existing tables. We should flag that an Airtable access
token is scoped **per base, not per table** — so the token itself cannot enforce that. LabOS therefore
enforces it: our client checks every write against a one-table allowlist and refuses before the request is
even built.

```
refusing to write Airtable table 'Projects':
not in allowlist ['LabOS Raw Test Results']
```

This holds regardless of what the token technically permits. We would still suggest the structural fix —
putting the writable table in its own base — so that the guarantee is enforced by Airtable rather than by our
good behaviour. Either way is workable; it is worth a deliberate choice.

---

## 4. How we will verify the connection

Three stages, in increasing order of what they touch. **Only stage 1 has run so far.**

### Stage 1 — inside our own system (no access to your base needed) · *in progress*

We test our result payloads offline against the agreed contract: that every required field is present for
each test type, that no empty strings are ever sent, that only agreed option values are used, that all
timestamps are ISO 8601 UTC, and that a genuine zero reading is sent as `0` rather than dropped. This proves
our half without touching anything of yours.

### Stage 2 — reading your sandbox base (read-only) · *needs the new token*

Four read requests, no writes of any kind:

```bash
# 1. What can this token actually do?
GET https://api.airtable.com/v0/meta/whoami

# 2. The base schema — every table, field, field ID, type and option list
GET https://api.airtable.com/v0/meta/bases/appYBTqIL43pmS0xN/tables

# 3. A three-record sample from each table, to confirm we can follow
#    Project → Mock-Up → Protocol → Section → Wall through your ID fields
GET https://api.airtable.com/v0/appYBTqIL43pmS0xN/{table}?pageSize=3

# 4. The Protocol Sections read that decides our Week 3 design
GET https://api.airtable.com/v0/appYBTqIL43pmS0xN/Protocol%20Sections?pageSize=10
```

Request 2 is the valuable one: **it answers six of our open questions mechanically, without another document
round-trip** — whether the record-ID fields are plain text or linked records, whether `Photos` is a URL field
or an attachment field, whether `LabOS Attempt ID` is a plain text field, what your real option lists are,
what type `Required Testing Parameters` is, and every field's stable ID.

Request 4 settles our biggest open risk from your own sample data. **If `Required Testing Parameters` holds
prose, the operator still has to read it and re-type the numbers, which is the exact problem this integration
exists to remove.** We would much rather discover that from your samples than argue it in a document.

**What you get back:** a written schema report within a day of receiving the token — every field, its type, its
ID, and its option list, with each of our open questions marked answered or still open.

### Stage 3 — writing to `LabOS Raw Test Results` only · *needs your explicit approval*

Fourteen small, deliberate checks against the sandbox results table, grouped by what they confirm:

| Group | What it confirms |
|---|---|
| **No duplicates** — send the same attempt twice, then repeat it exactly as a timed-out retry would | **The core guarantee.** One record, not two. A retry updates the existing row instead of creating a second one. |
| **Blank handling** — send an empty string to a number, a date, and a select field; then omit the key instead | Which approach your API actually accepts. We expect the empty strings to be rejected, which would confirm the correction we proposed to your §5. |
| **Value discipline** — an unknown option value; a genuine `0` | That unrecognised values fail loudly rather than creating stray options, and that a zero reading is stored as zero rather than treated as blank. |
| **Limits and formats** — batch size, request rate, field IDs as keys, a JSON round-trip, a UTC timestamp round-trip | That our client respects your limits and that timestamps and structured detail survive intact. |

The single most important request, in full:

```bash
PATCH https://api.airtable.com/v0/appYBTqIL43pmS0xN/LabOS%20Raw%20Test%20Results

{ "performUpsert": { "fieldsToMergeOn": ["LabOS Attempt ID"] },
  "records": [ { "fields": {
      "Airtable Project ID": "rec…", "Airtable Mock-Up ID": "rec…",
      "Airtable Protocol ID": "rec…", "Airtable Section ID": "rec…",
      "LabOS Test ID": "probe-test-0001",
      "LabOS Attempt ID": "probe-attempt-0001",
      "Attempt Number": 1,
      "Test Name": "Static Load", "Test Type": "Static Load",
      "Test Status": "Completed", "Test Result": "Pass",
      "Measured Value": 40.0, "Unit": "PSF", "Deflection Value": 0.42,
      "Testing Start Date": "2026-07-29T14:03:00Z",
      "Testing End Date":   "2026-07-29T14:31:00Z",
      "Operator Name": "LABOS-PROBE",
      "Retest Required": false, "Testing Continued": "Continued"
  } } ] }
```

Sent **twice, unchanged.** Expected: the first call creates one record, the second updates that same record
and creates nothing. This is what proves a network timeout can never duplicate a test result.

**Housekeeping:** every test row is tagged `Operator Name = LABOS-PROBE` with a `LabOS Test ID` starting
`probe-`, so they are easy to filter. Your document says LabOS only creates and updates, never deletes — so
please either purge the tagged rows afterwards, or grant delete on that one sandbox table.

---

## 5. What we need from the Airtable side

*(The six items below are the ones that block progress now. The full list, including our own outstanding work, is tracked internally in the write contract.)*

| # | Item | What it holds up |
|---|---|---|
| 1 | **Revoke the token in your document** and send the replacement out-of-band — a secrets manager rather than a file. It also persists in the document's version history, so revocation is the only complete fix. | every request above |
| 2 | On the new token, include **schema read** access alongside record read and write. It lets us bind to field *IDs* instead of names, so renaming a field on your side can never break the integration. | stage 2, and long-term stability |
| 3 | **Approval for stage 2** (read-only) and **stage 3** (writes to the one results table). | all connection testing |
| 4 | **Test parameters in a machine-readable form** — either discrete fields on Protocol Sections (inward and outward design pressure, hold time, loading sequence, deflection points, cycles) or one agreed JSON field. Free text means the operator still re-types the numbers. | **Week 3** |
| 5 | The **11 additional result fields** and the proposed option lists from our response document. Five are essential, including peak pressure achieved and a way to reference a corrected attempt. | **Week 4** |
| 6 | **One contradiction in your §4:** `Testing End Date` is listed as always required, but a test that is still in progress has no end date. Either drop it from the always-required set — which lets us create the row when a test *starts*, giving you live visibility of what is on the walls — or confirm you want a single write at completion only. As written, your document rules out the first. | the record lifecycle |

---

## 6. What happens next

| **On the LabOS side — now, unblocked** | **On the Airtable side** |
|---|---|
| Airtable client: rate limiting, retry handling, the upsert call, and a stored copy of your schema that we compare on every deployment | Revoke and reissue the token, with schema read access |
| Offline contract tests for our result payloads (stage 1) | Approve stages 2 and 3 |
| Append-only test-attempt data model — every attempt kept separately, never overwritten | Decide the test-parameter structure (item 4) |
| Rig-side capture of peak pressure and per-gauge deflection, which the new fields need | Confirm the additional fields and option lists (item 5) |
| Then: run stage 2, send you the schema report; run stage 3, send you the results | Resolve the `Testing End Date` question (item 6) |

**A 45-minute call would settle items 3 to 6 faster than documents will** — happy to schedule whenever suits.

---
*LabOS · 2026-07-29. No request has been made against base `appYBTqIL43pmS0xN`. Every request in stages 2 and
3 is written out above so that it can be reviewed before it is run.*
