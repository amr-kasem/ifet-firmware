# LabOS Verification Report & API Pre-Flight — Airtable Integration

**From:** LabOS (Abdelrahman) · **Date:** 2026-07-29 · **Base:** `appYBTqIL43pmS0xN` (`IFET Test Base For LabOS`)
**Companion:** *LabOS Response — Airtable Schema Review & Write Contract v0.2*

---

## 0. Status in one paragraph

**No request has yet been made against your base.** The access token printed in §1 of your document is treated
as compromised and was never used or stored by LabOS — we are waiting for the rotated one. So this report has
two halves: **Part A** is what LabOS has already built and verified *on our own side*, with commands and
outputs; **Part B and C** are the **exact HTTP requests we intend to run**, listed in full so you can approve
them before anything touches your base. Part B is entirely read-only. Part C writes only to
`LabOS Raw Test Results` and needs your explicit go-ahead.

---

## Part A — What LabOS has verified (completed 2026-07-29)

### A.1 Secret handling — the token now has exactly one way into the system

Ahead of receiving the replacement token, every credential was moved out of source control into a
server-side-only environment file. The relevant guarantee for you: **the Airtable token can no longer reach a
file that a browser can read.**

| Check | Command | Result |
|---|---|---|
| Configuration resolves with the environment file present | `docker compose config --quiet` | **exit 0** |
| Stack refuses to start when a credential is missing | `docker compose config --quiet` (file removed) | **exit 1** — `required variable POSTGRES_USER is missing a value: set POSTGRES_USER in .env` |
| No credential remains in version control | `./deployment/scripts/check-secrets.sh` | **PASS** — 4/4 checks |
| No Airtable token pattern in any tracked file | `git grep -E 'pat[A-Za-z0-9]{14}\.'` | **0 matches** |
| Browser-served configs carry no secrets | guard checks `deployment/config/config.json`, `src/ifet_ui_react/config.json` | **clean** — credential fields absent or empty; no mention of Airtable |

The guard is a pre-commit check that fails the build on a token pattern in tracked content, a non-empty
credential in either browser-served config, or a literal credential in the compose file. It is the direct
answer to how the leak that happened to your document cannot happen to ours.

### A.2 The integration service comes up and reads its settings correctly

Rehearsed end-to-end in an isolated environment — no production system involved:

| Check | Result |
|---|---|
| Database + API services start | both **Up** |
| Environment inside the API container | `AIRTABLE_BASE_ID=appYBTqIL43pmS0xN`, `AIRTABLE_RESULTS_TABLE=LabOS Raw Test Results`, `AIRTABLE_WRITE_ALLOWLIST=LabOS Raw Test Results`, `AIRTABLE_SYNC_ENABLED=false`, `AIRTABLE_TOKEN=` *(empty)* — all correctly injected |
| Database authentication from the secret store | **succeeded** — `Application startup complete`, no auth errors |
| Real HTTP request against the LabOS API | `curl -o /dev/null -w "%{http_code}" http://localhost:18000/docs` → **HTTP 200** |
| Settings module output | `{'base_id': 'appYBTqIL43pmS0xN', 'results_table': 'LabOS Raw Test Results', 'write_allowlist': ['LabOS Raw Test Results'], 'sync_enabled': False, 'token_present': False, 'public_origin': None}` → `state: not configured (missing: AIRTABLE_TOKEN)` |

Three properties worth calling out, because they are the ones that matter to you:

1. **The token is never printed.** The settings object reports `token_present: true/false` and nothing more —
   in logs, in error traces, in debug output. There is no code path that emits its value.
2. **A missing token is a valid, non-fatal state.** LabOS runs normally with Airtable unconfigured; it simply
   does not sync. So issuing the token is not on anyone's critical path, and revoking it breaks nothing.
3. **Sync is behind two independent switches** — an explicit `AIRTABLE_SYNC_ENABLED` flag *and* a
   fully-configured check. A half-filled configuration cannot accidentally start writing to your base.

### A.3 The write boundary is enforced in our code

Because an Airtable personal access token is scoped **per base, not per table**, the "read-only on all
existing tables" guarantee in your §1 cannot be enforced by the token itself. LabOS therefore enforces it
locally: the API client checks every write against a single-table allowlist and raises before the request is
built.

```
PermissionError: refusing to write Airtable table 'Projects': not in
AIRTABLE_WRITE_ALLOWLIST ['LabOS Raw Test Results']
```

This holds regardless of what the token technically permits. We'd still suggest the structural fix — putting
the writable table in its own base — so the guarantee is enforced by Airtable rather than by our good
behaviour.

---

## Part B — Read-only requests we will run first (for your approval)

All `GET`. No writes, no deletes, no schema changes. Rate-limited to **5 requests/second** per your API's
limit. The token is read from the environment and never appears on a command line or in a log.

```bash
# Authorization header comes from the environment, never inline
AUTH="Authorization: Bearer $AIRTABLE_TOKEN"
BASE=appYBTqIL43pmS0xN
```

