# Review — "IFET Phase 2 · LABOS Sample Schema" (Airtable team, received 2026-07-29)

**Author:** Abdelrahman (LabOS) · **Date:** 2026-07-29 · **Status:** Internal review + ready-to-send reply
**Their doc:** `IFET-Phase-2-LabOS-Doc.pdf` (6 pp) — test base access, read-only field list, `LabOS Raw Test Results` write table, required fields, blank/null rule, roll-up ownership.
**Our side:** [Field Mapping (Working)](https://app.notion.com/p/3a357bad43d581c68ea1c85411429cac) · [5-Week Plan](https://app.notion.com/p/3a657bad43d581e59490f53a8eeedbf6) · internal plan `docs/labos-airtable-integration-internal-plan-2026-07-23.md` · write spec `docs/labos-airtable-write-contract-v0.3.md`


> ### ⚠️ Superseded in part — read this first
>
> This document is the **record of what LabOS sent on 2026-07-29**, kept verbatim so the correspondence stays
> auditable. It reviews the Airtable team's **v1** schema doc.
>
> They replied with **v2 of the integration guide on 2026-08-17**, which changed the base IDs, published real
> table IDs, granted four of the eleven requested fields, and removed several fields this document assumes.
> **Nothing below has been rewritten to match.**
>
> For the current position, read:
> - **`labos-airtable-write-contract-v0.3.md` §0** — what v2 changed, and the live base/table IDs
> - **`labos-airtable-write-contract-v0.3.md` §10** — the canonical open-items list (this doc's §6 is a
>   stale view of it)
> - **`labos-airtable-v2-guide-reconciliation-2026-08-22.md`** — the v2 delta and the outbound reply
>
> In particular: base `appYBTqIL43pmS0xN` and the table name `LabOS Raw Test Results` **no longer apply.**
> The testing base is `app4oXS3Kd5IKWgJ7` and the writable table is `LabOS Raw Data Table`
> (`tblnc9SsbXU0C0FWh`).

---

## 0. Verdict

**Accept the architecture, negotiate the schema.** Their model — one writable table, Airtable owns
scheduling/roll-ups, LabOS owns test execution — is exactly the separation of concerns we asked for, and it
closes three of our open gaps outright (sandbox base, roll-up ownership, photos-as-links). HM's and Luis's
comments are all correct and, usefully, all point the same way we do.

Two things in their doc are **wrong as written and must change before either side builds**:

1. **§5 "send `\"\"`" is wrong** and directly contradicts HM's point 1. Airtable's REST API rejects `""` on
   number and date fields (`422 INVALID_VALUE_FOR_COLUMN`) and on single-selects unless `""` is a real
   option. The rule must be **omit the key entirely**. (HM is right; their §5 needs replacing.)
2. **"read-only for all existing tables" is not enforceable by an Airtable PAT.** PAT scopes
   (`data.records:read` / `data.records:write`) are granted **per base, not per table**. A token that can
   write `LabOS Raw Test Results` in that base can technically write every other table in it. Their stated
   guarantee is a *convention*, not a permission — see §3.1 for the two ways to make it real.

Everything else is additive: the schema is missing the fields our hardware tests actually produce (peak
pressure, per-gauge deflection, cycle counts), a correction-reference field their own immutability rule
requires, and the schema version Luis asked for. Detail below.

---

## 1. What their doc gives us (and what it closes)

| Item | Status for us |
|---|---|
| Separate test base `IFET Test Base For LabOS` (`appYBTqIL43pmS0xN`) | ✅ **Closes gap G** (sandbox base). W3/W4 can be built safely. |
| Read-only field list for Projects / Mock-Ups / Protocols / Sections / Walls+Scheduling | ✅ Fills the empty middle column of our mapping §1 — first real field names. Mapping rows go 🟡 → 🔵 In review. |
| One writable table `LabOS Raw Test Results`, ~34 fields | ✅ Matches our mapping §2 intent; **simpler than our proposal** (they do not want us touching Projects/Mock-Ups/Protocols at all). Adopt it. |
| Roll-ups handled by Airtable/Make automations (§6) | ✅ **Closes gap E** and confirms our pre-closed decision #8. LabOS writes one record per attempt, nothing else. |
| Required-always vs. test-specific field split (§4) | ✅ Answers our mapping §3 open item, subject to the additions in §4 below. |
| Walls / positions / reservations read-only, managed in Airtable | ✅ Clear ownership. We snapshot, never write back (HM point 4 — agreed, see §3.4). |
| Photos + Excel + Report as links | ✅ Confirms our pre-closed decision #6 — **provided the `Photos` field type is URL/long-text, not Attachment** (HM point 6). |
| Scoped PAT | ⚠️ Leaked in the PDF — must be revoked; see §2. |

**Plan impact:** gaps **E** and **G** close; decisions **#4** (LabOS computes pass/fail → writes `Test Result`),
**#6** (photo links), **#8** (Airtable owns roll-ups) are confirmed by the counterparty. The remaining W3 gate
is no longer "give us field names" — it is now **"make the read-side test parameters machine-readable"** (§5).

---

## 2. Security — do this first, before any schema debate

1. **Revoke the PAT printed in §1 of their PDF.** Both HM and Luis already called this; treat it as
   compromised regardless of who has seen it. A Google-Docs-exported PDF also leaves the token in the
   document's **version history**, so removing the line from the doc is not sufficient — revocation is the
   only real fix.
2. **LabOS has not stored it.** It is in no config, `.env`, repo, or CI secret, and the API has not been
   called with it. **Action on us:** delete `~/Downloads/IFET-Phase-2-LabOS-Doc.pdf` (and any re-download)
   once the reply is sent — it is the only copy on our side, and it is the whole credential in plaintext.
   No copy of the token appears in this repo or in any Notion page.
3. **Send the replacement out-of-band** — a secrets manager share (1Password/Bitwarden) or Airtable's own
   invite flow. Not in a document, not in email or chat.
4. **Scopes we need on the new token:** `data.records:read` (read base), `data.records:write` (results table's
   base), and **`schema.bases:read`** — that last one lets us bind to **field IDs** instead of field names
   (§3.2) and detect schema drift automatically instead of failing at runtime.
5. **Our side of the hygiene, already tracked:** the token lives server-side only in a gitignored
   `.env`/secret store (P0, Ref 42). It must **never** reach `deployment/config/config.json` or
   `src/ifet_ui_react/config.json` in ifet-management — those are served to the browser. This is a standing
   watch item from the branch reconcile.

---

## 3. Required changes to their doc (the ten we're sending back)

### 3.1 The "read-only" guarantee needs a structural fix, not a promise
PAT scopes are **base-level**. Two options:
- **Preferred:** keep `LabOS Raw Test Results` in a **separate base** from the read-only tables, and issue us
  *two* tokens — read-only on the ops base, write on the results base. Then the guarantee is enforced by
  Airtable, not by our good behaviour. (Cost: cross-base links become text IDs — which is what we want
  anyway, see §3.3.)
- **Acceptable:** one base, single token, and the guarantee is enforced in LabOS code (a single
  write-allowlist constant — the client refuses any table but the results table) plus Airtable's per-record
  revision history for audit. We'll implement the allowlist either way.

### 3.2 Bind by **field ID**, not field name
Airtable writes accept `fld…` IDs as keys in the `fields` object, and reads support
`returnFieldsByFieldId=true`. If we bind by name, any rename on the Airtable side silently breaks the
integration; bound by ID, renames are free. **Ask:** grant `schema.bases:read` and let us pin field IDs; we'll
keep a generated snapshot of the base schema in our repo and diff it on every deploy.

### 3.3 Are the `Airtable … ID` fields plain text or link-to-record?
This changes our payload shape materially (`"recXXX"` vs `["recXXX"]` + typecast) and it is not stated.
**Our proposal:** they are **plain text** fields on the raw-results table holding `rec…` IDs. LabOS writes
strings; the Airtable automation resolves them into real linked-record fields on their side when it processes
the raw row. That keeps LabOS out of Airtable link semantics permanently and survives their table
refactors — the cleanest separation of concerns available.

### 3.4 Blanks: **omit the key**. Never `""`, never `null`, never `0`, never `"N/A"`
Replacing their §5. Precise semantics we will implement:
- **Key absent** = "this field does not apply / no value" → the cell is left untouched.
- **`null`** = "explicitly clear this cell". LabOS will **never** send it (records are immutable once
  terminal, §3.5) — reserved so the meaning isn't ambiguous later.
- **`""`** = never sent. Valid only on text fields anyway, and unsafe as a general rule.
- **`0`** is a real measurement, not a blank — a 0 PSF reading means zero pressure and must be sent as `0`.
- Required identifiers and the always-required set are never omitted.
We'll verify the exact 422 behaviour per field type on the sandbox base and append the results to the write
contract, so both sides have evidence rather than assumptions.

### 3.5 Immutability needs a **field**, not just a rule
We fully agree with HM point 3: once `Test Status` is `Completed` or `Aborted`, the record is final and
corrections arrive as a **new record referencing the old attempt**. But "referencing the old attempt" is
impossible with the current schema — there's nothing to put the reference in. **Add:**
- `Corrects Attempt ID` (text) — the `LabOS Attempt ID` this record supersedes.
- `Correction Reason` (long text) — why.
Then Airtable's automation can mark the prior record `Superseded` and exclude it from roll-ups. **LabOS
enforces the lock at source:** once we write a terminal status for an attempt, that attempt ID is never
written again by our sync worker. Note honestly that a write-scoped PAT *can* technically PATCH an old record
— so the lock is a LabOS invariant plus an Airtable audit, not an API-level permission.

### 3.6 Upsert on `LabOS Attempt ID` — and what that requires of the field
Agreed and already our design (mapping §0 / contract §5). Mechanism: Airtable's
`PATCH /v0/{baseId}/{tableId}` with `performUpsert: { fieldsToMergeOn: ["LabOS Attempt ID"] }`, ≤10 records
per request. Two constraints for them:
- `LabOS Attempt ID` must be a **plain text field, not a formula/rollup/computed** field — computed fields
  can't be used in `fieldsToMergeOn`.
- Airtable can't enforce uniqueness. **LabOS guarantees it**: the attempt ID is a UUID/ULID minted once when
  the attempt is created locally, stable across retries, reboots, and offline queue replays. That is what
  makes a timed-out retry idempotent instead of duplicating.

### 3.7 Fixed value lists (HM point 5) — our proposed option sets
Please create these as single-selects with exactly these options, and **don't let LabOS write free text into
them**. If a value we need is missing, that's a contract change, not a new option invented at runtime:

| Field | Options | Notes |
|---|---|---|
| `Test Type` | `Static Load`, `Cycles`, `Impact`, `Forced Entry`, `ANSI Z97.1` | The 5 LabOS test types. Additions = contract bump. |
| `Test Status` | `In Progress`, `Completed`, `Aborted` | LabOS writes only these three. Airtable may add `Superseded` for its own use (§3.5) — LabOS never writes it. |
| `Test Result` | `Pass`, `Fail`, `Inconclusive` | Omitted while `In Progress`; required when `Completed`. |
| `Unit` | `PSF`, `PSI`, `in`, `mm`, `lbf`, `N`, `cycles`, `s` | Pressure results are **PSF** (the rig reads PSI and scales ×144). |
| `Testing Continued` | `Continued`, `Stopped` | |
| `Retest Required` | checkbox → we send explicit `true`/`false` | Omission must not be read as `false`. |
| `Abort Reason` *(new)* | `Specimen Failure`, `Equipment Fault`, `Operator Stop`, `Power/Comms Loss`, `Other` | `Aborted` is terminal; a reason field beats parsing Notes. |

### 3.8 `Schema Version` (Luis's ask) — accepted, with a concrete shape
Add `Schema Version` (text) to the results table; every record LabOS writes carries the contract version it
was produced under, starting `1.0`. Rules: **additive changes bump the minor** (`1.1` — new optional field,
new select option), **breaking changes bump the major** (`2.0` — field removed/retyped/renamed-by-ID,
semantics changed). Both sides pin a version; Airtable automations can branch on it, and old records stay
interpretable forever. We'd also like the *read* side versioned — simplest form is one `Integration Meta`
table with a single row holding `Schema Version` + `Last Changed`, which we poll and log on drift.

### 3.9 Snapshots vs. live data (HM point 4) — agreed, make it explicit in the doc
The wall/position/reservation fields and `Required Value` / `Required Unit` we write are **values as of test
time**, not live pointers. They exist so a raw result is self-describing and auditable years later.
Consequence both sides should accept: if Airtable later moves a reservation, the historical result keeps the
old snapshot **by design** and must not be "corrected". Recommend renaming to make it unambiguous —
`Wall Reservation Start (at test)` etc. — or documenting it in the field description.

### 3.10 `Sync Status` should not be a LabOS-written field
A field whose failure states are `Sync Failed` / `Retry Required` can never be written *when the sync fails* —
if we can reach Airtable to report the failure, there was no failure. It's incoherent as a synced field, and
it costs an extra write per attempt. **Proposal:** drop it, and let Airtable use its own `Created time` /
`Last modified time` for arrival tracking. LabOS keeps the real queue state (`Pending` / `Synced` /
`Sync Failed` / `Retry Required`) locally and shows it in the LabOS UI, which is where an operator can act on
it. If Airtable wants a coarse signal, we can write `LabOS Updated At` (already in the schema) — it's a
timestamp, and a missing/stale one is the honest indicator of an unsynced attempt.

---

## 4. Fields we need **added** to `LabOS Raw Test Results`

The current schema can't represent what the rig actually produces. `Measured Value` + one `Deflection Value`
collapses a static-load test to two numbers; a real one yields a held pressure, a peak pressure, and a
deflection reading per gauge at each load step.

| # | Field | Type | Why | Priority |
|---|---|---|---|---|
| 1 | `Max Pressure Achieved` | Number (PSF) | Peak pressure reached, distinct from the held/target pressure in `Measured Value`. For a failure test this **is** the result. Firmware P3 captures it. | **Blocking** |
| 2 | `Result Detail (JSON)` | Long text | One extensible field carrying test-type-specific structure — per-gauge deflection readings with timestamps, load-step table, impact drop sequence, forced-entry attempt log. Read with `Schema Version`. **This is the field that stops us renegotiating the schema for every test type.** | **Blocking** |
| 3 | `Deflection Unit` | Single select (`in`, `mm`) | `Unit` describes the pressure; deflection needs its own unit or the number is meaningless. | **Blocking** |
| 4 | `Corrects Attempt ID` + `Correction Reason` | Text + long text | Required to make their own immutability rule (§3.5) implementable. | **Blocking** |
| 5 | `Schema Version` | Text | Luis's ask (§3.8). | **Blocking** |
| 6 | `Cycles Required` + `Cycles Completed` | Number + Number | A cyclic test's primary result is "did it complete N cycles". Currently unrepresentable. | High |
| 7 | `Required Unit` | Single select (same list as `Unit`) | They snapshot `Required Value` but not its unit; the record isn't self-describing without it. | High |
| 8 | `Abort Reason` | Single select (§3.7) | Terminal state deserves a structured cause. | High |
| 9 | `Test Rig` | Single select (`System 1`, `System 2`) | Which IFET rig ran it. We have it free; a lab needs it for traceability and for correlating a suspect result to a rig. | Medium |
| 10 | `LabOS Version` | Text | Firmware/LabOS build that produced the numbers. Standard metrology traceability; also how we'd ever explain a historical anomaly. | Medium |
| 11 | `Result Rationale` | Long text | How pass/fail was determined (e.g. "max deflection 0.42 in ≤ L/175 limit 0.55 in"). LabOS computes pass/fail, so it should show its work. | Medium |

**Not asked for, deliberately:** separate `Impact Results` / `Forced Entry Results` / `ANSI Z97.1 Results`
columns (our earlier mapping §2 proposed these). Their generic `Test Result` + `Measured Value` + the new
`Result Detail (JSON)` covers all five test types with fewer fields and no schema churn when a sixth arrives.
Withdrawing that ask is a simplification, and it's theirs to accept.

---

## 5. The read side is the real risk — bigger than any write-field debate

Their read schema exposes test requirements as **`Required Test Value`, `Required Unit`,
`Required Testing Parameters`** at the Protocol Section level. If `Required Testing Parameters` is free text,
**the operator still has to read it and type numbers into LabOS — which is the entire problem the integration
exists to eliminate.** One scalar `Required Test Value` cannot express what a static-load test needs.

A static load test needs, as discrete machine-readable values: **inward design pressure**, **outward design
pressure**, **hold time**, **load-step/loading sequence**, and **number of deflection points/gauges**. A
cyclic test needs **cycle count** and **pressure range**. These were rows 5–9 of our mapping §1 and they have
no home in their current read schema.

**Ask (pick either, per test type):**
- **(a) Discrete fields on Protocol Sections** — `Design Pressure Inward (PSF)`, `Design Pressure Outward
  (PSF)`, `Hold Time (s)`, `Cycles Required`, `Deflection Points`, `Loading Sequence (JSON)`. Most robust; we
  can validate types and refuse a malformed protocol before the rig moves.
- **(b) One `Required Testing Parameters (JSON)` long-text field** with an agreed shape per `Test Name`.
  Faster for them, and acceptable to us if the shape is fixed and versioned.

Free text is the one outcome that doesn't work — we'd be shipping a copy-typing UI with extra steps.

**Two smaller read-side asks:**
- **Give us named views to read, not raw tables** — e.g. `LabOS – Scheduled Tests`, `LabOS – Active Projects`.
  We read `?view=…`, they own the filter logic. Their scheduling changes then don't become our bug.
- **Confirm date/time format and timezone.** We will send **ISO 8601 UTC** (`2026-07-29T14:03:00Z`) on all
  date/datetime fields and let their field config handle display timezone. IFET operates US/Eastern, so an
  ambiguous local timestamp is a real off-by-hours risk on overnight cyclic runs.

---

## 6. Open questions for them (short list, ordered)

> **View, not source.** The canonical open-items list is `labos-airtable-write-contract-v0.3.md` §10.
> This section is the subset worth raising conversationally, ordered by how much it unblocks.

1. `Photos` field type — URL/long-text (multiple links newline-separated), or Attachment? We need the former
   (HM point 6). Related: do `Report Link` / `Excel File Link` need to be **publicly** reachable, or will
   Airtable users be authenticated to LabOS? That decides whether our links carry a signed token.
2. Are the `Airtable … ID` fields text or link-to-record? (§3.3)
3. Read structure for test parameters — option (a) or (b)? (§5)
4. Separate base for the writable table, or one base + code-enforced allowlist? (§3.1)
5. `schema.bases:read` on the new token so we can bind by field ID? (§3.2)
6. Are the 8 wall/reservation snapshot fields **required** on every record, or only when a wall position was
   reserved? Their §4 lists them as not-always-required, but a static test always occupies a wall — confirm.
7. Which side owns `Test Name` canonically — is it free text or does it come from the Protocol Section's
   `Test Name`? If the latter, we echo their exact string.
8. Confirm we may create records for `In Progress` (a test starts, and the row appears immediately with a
   partial payload, then upserts to `Completed`), or whether they want a single write only at terminal state.
   Our preference is the former: it gives Airtable live visibility and it's what makes the upsert key earn
   its keep.

---

## 7. Reply to send — final wording

Written in the same register the Airtable team used in their own review notes: short numbered points,
colleague-to-colleague, no document formality. **This is the text that goes out**, verbatim.

Ordering is deliberate — the three confirmations of HM's points come first (cheap agreement, builds the
premise), then the field gaps, then the two items that need an actual decision from them (§4 contradiction,
read-side structure), then the token and the access note. Point 6 appears in nobody's review, including HM's:
their always-required `Testing End Date` silently forbids creating the row when a test starts.

