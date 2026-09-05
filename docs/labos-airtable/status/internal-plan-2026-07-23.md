# LabOS ↔ Airtable Integration — Internal Engineering Plan

> **Current update — 2026-09-06:** Design is decided in `../contract/write-contract-v0.4.md`;
> A1–A8 are closed. Testing Base field setup is authorized but not applied. The 66-row register separates
> decisions from delivery. Existing client/P1/outbox code remains groundwork; the programme/run flow,
> migrations and v0.4 acceptance are not delivered. No runtime code or production deployment is part of closure.
> Next implementation: M1 Testing Base diff/fixtures → M2 local PostgreSQL import/run/offline replay →
> M3 APIs/review/evidence → actual-change document → coordinated cutover. UI and water integration deferred.
> Independent source verification, measurement quarantine and automation/deployment checks remain.
> All five Test Type options, datetime Test Date and Correction Reason existed at the September 5 baseline.
> The September 6 notice is NOT SENT. No further field-design approval question remains.
> **The older assessment below is historical.** Its dates, approval waits, field gaps and test counts are
> dated observations, not current instructions. October 9 is an earlier target, not revalidated here.

**Author:** Abdelrahman · **Date:** 2026-07-23 · **Updated:** 2026-07-29 · **Status:** Working (internal) · **Mode:** Solo
**Companion (external) view:** the *Delivery & Progress Tracker* dashboard on Notion (Epic **IFET-32**).

> ### Update 2026-08-23 — **the gate opened.** Gap I answered (with a defect), gap J closed
> Both PATs delivered. The schema probe and a record dump ran against **both** bases — read-only, nothing
> written to either. Evidence: **`docs/labos-airtable/evidence/live-probe-findings-2026-08-23.md`**. Canonical open items:
> **`docs/labos-airtable/evidence/write-contract-v0.3-superseded-2026-09-06.md` §10**, now 22 items.
>
> **Closed:** §10.1 `Photos` is `url` · §10.2 the four ID fields are plain text as proposed · §10.5
> `Impact Result` is free text · §10.10 **PAT delivered** · §10.11 null/blank table verified · §10.16
> `Test Result` is `Passed`/`Failed` — **their example was right and our contract was wrong.**
>
> **Gap I / §10.3 is answered** — the read side is **row-per-parameter** on `Protocol Sections`
> (`Section Name` + free-text `Value`), which is neither option either side proposed. Addressable, so
> **W3 is unblocked on structure.** Untyped, so the `Required Value` / `Required Unit` ask stands.
>
> **⚠️ New, and worse than a missing spec — §10.19.** Their PDF extractor drops blank cells instead of holding
> the column position, so requirement values are shifted one column. Their sample job reads
> `DP (+) (PSF) = 9` where the proposal says `+60/60`. Those values drive the rig. **Standing rule: nothing
> reads requirements from Airtable for a live test until they fix the extractor.** W3 may be *built* against
> the structure; it must not be *trusted* with a rig.
>
> **Also new:** `Test Type` has only `Static Load`, so 4 of 5 test types cannot be written (§10.17, blocking) ·
> `Abborted` is misspelt in their base (§10.18) · `Test Date` is a `date`, so duration is unrepresentable
> (§10.20) · confirm their automation owns the `Protocol Sections` roll-up (§10.21) · their sample uses `001`
> where §3 specifies a UUID (§10.22).
>
> **Next:** verification stage 3 — a live upsert round-trip into the testing base. Last thing before W2.

> ### Update 2026-08-22 — their guide **v2** landed; gap G re-based, gap I still open
> *IFET Phase 2 · LabOS × Airtable API Integration Guide* **v2** (2026-08-17) supersedes the v1 schema doc
> reviewed below. Delta and the outbound reply: **`docs/labos-airtable/correspondence/v2-guide-reconciliation-2026-08-22.md`**.
> Canonical open items: **`docs/labos-airtable/evidence/write-contract-v0.3-superseded-2026-09-06.md` §10**.
>
> **Changed:** the sandbox base ID below is **stale** — the testing base is now `app4oXS3Kd5IKWgJ7` and
> production is `app0OCunbmuXl7Hc9`; all nine table IDs are published (contract §0.1). **4 of the 11
> requested fields granted**, including the JSON valve (`Complete LabOS JSON Response`).
> **New blockers:** the `Test Date` collapse (§10.13) and the absent correction fields (§10.14).
> **Unchanged and now the critical path:** gap **I** / contract §10.3 — v2 still does not specify how test
> requirements come out of Protocol Sections. **W3 stays blocked.**
>
> **PAT status:** v2 correctly contains no token. The v1 leak is remediated; LabOS never used or stored it.
> ~~The testing PAT is still not delivered~~ — **delivered 2026-08-23; see the 2026-08-23 update above.**

