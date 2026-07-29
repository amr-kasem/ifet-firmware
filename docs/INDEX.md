# IFET Project — Documentation Index

**Maintained by:** Abdelrahman · **Reconciled:** 2026-07-29
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
| **Open integration items / what blocks what** | `labos-airtable-write-contract-v0.2.md` **§10** | review doc §6 · verification report §5 · Notion mapping §5 · Notion response §9 |
| **The write envelope** — fields, types, required-per-test-type, blank rules, upsert, immutability | `labos-airtable-write-contract-v0.2.md` | Notion *Field Mapping* §2 · Notion *Response* §4 |
| **Field-name mapping** LabOS ↔ Airtable, and ratification status per row | Notion *[Field Mapping (Working)](https://app.notion.com/p/3a357bad43d581c68ea1c85411429cac)* | the contract's field tables |
| **What we asked the Airtable team for, and why** | `labos-airtable-team-doc-review-2026-07-29.md` | Notion *[Response page](https://app.notion.com/p/3ac57bad43d581c49ff9cf1e125c40c3)* |
| **The exact message that goes out** | review doc **§7** | — |
| **What we've verified, and the requests awaiting their approval** | `labos-airtable-verification-report-2026-07-29.md` | Notion *[Verification Report](https://app.notion.com/p/3ac57bad43d5811b84a2da22288d0edb)* |
| **Internal plan, gaps A–J, pre-closed decisions, week sequencing** | `labos-airtable-integration-internal-plan-2026-07-23.md` | Notion internal copy (private) |
| **Cross-team schedule and per-week deliverables** | Notion *[5-Week Integration Plan](https://app.notion.com/p/3a657bad43d581e59490f53a8eeedbf6)* | — |
| **Live task status** | Notion *Delivery & Progress Tracker* (Epic IFET-32) | — |
| **Repo/branch/production ground truth** | `labos-branch-reconcile-plan-2026-07-24.md` | Notion *[Execution Record](https://app.notion.com/p/3a957bad43d581b4a091d1c1459de641)* |
| **Secret handling and the gated deploy runbook** | `ifet-management/deployment/SECRETS.md` | this index |
| **Hardware config — Modbus, VFD, valve pins** | `README.md` (this directory) | — |

**Rule:** when an item closes, close it in the authoritative document **first**, then update the views the same
day. If two documents disagree, the authoritative one wins and the other is a bug.

---

## 2. Document inventory

### `ifet-firmware/docs/`

| Document | Purpose | Status |
|---|---|---|
| `INDEX.md` | this file | current |
| `labos-airtable-write-contract-v0.2.md` | **The spec both teams build against.** Identity, idempotency, the attempt lifecycle, retest vs. correction, the field envelope, blank rules, JSON shapes, retry classes, and the canonical open-items list. | **`v0.2 DRAFT`** — ratifies to `v1.0` when §10 closes |
| `labos-airtable-team-doc-review-2026-07-29.md` | Our review of their schema doc: the verdict, ten required changes, eleven requested fields, and **§7 — the message that goes out.** | current |
| `labos-airtable-verification-report-2026-07-29.md` | Sendable report: the ownership boundary, what LabOS has verified, and the exact HTTP requests awaiting their approval. | current — **stage 1 done, stages 2–3 pending their token and approval** |
| `labos-airtable-integration-internal-plan-2026-07-23.md` | Internal superset: gaps A–J, nine pre-closed decisions, the five-week sequencing with off-dashboard firmware work. | current (updated 2026-07-29) |
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

## 3. Status snapshot — 2026-07-29

| | |
|---|---|
| **Week** | 1 of 5 |
| **Contract** | `v0.2 DRAFT`. Ratifies to `v1.0` when contract §10 closes. |
| **Mapping ratification** | 0 rows 🟢 Agreed. ~45 🔵 In review (their field names supplied), 11 🟠 Requested, 4 ⛔ withdrawn by us. |
| **Sandbox base** | provisioned — `appYBTqIL43pmS0xN`. No request made against it yet. |
| **Token** | the one in their PDF is compromised; revocation requested; **never used or stored by LabOS**. |
| **Done** | branch reconcile (closed) · schema review + reply · write contract v0.2 · P0/Ref 42 secret store (`bf4db01`, built + rehearsed off-node, **not deployed**) |
| **Blocked on the Airtable team** | rotated token with schema-read scope · read-side parameter structure (gates W3) · the 11 field additions (gates W4) · approval to run stages 2–3 · the `Testing End Date` contradiction |
| **Blocked on the manager** | test node up and reachable — the `test` node has been offline since ~2026-07-24 |
| **Not blocked** | Airtable API client + probe harness · offline payload contract tests · P1 append-only attempt model · firmware P3 pressure and per-gauge deflection capture |

---

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