### B.1 Confirm what the token can actually do

```bash
curl -s -H "$AUTH" https://api.airtable.com/v0/meta/whoami
```
**Answers:** the token's identity and its granted scopes. This settles the per-base vs. per-table question
without writing anything, and confirms whether `schema.bases:read` was included.

### B.2 Read the base schema — the single most useful call

```bash
curl -s -H "$AUTH" https://api.airtable.com/v0/meta/bases/$BASE/tables
```
**Answers, mechanically, six of the open questions in our response document:**
- whether the `Airtable … ID` fields are **plain text or link-to-record**
- whether `Photos` is a **URL/long-text or an Attachment** field
- whether `LabOS Attempt ID` is **plain text** (required — computed fields cannot be an upsert merge key)
- the **real option sets** for `Test Status`, `Test Result`, `Unit`, `Testing Continued`, and the status fields
- whether `Required Testing Parameters` is long text
- every field's **field ID** (`fld…`), which is what LabOS binds to so a later rename cannot break the
  integration

We snapshot this response into our repository as the binding baseline and compare it on every deployment, so
an Airtable-side schema change surfaces as a deployment failure rather than a silent mid-test failure.

### B.3 Read a small sample from each table

```bash
for T in Projects "Mock-Ups" "Test Protocols" "Protocol Sections" Walls; do
  curl -s -H "$AUTH" -G "https://api.airtable.com/v0/$BASE/$(printf %s "$T" | jq -sRr @uri)" \
       -d pageSize=3 -d returnFieldsByFieldId=true
done
```
**Answers:** that we can walk **Project → Mock-Up → Protocol → Section → Wall** using your ID fields, and that
`returnFieldsByFieldId` behaves as expected. Three records per table is enough; we are not bulk-reading your
data.

*(Exact table names/IDs will be taken from B.2 rather than guessed — names containing spaces are URL-encoded.)*

### B.4 The one read that decides the Week 3 design

```bash
curl -s -H "$AUTH" -G "https://api.airtable.com/v0/$BASE/Protocol%20Sections" \
     -d pageSize=10 \
     -d "fields%5B%5D=Test Name" \
     -d "fields%5B%5D=Required Test Value" \
     -d "fields%5B%5D=Required Unit" \
     -d "fields%5B%5D=Required Testing Parameters"
```
**Answers the biggest open risk empirically.** If `Required Testing Parameters` contains prose, the operator
still has to read it and re-type the numbers, and Week 3 delivers nothing — we would need the discrete fields
(inward/outward design pressure, hold time, loading sequence, deflection points, cycles) or one versioned JSON
field. If the samples already contain structured values, the design may be fine as-is. **We would rather find
this out from your sample data than debate it.**

### B.5 Read through a named view, if you create one

```bash
curl -s -H "$AUTH" -G "https://api.airtable.com/v0/$BASE/Protocol%20Sections" \
     -d "view=LabOS – Scheduled Tests"
```
**Answers:** whether we can take our work queue from a view you control. You own the filter logic; your
scheduling changes then never become a LabOS bug.

**Deliverable from Part B:** a written schema report back to you within a day of receiving the token —
every field, its type, its ID, and its option set, with our open questions marked answered or still open.

---

## Part C — Write probes (explicit approval needed)

Only against `LabOS Raw Test Results`, only in the sandbox base. Each probe proves one contract rule, so the
contract rests on your API's actual behaviour instead of on either side's assumption.

**Tagging and cleanup.** Every probe row carries `Operator Name = LABOS-PROBE` and a `LabOS Test ID` prefixed
`probe-`, so they are trivially filterable. Your document says LabOS only creates and updates, never deletes —
so please either **purge the tagged rows** when we're done, or grant delete on that one sandbox table.

| # | Probe | Expected | What it settles |
|---|---|---|---|
| 1 | Create with required fields only | 200 | the minimum viable payload |
| 2 | `""` into a number field | **422** | confirms §5 must become "omit the key" — with your API's own error text as evidence |
| 3 | `""` into a date field | **422** | same, for dates |
| 4 | `""` into a single select | **422** | same, for selects |
| 5 | Omit a non-applicable key | 200, cell empty | our replacement rule works |
| 6 | Send `0` into a number | 200, stores `0` | a zero reading is data, not a blank |
| 7 | **Upsert twice with the same `LabOS Attempt ID`** | **one record**; second call reports *updated* | the no-duplicates guarantee |
| 8 | Repeat the identical payload, as a timed-out retry would | still **one record** | retries after a network timeout are safe |
| 9 | Unknown select option | 422 | LabOS must never invent an option at runtime |
| 10 | Batch of 10, then 11 | 200, then 422 | documents the batch limit |
| 11 | Burst above 5 req/s | 429 | confirms our rate limiter |
| 12 | Field **ID** as the payload key | 200 | we can bind by ID, so renames are free |
| 13 | JSON round-trip through a long text field | byte-identical | `Result Detail (JSON)` is safe to use |
| 14 | ISO 8601 UTC datetime round-trip | no timezone shift | overnight cyclic runs are not off by hours |