> ### Update 2026-07-29 — the Airtable team answered; three gaps close, one new one opens
> Their *IFET Phase 2 · LABOS Sample Schema* doc landed (sandbox base + read-only field list + a single
> writable `LabOS Raw Test Results` table). Full review, the ten required changes, the eleven fields we need
> added, and the reply draft: **`docs/labos-airtable/correspondence/team-doc-review-2026-07-29.md`**. The write spec both
> teams build against: **`docs/labos-airtable/evidence/write-contract-v0.3-superseded-2026-09-06.md`**.
>
> **Closed by their doc:** gap **G** (sandbox base — provisioned, ~~`appYBTqIL43pmS0xN`~~ **superseded 2026-08-22 → `app4oXS3Kd5IKWgJ7`**) · gap **E**
> (roll-ups = Airtable automations, confirming decision **#8**) · decision **#6** (photos = links) and
> decision **#4** (LabOS computes pass/fail → writes `Test Result`) both confirmed by the counterparty.
> **Also simpler than planned:** LabOS writes *one table*, never Projects/Mock-Ups/Protocols — so the P4
> write surface shrinks, and our separate Impact/Forced-Entry/ANSI result columns are **withdrawn** in favour
> of one `Result Detail (JSON)` field.
>
> **New blocking gap I — read-side parameters are not machine-readable.** Their read schema exposes
> requirements as `Required Test Value` / `Required Unit` / `Required Testing Parameters`. If the last is free
> text, the operator still re-types the numbers and P2 delivers nothing. This — not field names — is now the
> real W3 gate. *(~S once decided; blocked on them.)*
>
> **Secret hygiene, immediate:** their PDF contained a live PAT. Revocation requested; LabOS never stored or
> used it. P0/Ref 42 (`.env` externalization) **landed 2026-07-29** (`bf4db01`) — ahead of the replacement token, as intended.

> This is my private, complete plan to finish **all** LabOS work for the Airtable integration —
> the superset of the dashboard. The dashboard shows the Airtable team only the clean deliverable
> milestones (P0–P6, management side). This doc adds what stays off the board: the off-dashboard
> firmware result-capture, the branch reconcile, the decisions I must pre-close, and the gaps found
> reviewing the contract + mapping. It is sequenced around **"contract active" (v1.0)** as the trigger.

---

## 0. TL;DR — the one thing that shapes everything

The **field bindings are the only thing gated on the Airtable team.** Contract §2/§5 give a **stable
canonical envelope** that needs no field names. So I front-load every phase that builds against the
canonical shape (P0, P1, firmware P3) *now*, and the moment the mapping doc reaches 🟢 **Agreed**
I only have to wire a **thin binding layer** (read mapping + upsert mapping) and cut over.

**Two-track framing:**
- **Track A — build now, contract-independent:** P0 foundations, P1 schema/identity (canonical),
  firmware P3 result-capture, branch reconcile, my own decisions.
- **Track B — unlocked when contract goes active:** the read/write field bindings (P2 mapping,
  P4 upsert mapping), backfill, cutover, v1.0 sign-off.

---

## 1. Ground-truth baseline (the reconcile — internal only)

Verified 2026-07-23 against the live fleet + repos. **The 2026-07-20 readiness eval read `main`;
production actually runs `latest`, which is further along.** This reconcile lives here, not on the board.

| Component | Deployed reality | Effect on plan |
|---|---|---|
| **ifet-management** | Node runs branch **`latest` @ 5775e87**. Alembic **live with ~28 migrations**; DB has `test_results`, `cyclic_test_results`, `static_test_results`, `project_parents`. | **P0 migration task ≈ done** (verify only). **P1 attempt model** builds on the existing `TestResult` hierarchy, not greenfield. |
| **ifet-firmware** | Nodes run **`dev` @ 3642711** (usual uncommitted prod edits). Result POSTs send **deflection only**; no actual/max pressure; no external IDs. | Firmware P3 gaps all confirmed open (off-dashboard). |
| **Airtable surface** | `grep -ril airtable` on the live node → **zero**. No `integrations/`, no `sync_queue` table, no `AIRTABLE_*` env. | Entire Airtable surface is genuinely greenfield. |

**Reconcile action (pre-W1, ~0.5 day):** confirm `latest` is the integration baseline, branch
`feature/labos-airtable` off it, and re-point the eval's `main`-based line numbers. *Not a dashboard row.*

---

## 2. Contract & mapping readiness

- **Contract** (`v0.3 DRAFT` as of 2026-08-22; was `v0.2`, was `v0.1`): envelopes, identifiers, sync state machine,
  retry policy, auth — all stable and sufficient to build Track A against. v0.2 adds the real Airtable
  field names, the omit-vs-null rule, the upsert/immutability model, and the retest-vs-correction
  distinction. Ratifies to **v1.0** when contract §10 (the canonical open-items list) closes.
- **Mapping doc:** complete LabOS proposal but **0% Agreed** — every row 🟡 Proposed, Airtable-field
  column empty. **All ratification work is the Airtable team's / Luis's**, none is mine.
- **My ask into the Airtable team (send W1, day 1):** (a) fill real table + field names/types,
  (b) confirm identifier scheme (record IDs), (c) close the 6 §5 open items, (d) **provision a
  separate staging/sandbox base** for me to build against (gap G).

---

## 3. Decisions I pre-close (so "contract active" → I just build)

My recommended call for each, so nothing stalls once bindings land:

| # | Decision | My call | Rationale |
|---|---|---|---|
| 1 | Migration tool | **Adopt existing Alembic on `latest`**, retire `create_all` | Already in prod; free. |
| 2 | Hierarchy depth | **Store Airtable IDs + display fields only**; Airtable stays authoritative; reuse `project_parents` | Lightweight; avoids re-modeling their hierarchy. |
| 3 | Requirements materialization | **Snapshot into local rows at selection time** + cache last payload | Offline-safe, auditable, matches contract §4 callout. |
| 4 | Pass/fail ownership (gap C) | **Compute in management** from captured pressure vs. design pressure | Keeps a *required* write field **on-dashboard**; firmware only supplies actual/max pressure. |
| 5 | Sync worker shape | **In-process asyncio/APScheduler task** in report-api (not a separate service) | Fewer moving parts for solo; serializes to honor 5 req/s (§3). |
| 6 | Photo storage (gap A) | **LabOS-hosted URLs**, not Airtable attachments | Reuses the reachable-origin work (gap B); avoids binary upload + attachment token scope. |
| 7 | Structured formats (gap D) | **JSON-in-long-text v1**; upgrade to linked child records only if Airtable wants it queryable | Unblocks P1 schema now; cheap to send. |
| 8 | Status roll-up (gap E) | **Prefer Airtable automations** own the roll-up; LabOS writes only the result record | Fewer LabOS calls, less coupling. Confirm with Airtable team. |
| 9 | Rollout (gap F) | **Dark-launch behind a flag**, backfill Airtable IDs for active projects, cut over per new project | Additive, reversible, no big-bang. |

---

## 4. Gaps folded in (from the contract + mapping review)

- **A · Photo pipeline** — new: capture → LabOS-hosted store → URL in `photo_links`. Feeds P5. *(new work, ~M)*
- **B · Reachable report origin** — management needs a stable external base URL so `labos_report_link`
  + photo URLs resolve. Bigger than the P6 localhost cleanup; do it **before** first real write. *(~S–M)*
- **C · Pass/fail in management** — implemented via decision #4; add criteria + compute step. *(~S)*
- **D · Structured-format modeling** — decision #7; affects P1 columns. *(folded into P1)*
- **E · Roll-up** — decision #8; confirm at ratification so P4 write count is fixed. *(decision)*
- **F · Backfill** — one-off script to stamp Airtable IDs onto existing active projects. *(~S, in W5 cutover)*
- ~~**G · Sandbox base**~~ — ✅ **CLOSED**, re-based 2026-08-22. Their v2 guide replaces the original sandbox
  with **`LabOS Testing Base` (`app4oXS3Kd5IKWgJ7`)**; production is `app0OCunbmuXl7Hc9`. The earlier ID
  `appYBTqIL43pmS0xN` is **retired — do not use it.** W3/W4 can be built safely. *(Still gated on the testing
  PAT being delivered out-of-band; the v1 token leaked in their PDF and was never used by LabOS.)*
- ~~**E · Roll-up**~~ — ✅ **CLOSED 2026-07-29.** Their §6 puts all Project/Mock-Up/Protocol roll-ups on
  Airtable automations, exactly as decision #8 proposed. LabOS writes one attempt row, nothing else.
- **I · Read-side parameters** — 🟡 **ANSWERED 2026-08-23, and it split in two.**
  *Structure:* neither discrete fields nor versioned JSON — it is **row-per-parameter** on `Protocol
  Sections`: one record per requirement line, `Section Name` (e.g. `DP (+) (PSF)`) + free-text `Value`.
  Addressable, so **W3 is unblocked on structure** and the parser is ~S as estimated. Still untyped —
  `9`, `Full` and `+60/60` share one text column and the unit lives in the *name* — so the ask for
  `Required Value` + `Required Unit` stands (contract §10.3).
  *Data:* ❌ **and this is the new blocker.** The values do not match the source proposal — their extractor
  drops blank cells instead of holding column position, so everything shifts one column left (§10.19).
  LabOS cannot detect it; every shifted value is individually plausible. **W3 may be built, not trusted.**
  See `docs/labos-airtable/evidence/live-probe-findings-2026-08-23.md` §5.
- ~~**J · Field-ID binding + schema-drift detection**~~ — ✅ **CLOSED 2026-08-23.** `schema.bases:read` arrived
  on both PATs; the probe writes the `fld…`-ID snapshot and both bases are committed under
  `docs/labos-airtable/schema/`. Bonus: the testing base is a structural *clone* of production (identical table and
  field IDs), so one snapshot binds both environments and a cutover cannot silently re-point.
- **H · Firmware→mgmt `/trials` contract** — extend payload for IDs + pressure; Ref 53 (fw, off-board)
  ↔ Ref 54 (mgmt, on-board) must land together. *(coordinate across the seam)*

---

## 5. Full work breakdown (management on-board + firmware off-board + gaps)

Points re-sized to the `latest` reality. **[D]** = on dashboard (has a tracker Ref). **[off]** = off-dashboard.

### Track A — build now (contract-independent)
- **P0 Foundations** — [D 42] server-side `AIRTABLE_TOKEN/BASE_ID` secret · [D 43] `app/integrations/airtable/` HTTP client skeleton · [D 41→verify] confirm Alembic baseline · **+ gap B** reachable origin. (~5)
- **P1 Schema & identity** — [D 44] external-ID cols · [D 46] append-only attempt model on existing `TestResult` · [D 45] Mock-up/Protocol/Section as lightweight ref (decision #2) · [D 47] results-out fields matching §5 envelope · **+ gap D** JSON columns. (~6)
- **Firmware P3** *(off-dashboard — tracked in my firmware docs)* — [off 51] capture actual & max pressure in `holding_time`/`automatic_cycling` · [off 52→moved to mgmt per decision #4] supply data for pass/fail · [off 53] thread IDs through `start` + result POST · pairs with [D 54] persist attempts on `/trials`. **On-rig testing required.** (~8)

### Track B — unlocked when contract active (needs mapping 🟢 Agreed)
- **P2 Requirements-IN** — [D 48] Airtable read service + **field binding** · [D 49] replace hardcoded auto-seed · [D 50] Project→Mock-up→Protocol→Test selection UI + requirements cache. (~8)
- **P4 Results-OUT + sync** — [D 55] durable `sync_queue` + in-process worker (decision #5) · [D 56] idempotent upsert + **field binding** · [D 57] retry/backoff/error-class per §6 · [D 58] sync-status UI (states map 1:1 to §6). (~13)
- **Cutover** — gap F backfill · flip flag · e2e with Airtable team on the sandbox then prod.

### Track C — feeds the envelope; my decisions, not contract-blocked
- **P5 Manual screens** — [D 59] Impact (wire modal + endpoints) · [D 60] Forced-Entry + ANSI Z97.1 model/API/form · [D 61] pre-filled context · **+ gap A** photo pipeline. (~8 + photo)
- **P6 Hardening** — [D 62] UI cleanup / route drift · [D 63] token rotation + least privilege · [D 64] sync observability · [D 65] MQTT auth (optional). (~5)

---

## 6. 5-week sequencing (mirrors the dashboard; off-board + gaps slotted in)

| Wk | Board milestone (external) | + Off-board / gap work (internal) | Gate |
|---|---|---|---|
| **Pre** | — | Branch reconcile to `latest`; branch `feature/labos-airtable`. | — |
| **W1** | P0 foundations + contract lock | ✅ *done 2026-07-29:* mapping + sandbox ask sent **and answered**. Now: reply with contract v0.3 asks (v2 reconciliation); ✅ **P0/Ref 42 done (`bf4db01`, built + rehearsed, not deployed)**; gap J field-ID binding + schema snapshot; gap B reachable origin; **start firmware P3 pressure capture (off-board)**. | Airtable team ratifying; sandbox base in hand |
| **W2** | P1 schema & identity migrated | gap D JSON cols; **finish firmware P3 + `/trials` seam (H)**; pass/fail compute stub (C). | canonical build, no field names needed |
| **W3** | P2 requirements-IN live | Build against **sandbox base**; requirements cache. | **needs mapping 🟢 Agreed** (else swap W3⇄W4) |
| **W4** | ★ Bidirectional sync, dark-launched | in-process worker (5); confirm roll-up mechanism (E) live. | needs mapping Agreed |
| **W5** | Manual screens + hardening + cutover | gap A photo pipeline; gap F backfill; e2e sandbox→prod; contract → **v1.0**; flag on. | contract ratified |

**Solo honesty:** W4 (sync queue, ~13, highest risk) + gap-A photo work in W5 are the crunch. If the
Airtable team slips ratification, **swap W3⇄W4** (build sync-queue plumbing against canonical envelope
first, bind reads when names land). The natural W6 spill candidate is **P5 manual screens** — off the
P0→P1→P4 spine and mostly my own decisions.

---

## 7. Definition of Done — full integration complete

- [ ] Requirements read from the (agreed) Airtable base into the selection UI; operator re-types nothing.
- [ ] Every test/attempt commits locally first; results upsert to Airtable idempotently on
      (`labos_test_id`, `labos_attempt_id`); no duplicate records.
- [ ] Attempts append-only; sync states (Pending/Synced/Sync Failed/Retry Required) visible + manual retry.
- [ ] Static/Cycles write `actual_pressure` + `max_pressure_achieved` (firmware P3 landed) and
      management-computed `pass_fail`.
- [ ] Impact / Forced-Entry / ANSI Z97.1 manual screens live, with working photo links + report link.
- [ ] Token scoped + rotatable; secrets server-side only; sandbox proven before prod cutover.
- [ ] Mapping rows 🟢 Agreed → **contract bumped to v1.0**.

---

## 8. Open items I still need from the Airtable team / Luis

**Re-baselined 2026-07-29 against their doc.** Answered: (1) field names now supplied ✅ · (2) identifiers =
`rec…` IDs ✅ · (4) roll-ups = Airtable automations ✅ · (5) photos = links ✅ (field *type* still to confirm) ·
(6) option sets — we proposed them, awaiting acceptance · (7) sandbox base ✅ provisioned.

**Re-baselined again 2026-08-23** against the live probe. Newly answered: (3) `Photos` field type ✅ `url` ·
the four `Airtable … ID` fields ✅ plain text · `Impact Result` ✅ free text · **the PAT** ✅ delivered ·
option sets ✅ read from the base rather than proposed.

Still open — full list with owners in `docs/labos-airtable/evidence/write-contract-v0.3-superseded-2026-09-06.md` §10. The ones that matter:
0. **The proposal-extraction shift** (§10.19) — *highest severity.* Their requirement values do not match the
   proposal PDF they came from. *Gates any live test driven from Airtable, which is the point of W3.*
0b. **`Test Type` has one option** (§10.17) — 4 of 5 test types cannot be written back at all. *Gates W4.*
1. **Read-side parameter structure** (gap I) — ✅ structure answered; the *typing* ask (`Required Value` /
   `Required Unit`) remains. *W3 unblocked to build, blocked to trust.*
2. **The requested result fields — 4 of 11 granted in v2** (`Schema Version`, `Max Pressure Achieved`,
   `Deflection Unit`, `Complete LabOS JSON Response`). Still outstanding: `Corrects Attempt ID` +
   `Correction Reason` (**blocking** — contract §10.14), `Test Name`, `Abort Reason`, `Cycles
   Required/Completed`, `Required Value/Unit`, traceability extras (all carryable in JSON — §10.15).
   *Gates W4.*
3. ~~**Rotated PAT**~~ — ✅ **CLOSED 2026-08-23.** Both PATs delivered with `schema.bases:read`, stored in the
   gitignored `.env`, in no commit or document. **Rotate after acceptance testing:** they arrived as plaintext
   email, the second credential-delivery leak on this project.
4. **Writable table in its own base, or one base + LabOS write allowlist** — their "read-only on existing
   tables" guarantee isn't enforceable by a PAT (scopes are per-base, not per-table). Their choice; we
   implement the allowlist either way.

Plus, ours not theirs: verify the omit-vs-null behaviour on the sandbox (contract §5, §10.11) and stand up the
reachable report/photo origin (gap B) before the first production write.