```text
Thanks Huzaifa. Went through the doc — structure works for us as-is, and we're
adopting it. One writable table, you own scheduling and rollups, we write one row
per test attempt and nothing else.

Also agree with all of HM's points and Luis's.... that's already how LabOS is
built. A few things before we build against it....

1. On the "" rule — agreed with HM, we can't send "".... Airtable rejects it on
number/date/select. We'll omit the key entirely when a field doesn't apply. One
exception worth flagging: 0 is a real reading, not a blank.... a genuine zero
pressure result gets sent as 0.

2. Upserts on LabOS Attempt ID — yes, that's our design.... two things needed on
your side though: it has to be a plain text field (computed fields can't be used
as a merge key), and Airtable can't enforce uniqueness, so we guarantee it. UUID
minted before the first send, reused on every retry and offline replay.

3. Locking after Completed/Aborted — agreed, and we enforce it at our end....
but "a new record referencing the old attempt" needs somewhere to put the
reference. Can you add Corrects Attempt ID + Correction Reason? Right now there's
no field for it.

4. The schema can't hold what the rig actually produces yet.... we need
Max Pressure Achieved (peak is different from the held pressure, and on a failure
test the peak IS the result), Deflection Unit (Unit describes the pressure, so
the deflection number has no unit of its own), and one Result Detail (JSON) long
text for per-gauge deflection, load steps, impact sequences. That last one means
neither side has to touch the schema again when a 6th test type shows up. Plus
Cycles Required / Cycles Completed for cyclic.

5. Schema version per Luis — agreed.... every row carries it, starting 1.0.
Additive changes bump the minor, breaking changes the major. Would help to
version the read side too, even just one row we can poll.

6. Small contradiction in section 4.... Testing End Date is in the always-required
list, but a test that's still In Progress doesn't have one. Either drop it from
that list — then we can create the row when a test starts, so you'd see what's on
the walls live — or tell us you want a single write at the end only. As written
the doc rules out the first.

7. Biggest one, and it's on the read side.... if Required Testing Parameters is
free text, the operator still has to read it and type the numbers into LabOS,
which is the thing we're removing. A static test needs discrete values — inward
and outward design pressure, hold time, loading sequence, gauge/deflection count.
Cyclic needs cycle count and pressure range. Either discrete fields on Protocol
Sections or one agreed JSON shape, both work for us. Free text doesn't.

8. Sync Status — we'd suggest dropping it.... a field whose values include
"Sync Failed" can never be written at the moment the sync actually fails. We keep
that state in LabOS where the operator can act on it, and LabOS Updated At plus
your Created time gives you arrival tracking anyway.

9. Token — please revoke the one in the PDF.... it's also in the doc's version
history, so revoking is the only complete fix. We haven't stored or used it. On
the new one, could you include schema read access alongside record read/write?
That lets us bind to field IDs instead of names, so renaming a field on your side
never breaks the integration.

10. One note on access.... an Airtable token scopes per base, not per table, so
"read-only on the existing tables" isn't something the token can enforce while
the writable table lives in the same base. Own base would make it real.
Otherwise we enforce it in code with a one-table allowlist — fine either way,
just flagging it so it's a deliberate choice.

Also, we're dropping our earlier ask for separate Impact / Forced Entry / ANSI
result columns.... your Test Result + Measured Value plus that JSON field covers
all five test types with fewer columns.

Once the new token's in, we'd like to run read-only checks first — whoami, the
base schema, a few sample records — and send you back a full schema report within
a day. Then a handful of write probes against the results table only, tagged
LABOS-PROBE so you can filter and purge them. Just let us know if that's OK.

Happy to get on a call — 45 minutes would close most of this faster than docs.
```