### The two requests that matter most, in full

**Minimal upsert — the shape every result write will take:**
```bash
curl -s -X PATCH "https://api.airtable.com/v0/$BASE/LabOS%20Raw%20Test%20Results" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "performUpsert": { "fieldsToMergeOn": ["LabOS Attempt ID"] },
    "records": [{ "fields": {
      "Airtable Project ID":  "recXXXXXXXXXXXXXX",
      "Airtable Mock-Up ID":  "recYYYYYYYYYYYYYY",
      "Airtable Protocol ID": "recZZZZZZZZZZZZZZ",
      "Airtable Section ID":  "recWWWWWWWWWWWWWW",
      "LabOS Test ID":        "probe-test-0001",
      "LabOS Attempt ID":     "probe-attempt-0001",
      "Attempt Number":       1,
      "Test Name":            "Static Load",
      "Test Type":            "Static Load",
      "Test Status":          "Completed",
      "Test Result":          "Pass",
      "Measured Value":       40.0,
      "Unit":                 "PSF",
      "Deflection Value":     0.42,
      "Testing Start Date":   "2026-07-29T14:03:00Z",
      "Testing End Date":     "2026-07-29T14:31:00Z",
      "Operator Name":        "LABOS-PROBE",
      "Retest Required":      false,
      "Testing Continued":    "Continued"
    }}]
  }'
```
Run **twice, unchanged**. Expected: the first call creates one record, the second **updates that same record**
and creates nothing. That is probes 7 and 8, and it is the single most important test in this document —
it's the proof that a retry after a timeout cannot duplicate a test result.

**The blank-handling probe, which produces the evidence for your §5:**
```bash
# identical body, except one number field carries an empty string
... "Deflection Value": "" ...
```
Expected: **422**, with an `INVALID_VALUE_FOR_COLUMN`-class error naming the field. We will send you the exact
response so the rule change rests on your API's behaviour rather than on our claim.

---

## Part D — What we need from you

| # | Item | Blocks | Note |
|---|---|---|---|
| 1 | **Revoke the token in your §1** and send the replacement out-of-band (secrets manager, not a document) | every request in this report | It also persists in the source document's version history, so revocation is the only complete fix |
| 2 | Scopes on the new token: `data.records:read`, `data.records:write`, **`schema.bases:read`** | B.2, and field-ID binding | Without the third, we must bind to field *names* and a rename silently breaks the integration |
| 3 | **Approval to run Part B** (read-only) and **Part C** (writes to the results table only) | testing | Part B is harmless; we won't run Part C without a yes |
| 4 | Read-side parameter structure — discrete fields or one versioned JSON field | **Week 3** | B.4 may answer this from your samples; if it shows prose, this becomes urgent |
| 5 | The 11 requested result fields and the proposed option sets | **Week 4** | Five are blocking: `Max Pressure Achieved`, `Result Detail (JSON)`, `Deflection Unit`, `Corrects Attempt ID` + `Correction Reason`, `Schema Version` |
| 6 | **`Testing End Date` is in your §4 always-required list** — but a test that is still `In Progress` has no end date | the record lifecycle | Either drop it from the always-required set so we can create the row when a test *starts* (giving you live visibility of what is on the walls), or tell us you want a single write at completion only. **Your document as written forbids the first.** |
| 7 | Who purges the `LABOS-PROBE` rows, or delete permission on that sandbox table | cleanup | |
| 8 | Whether report/photo links must be publicly reachable, or Airtable users authenticate to LabOS | Week 5 | Decides whether our URLs carry a signed, expiring token |

---

## Part E — What LabOS does next, in order

| Step | Waits on | Status |
|---|---|---|
| Secret store, write allowlist, settings module | — | ✅ **done and verified** (Part A) |
| Airtable API client — rate limiter, retry classes, upsert helper, schema snapshot | — | in progress; no token needed to build it |
| Payload builder + offline contract tests (no empty strings, required-per-test-type, enum validation, ISO 8601 UTC) | — | in progress; testable with no API access at all |
| **Run Part B and send you the schema report** | items 1–3 | ready to run |
| **Run Part C and send you the evidence table** | item 3 | ready to run |
| Append-only attempt data model | — | next |
| Rig-side capture of peak pressure + per-gauge deflection | — | in parallel; needs rig time |
| Requirements-IN operator flow | item 4 | Week 3 |
| Results-OUT sync queue, dark-launched | items 4, 5 | Week 4 |

**A 45-minute call would close items 3–6 faster than document round-trips** — happy to schedule whenever
suits.

---
*LabOS · 2026-07-29. No request has been made against base `appYBTqIL43pmS0xN`. Every command in Parts B and C
is listed here in full precisely so that it can be reviewed before it is run.*
