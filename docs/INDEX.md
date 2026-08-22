# IFET Project — Documentation Index

**Maintained by:** Abdelrahman · **Reconciled:** 2026-08-22 (previously 2026-07-29)
**Scope:** every LabOS ↔ Airtable integration and status document, across both repos and Notion.

> **Why this file exists.** The same fact was living in five places and starting to drift — three different
> open-item lists, a contract version that had moved on, a P0 task marked "next" after it was done, and a VFD
> Modbus address in the config docs that production stopped using in July. This index fixes the pattern rather
> than the instances: **each subject has exactly one owning document**, and everything else is explicitly a
> *view* of it.

---

## 1. Single source of truth — which document owns which subject

| Subject | **Authoritative document** | Views that must follow it |
|---|---|---|
| **Open integration items / what blocks what** | `labos-airtable-write-contract-v0.3.md` **§10** | review doc §6 · verification report §5 · Notion mapping §5 · Notion response §9 |
| **The write envelope** — fields, types, required-per-test-type, blank rules, upsert, immutability | `labos-airtable-write-contract-v0.3.md` | Notion *Field Mapping* §2 · Notion *Response* §4 |
| **Field-name mapping** LabOS ↔ Airtable, and ratification status per row | Notion *[Field Mapping (Working)](https://app.notion.com/p/3a357bad43d581c68ea1c85411429cac)* | the contract's field tables |
| **What we asked the Airtable team for, and why** | `labos-airtable-v2-guide-reconciliation-2026-08-22.md` | Notion *[Response page](https://app.notion.com/p/3ac57bad43d581c49ff9cf1e125c40c3)* · review doc `…-2026-07-29.md` (superseded, kept as the sent record) |
| **The exact message that goes out** | reconciliation doc **§5** | review doc §7 (the 2026-07-29 message, already sent) |
| **What we've verified, and the requests awaiting their approval** | `labos-airtable-verification-report-2026-07-29.md` | Notion *[Verification Report](https://app.notion.com/p/3ac57bad43d5811b84a2da22288d0edb)* |
| **Internal plan, gaps A–J, pre-closed decisions, week sequencing** | `labos-airtable-integration-internal-plan-2026-07-23.md` | Notion internal copy (private) |
| **Cross-team schedule and per-week deliverables** | Notion *[5-Week Integration Plan](https://app.notion.com/p/3a657bad43d581e59490f53a8eeedbf6)* | — |
| **Live task status** | Notion *Delivery & Progress Tracker* (Epic IFET-32) | — |
| **Repo/branch/production ground truth** | `labos-branch-reconcile-plan-2026-07-24.md` | Notion *[Execution Record](https://app.notion.com/p/3a957bad43d581b4a091d1c1459de641)* |
| **Secret handling and the gated deploy runbook** | `ifet-management/deployment/SECRETS.md` | this index |
| **Airtable environments, base IDs, table IDs, PAT scopes** | `labos-airtable-write-contract-v0.3.md` **§0.1** | reconciliation doc §1 · `ifet-management` `app/config.py` · everything else |
| **The write envelope as executable rules** | `labos-airtable-write-contract-v0.3.md` §4/§5/§5.1 | `ifet-management` `app/airtable/contract.py` — **a view; the prose wins on disagreement** |
| **Hardware config — Modbus, VFD, valve pins** | `README.md` (this directory) | — |

**Rule:** when an item closes, close it in the authoritative document **first**, then update the views the same
day. If two documents disagree, the authoritative one wins and the other is a bug.

---

## 2. Document inventory

### `ifet-firmware/docs/`

| Document | Purpose | Status |
|---|---|---|
| `INDEX.md` | this file | current |
| `labos-airtable-write-contract-v0.3.md` | **The spec both teams build against.** Identity, idempotency, the attempt lifecycle, retest vs. correction, the field envelope, blank rules, JSON shapes, retry classes, the live base/table IDs (§0.1), and the canonical open-items list. | **`v0.3 DRAFT`** — ratifies to `v1.0` when §10 closes |
| `labos-airtable-v2-guide-reconciliation-2026-08-22.md` | **Current outbound artifact.** Delta against their *API Integration Guide v2*, the four things we need settled, and **§5 — the message that goes out.** | current |
| `labos-airtable-team-doc-review-2026-07-29.md` | Review of their **v1** schema doc: the verdict, ten required changes, eleven requested fields, §7 the message sent on 2026-07-29. | ⚠️ **superseded in part** by their v2 — bannered, kept verbatim as the sent record |
| `labos-airtable-verification-report-2026-07-29.md` | Sendable report: the ownership boundary, what LabOS has verified, and the exact HTTP requests awaiting their approval. | ⚠️ **superseded in part** — bannered. Its base ID and table name are stale; the stage 1–3 request *shapes* still stand. Reissue against `app4oXS3Kd5IKWgJ7` when the PAT lands |
| `labos-airtable-integration-internal-plan-2026-07-23.md` | Internal superset: gaps A–J, nine pre-closed decisions, the five-week sequencing with off-dashboard firmware work. | current (updated 2026-08-22) |
| `labos-branch-reconcile-plan-2026-07-24.md` | Repo ↔ production reconcile. Node baselines, container audit, the safety guardrails for git on a live node, and the Step E deploy runbook. | 🔒 **CLOSED** — only Step E/F remain, folded into the next deliberate deploy |
| `system1-sensor-vfd-debug-report-2026-07-07.md` | system-1 bring-up: sensors, the VFD-at-address-12 finding, PSF scaling. | historical record |
| `system1-sensor4-5-addition-2026-07-08.md` | system-1 sensor 4/5 addition. | historical record |
| `README.md` | Hardware configuration — Modbus RTU, Delta C2000 Plus VFD over serial and TCP, valve pin maps. | current (VFD address corrected to `12`, 2026-07-29) |

### `ifet-management/`

| Document | Purpose | Status |
|---|---|---|
| `deployment/SECRETS.md` | Where every credential lives, the secret-hygiene guard, and the **gated** migration runbook for the production management node. | current — P0 built and rehearsed, **deployment gated** |
| `src/management_service/DATABASE_MIGRATIONS.md` | Alembic usage. | pre-existing |

### Notion — [LabOS hub](https://app.notion.com/p/3a357bad43d5818cb726d24c5e803c69)

| Page | Audience | Status |
|---|---|---|
| *5-Week Integration Plan (LabOS × Airtable)* | cross-team | current — W1 progress note added 2026-07-29 |
| *LabOS ↔ Airtable — Field Mapping (Working)* | cross-team | current — real Airtable field names folded in 2026-07-29; 🟡→🔵, plus 🟠 `Requested` rows |
| *LabOS Response — Airtable Schema Review & Write Contract v0.2* | cross-team | current |
| *LabOS Verification Report & API Pre-Flight* | cross-team | current |
| *Branch Reconcile — Execution Record* | internal | 🔒 closed 2026-07-29 |
| *LabOS ↔ Airtable — Internal Engineering Plan* | private | mirrors the repo internal plan |
| *Codebase Readiness Evaluation (2026-07-20)* | internal | ⚠️ **partly superseded** — it read management branch `main`; production runs `latest`, which is further along. Its line-number citations are off. Read the internal plan §1 instead. |
| *Delivery & Progress Tracker* (Epic IFET-32) | cross-team | live board |

---

## 3. Status snapshot — 2026-08-22

| | |
|---|---|
| **Week** | 1 of 5 — still. W2+ has not started because the external gate never opened. |
| **Contract** | `v0.3 DRAFT` (was `v0.2`). Ratifies to `v1.0` when contract §10 closes. |
| **Their latest** | *API Integration Guide* **v2**, 2026-08-17. Delta: `labos-airtable-v2-guide-reconciliation-2026-08-22.md` |
| **Testing base** | `app4oXS3Kd5IKWgJ7` — *LabOS Testing Base*. Production `app0OCunbmuXl7Hc9`. All nine table IDs published (contract §0.1). **No request made against either base yet.** |
| **Write target** | `LabOS Raw Data Table` — `tblnc9SsbXU0C0FWh`. **The only writable surface**; LabOS enforces the allowlist client-side, since PAT scopes are per-base not per-table. |
| **Token** | v2 correctly contains no token; the v1 leak is remediated and was never used or stored by LabOS. **The testing PAT is still not delivered** — this gates every LabOS-side verification. |
| **Requested fields** | **4 of 11 granted** in v2: `Schema Version`, `Max Pressure Achieved`, `Deflection Unit`, `Complete LabOS JSON Response`. |
| **Done** | branch reconcile (closed) · schema review + reply · write contract v0.3 · v2 reconciliation + reply drafted · Airtable client, schema probe and envelope builder (`feature/labos-airtable`) · P0/Ref 42 secret store (`bf4db01`, built + rehearsed off-node, **not deployed**) |
| **Blocked on the Airtable team** | **read-side parameter structure (gates W3 — the critical path, open since 2026-07-23 and untouched by v2)** · testing PAT delivery · the `Test Date` collapse (§10.13) · `Corrects Attempt ID` + `Correction Reason` (§10.14) · approval to run verification stages 2–3 |
| **Blocked on the manager** | test node up and reachable — offline since ~2026-07-24, so there is **no non-production rig** for firmware P3 |
| **Built, awaiting the token** | Airtable API client + write allowlist · schema probe · payload envelope builder · **95 offline tests** — all in `ifet-management` @ `feature/labos-airtable`, stdlib-only so none of it needs a production image rebuild |
| **Not blocked** | P1 append-only attempt model · sync worker + durable queue · firmware P3 pressure and per-gauge deflection capture (write + unit-test only, no rig) |

> **The honest read.** Everything LabOS can do without the Airtable team is either done or unblocked and
> queued. What is missing is one field specification (§10.3) and one token. Neither is ours to produce.

## 4. Keeping these consistent

1. **Commit every day**, including work done over SSH on a node, and update the matching Notion page the same
   day. Uncommitted device edits are what caused the reconcile in the first place.
2. **Close items in the authoritative document first** (§1), then the views.
3. **Every commit is authored `gad`**, with no assistant attribution. Node git identities are `Hammad` /
   `device2` / unset, so pass the author explicitly when committing on a node.
4. **Never rebuild or restart a production container without notice.** `management`, `system-1`, and
   `system-2` are production. Rehearse off-production, inform the deployment owner, agree a window. Details in
   `ifet-management/deployment/SECRETS.md` §2.
5. **When a SHA, base ID, field name, contract version, or gate status changes, grep for it** across
   `docs/` and fix every occurrence — that is what this reconcile had to do by hand.

### Fixed in the 2026-07-29 reconcile

- Three competing open-item lists → contract §10 is canonical, the other two are labelled views.
- Internal plan still said contract `v0.1 DRAFT` → now `v0.2`.
- P0/Ref 42 marked as the "next task" in three places after it was completed → all corrected.
- `README.md` VFD examples used Modbus address `5`; **production answers on `12`** — the exact stale value that
  made the VFD go silent in July. Corrected in both examples, with a note to verify per device.
- `Testing End Date` contradiction was in the outbound message but missing from the contract's open items →
  added as §10 item 0.
- Retest vs. correction was undefined in the contract, though the whole immutability model depends on it →
  now contract §3.1.
- Readiness evaluation flagged as partly superseded rather than left to mislead.

### Fixed in the 2026-08-22 reconcile

- Base `appYBTqIL43pmS0xN` was cited as live in **5 files, 12 places**; their v2 guide re-based the sandbox to
  `app4oXS3Kd5IKWgJ7`. Every live reference now points at the new base; the two already-sent 2026-07-29 docs
  keep theirs, under a banner that says the ID is retired.
- Contract renamed `v0.2` → `v0.3` **with the filename**, so the version cannot drift from the document again;
  all nine inbound references updated.
- Their real wire names folded into contract §4 — `Airtable Mockup ID` (no hyphen), `LabOS Report Link`,
  `Complete LabOS JSON Response`. These are the strings the client sends; the LabOS names are internal only.
- `Test Result` option spelling flagged: v2's example sends `"Passed"`, the contract says `Pass`
  (§10.16).
- Open items 0, 7 and 9 went **moot** — v2 deleted the fields they were about. Recorded as moot rather than
  closed, and the substance reopened as §10.13 / §10.15 where it still matters.
- The two 2026-07-29 documents were **bannered, not rewritten.** They are the record of what was sent; editing
  them to match today's facts would falsify the correspondence.