**Send alongside it:** the two Notion links — *LabOS Response — Airtable Schema Review & Write Contract v0.2*
(the field-by-field detail behind points 1–10) and *LabOS ↔ Airtable — Integration Status & Verification
Report* (the ownership boundary, what we've verified, and the exact requests we're asking approval for).
The message carries the asks; the pages carry the evidence.

---

## 8. What LabOS does next — no longer blocked

**This week (W1), none of it gated on their reply:**
1. ✅ **P0 / Ref 42 — secret store. DONE 2026-07-29** (`bf4db01`, `feature/labos-airtable`). Every credential
   out of `compose.yaml` into a gitignored `.env`; `app/config.py` as the single server-side entry point (token
   never printed, one-table write allowlist, refuses to emit a localhost link); `check-secrets.sh` guard;
   gated migration runbook in `deployment/SECRETS.md`. Rehearsed off-node under an isolated compose project —
   evidence in SECRETS.md §2.1a. **Not deployed:** the management node is production, so deployment is gated on
   a maintenance window and, ideally, a test node.
2. **P0 / Ref 43 — Airtable HTTP client** on `feature/labos-airtable`: single-table write allowlist,
   5 req/s limiter, 429/5xx retry with backoff, `performUpsert` helper, field-**ID** binding table.
3. **Schema introspection tool** — `GET /v0/meta/bases/{baseId}/tables`, snapshot the base schema to the
   repo, and diff on every deploy so an Airtable-side rename fails loudly at deploy time rather than
   silently at test time. Runs the moment the rotated token lands.
4. **Write contract v0.2** — `docs/labos-airtable-write-contract-v0.3.md` (their table + our envelope +
   the omit-vs-null rule + upsert + immutability), the artifact both teams build against.
5. **Mapping doc update** — fill the Airtable column from their PDF, rows 🟡 → 🔵 In review, add the §4
   rows as `Requested`, replace the old Impact/Forced-Entry/ANSI rows with `Result Detail (JSON)`.

**W2, also ungated:** P1 append-only attempt model on the existing `TestResult` hierarchy, carrying every
identifier + the new result fields. **Firmware P3** is unchanged and now externally justified — `Max Pressure
Achieved` and per-gauge deflection are exactly what §4 items 1–3 need from the rig.

**Still gated on them:** W3 requirements-IN needs the read-parameter decision (§5); W4 results-OUT needs the
field additions (§4) and the base/token decision (§3.1). Neither blocks starting.

---
*Source doc reviewed 2026-07-29 from `~/Downloads/IFET-Phase-2-LabOS-Doc.pdf` (6 pp, Google Docs export). The
PAT it contains is treated as compromised and was never used or stored by LabOS.*
