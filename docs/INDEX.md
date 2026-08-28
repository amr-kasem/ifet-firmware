# IFET Project — Documentation Index

**Maintained by:** Abdelrahman · **Reconciled:** 2026-08-28 (previously 2026-08-23)
**Scope:** every LabOS ↔ Airtable integration and status document, across both repos and Notion.

---

## 0. Resume here — state as of 2026-08-28

> ### ⚠️ Read this before the rest of §0
>
> **The Monday 2026-08-25 message was never sent.** The §0 below was written on 2026-08-23 and its
> "shortest path" step 1 has not been executed. Everything it says about the *build* is still accurate and
> was re-verified on 2026-08-28 (132 tests green; both bases probed read-only, schema unchanged).
>
> **Current assessment: `labos-delivery-status-2026-08-28.md`** — build state, the schedule stated
> honestly (day 36 of a 35-day plan, 2 of 5 milestones done), and the extraction defect measured against
> the sample job `IFET-26-0066`.
>
> **The PM escalated on 2026-08-28** ("no activity, no Notion updates, 5 weeks nearly gone"). Answer:
> `labos-airtable-revised-roadmap-2026-08-28.md` — **revised target pilot go-live Fri 2026-10-09**, six
> working weeks from Mon 2026-08-31, **W4 pulled ahead of W3**. Notion twin:
> *🗓️ Revised Roadmap & True Timeline*, `3ca57bad43d581e5b7d4fc3dda389294`.
> Standing commitment made to the PM: **status page updated every Friday**, board reflects reality on the
> day, anything blocked >48h goes to the chat.
>
> **Two things are now prepared and waiting, so neither gets rushed later:**
> - **Stage 3 is a script**, not an improvisation: `ifet-management` `tests/stage3_live_write.py`.
>   Dry-run by default (`python3 -m tests.stage3_live_write`); a live run needs
>   `--live --approved-by "<who, when>"`, and the production base is refused unconditionally.
> - **The deploy is a runbook**: `labos-p0-p1-deploy-runbook-2026-08-28.md`. Read its §2 first — whether
>   `alembic_version` still returns `3a65a83e0463` decides whether the deploy can happen at all that day.
>
> **Notion is now synced (2026-08-28)** — see §4 below. The new status page is the human-readable view:
> *📊 Delivery Status — LabOS × Airtable (2026-08-28)*, `3ca57bad43d581f8b996e63764f5cbfc`.
>
> **Still step 1: send `labos-airtable-live-probe-findings-2026-08-23.md` §8.** It has been re-framed for
> a direct send and carries one new fact — the defect has already reached a *completed* record
> (`SMI (impacts) = 10`, `Passed`, where the proposal has no SMI value). All four asks re-confirmed open
> against both live bases on 2026-08-28.

### State as of 2026-08-23 (build facts still current)

*Written so a session starting cold can pick up without reconstructing anything. If this section and §3
disagree, §3 is newer and this one is the bug.*

### Where the work is

| | |
|---|---|
| `ifet-firmware` | `feature/labos-firmware-p3` — docs only, pushed, clean |
| `ifet-management` | `feature/labos-airtable` — all integration code, pushed, clean |
| **Deployed** | **Nothing.** Both branches are unmerged; production runs `latest` untouched |
| Tokens | Both Airtable PATs live in `ifet-management/.env` (gitignored, mode 600). **Never** in git, docs, or a browser-served config |

### What is done

- **Airtable client, schema probe, envelope builder** — built, and verified against the live bases.
- **The probe ran against both bases** on 2026-08-23, read-only. Six contract items closed, six opened.
- **W2 / P1 complete** — append-only attempt schema, Airtable linkage, JSON columns, ORM→envelope mapping,
  identity + lifecycle, both `/trials` endpoints wired. **132 offline tests**, stdlib-only.
- **Migration delivery fixed** — migrations were gitignored and the chain lived only on the node; the real
  30-revision chain is now in git, and `startup.sh` no longer autogenerates schema at boot.

### The three things that matter most

1. **⚠️ Airtable's requirement data is wrong.** Their PDF extractor drops blank cells, so values shift one
   column: their sample job reads `DP (+) (PSF) = 9` where the proposal says `+60/60`. Those values drive the
   rig. **Standing rule: nothing reads requirements from Airtable for a live test until they fix it.**
   Contract §10.19 · findings §5.2.
2. **A Monday message is written and unsent** — `labos-airtable-live-probe-findings-2026-08-23.md` §8. Luis
   was away for the weekend; a joint testing session is booked. Stamp the *Sent* line when it goes.
3. **⚠️ Deploy hazard.** Until the `startup.sh` change ships, every container restart appends a no-op
   revision on the node and moves the head. Deploy `startup.sh` **and** the P1 migration together, and
   re-confirm `SELECT * FROM alembic_version;` still returns `3a65a83e0463` immediately beforehand — a head
   we do not descend from means two heads and `upgrade head` silently refuses.

### The shortest path — do these two, in this order

**1. Send the Monday message.** Authoritative wording is
`labos-airtable-live-probe-findings-2026-08-23.md` **§8** — send it as written, don't re-draft it. The call is
**Monday 2026-08-25** with Luis; §7 is the agenda, ordered by what blocks the most. When it goes out, stamp the
*Sent* line at the end of §8 the same day.

**2. Then verification stage 3** — one live upsert round-trip into the **testing** base. The last step before
W3/W4. Three things to know before running it:

- **It is gated on Luis's explicit OK**, which is exactly what the §8 message asks for ("For Monday", item 3).
  Send first, get the go-ahead on the call, then run. Production base `app0OCunbmuXl7Hc9` is never touched.
- **⚠️ The stage 3 spec in `labos-airtable-verification-report-2026-07-29.md` is stale — do not run its payload
  as written.** It targets the retired sandbox `appYBTqIL43pmS0xN` / `LabOS Raw Test Results`, and sends
  `Testing Start Date` / `Testing End Date`, which do not exist on the live table (it is `Test Date`, and it is
  date-only — §10.20). The *fourteen checks* it describes still stand; re-point them at the real target from
  contract **§0.1 + §2**: `PATCH .../app4oXS3Kd5IKWgJ7/tblnc9SsbXU0C0FWh`, upsert on `LabOS Attempt ID`.
- **The test record must be `Static Load`.** Four of the five test types are refused by the live `Test Type`
  option set (§10.17), so static load is the only type that can be written back at all until item 2 lands.

### After that — none of these are blocked either

- ~~**Notion is four pages behind**~~ — ✅ **synced 2026-08-28**, see §4.
- **Firmware `/trials` seam** (gap H, Refs 53 ↔ 54) — must land on both sides together.
- Answer the open question in `labos-p1-schema-and-migration-mechanism-2026-08-23.md` §7: may an operator
  edit a *terminal* attempt's notes/photos? Likely split — artifacts appendable, results require a correction.

### Two practical notes

- **Rehearsing the migration needs SQLAlchemy**, which is not on the system Python. Rebuild the throwaway env
  with `uv venv <dir> && VIRTUAL_ENV=<dir> uv pip install sqlalchemy alembic`, then
  `<dir>/bin/python tests/rehearse_p1_migration.py /tmp/x.db`.
- **Reaching a node:** use the `ifet-ssh` skill. Mutating commands are blocked by the auto-mode classifier and
  have to be handed to the user; read-only ones run fine. Session record:
  `ifet-ssh-session-record-2026-08-23.md`.


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
| **The exact message that goes out** | `labos-airtable-live-probe-findings-2026-08-23.md` **§8** — the Monday message | reconciliation doc §5 and review doc §7 (the 2026-08-22 and 2026-07-29 messages, both already sent) |
| **Readiness summary — one readable overview for a human** | `labos-airtable-readiness-2026-08-23.md` | explicitly a **view of everything above**; it names its sources per section |
| **What we've verified against the live base** | `labos-airtable-live-probe-findings-2026-08-23.md` | `labos-airtable-verification-report-2026-07-29.md` (**historical** — the 2026-07-29 sent record) · Notion *[Verification Report](https://app.notion.com/p/3ac57bad43d5811b84a2da22288d0edb)* |
| **Internal plan, gaps A–J, pre-closed decisions, week sequencing** | `ifet-ssh-session-record-2026-08-23.md` | **Record of the 2026-08-23 SSH session on `management`.** Every command run, what it returned, what it established, and an explicit statement of what was *not* touched. All read-only. | current |
| `labos-p1-schema-and-migration-mechanism-2026-08-23.md` | **W2 / P1 evidence record.** The attempt schema, and the discovery that migrations are gitignored, bind-mounted from the node, and autogenerated at every container boot — production had 29 revisions, the repo had none. | current |
| `labos-airtable-integration-internal-plan-2026-07-23.md` | Notion internal copy (private) |
| **Cross-team schedule and per-week deliverables** | Notion *[5-Week Integration Plan](https://app.notion.com/p/3a657bad43d581e59490f53a8eeedbf6)* | — |
| **Live task status** | Notion *Delivery & Progress Tracker* (Epic IFET-32) | — |
| **Repo/branch/production ground truth** | `labos-branch-reconcile-plan-2026-07-24.md` | Notion *[Execution Record](https://app.notion.com/p/3a957bad43d581b4a091d1c1459de641)* |
| **Secret handling and the gated deploy runbook** | `ifet-management/deployment/SECRETS.md` | this index |
| **Airtable environments, base IDs, table IDs, PAT scopes** | `labos-airtable-write-contract-v0.3.md` **§0.1** | reconciliation doc §1 · `ifet-management` `app/config.py` · everything else |
| **The write envelope as executable rules** | `labos-airtable-write-contract-v0.3.md` §4/§5/§5.1 | `ifet-management` `app/airtable/contract.py` — **a view; the prose wins on disagreement** |
| **What was run on a node, when, and with what blast radius** | `ifet-ssh-session-record-2026-08-23.md` (2026-08-23) | — each SSH session gets its own record |
| **How a schema change reaches production** (alembic, bind mounts, autogenerate-at-boot) | `ifet-ssh-session-record-2026-08-23.md` | **Record of the 2026-08-23 SSH session on `management`.** Every command run, what it returned, what it established, and an explicit statement of what was *not* touched. All read-only. | current |
| `labos-p1-schema-and-migration-mechanism-2026-08-23.md` | `ifet-management` `startup.sh` + `compose.yaml` are the mechanism it documents |
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
| `labos-airtable-v2-guide-reconciliation-2026-08-22.md` | Delta against their *API Integration Guide v2*, and **§5 — the correspondence record.** Its §5.0 ask was **answered on 2026-08-23** (both PATs delivered). | current — but the **outbound artifact is now `labos-airtable-live-probe-findings-2026-08-23.md` §7**, the Monday agenda |
| `labos-airtable-readiness-2026-08-23.md` | **Start here for a human overview.** Where the integration stands, what is built, what today's probe proved, the one serious risk, what blocks and on whom, and the real position of the 5-week plan. A view — it names its authoritative source per section. | current |
| `labos-airtable-live-probe-findings-2026-08-23.md` | **Evidence record for the first live probe of both bases**, and **§8 the message going to the Airtable team.** What the schema actually holds, the six items it closes, the six it opens, §10.3 answered, and the proposal-extraction defect (§5.2). | current — **the outbound artifact** |
| `labos-airtable-team-doc-review-2026-07-29.md` | Review of their **v1** schema doc: the verdict, ten required changes, eleven requested fields, §7 the message sent on 2026-07-29. | ⚠️ **superseded in part** by their v2 — bannered, kept verbatim as the sent record |
| `labos-airtable-verification-report-2026-07-29.md` | The ownership boundary, and the exact HTTP requests LabOS proposed to run. | 📕 **Historical — the 2026-07-29 sent record.** Its stage 1 and 2 were **executed on 2026-08-23** against `app4oXS3Kd5IKWgJ7` and `app0OCunbmuXl7Hc9`; results live in `labos-airtable-live-probe-findings-2026-08-23.md`, which now owns this subject. Base ID and table name in the header are stale by design |
| `ifet-ssh-session-record-2026-08-23.md` | **Record of the 2026-08-23 SSH session on `management`.** Every command run, what it returned, what it established, and an explicit statement of what was *not* touched. All read-only. | current |
| `labos-p1-schema-and-migration-mechanism-2026-08-23.md` | **W2 / P1 evidence record.** The attempt schema, and the discovery that migrations are gitignored, bind-mounted from the node, and autogenerated at every container boot — production had 29 revisions, the repo had none. | current |
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

### Airtable (theirs — read-only to us)

| Resource | Link / ID | Notes |
|---|---|---|
| Production dashboard | [interface page](https://airtable.com/app0OCunbmuXl7Hc9/pagGRZZBAH691m3x5) | Human-facing only; interface pages are not exposed by the Meta API. Confirms production base `app0OCunbmuXl7Hc9`. |
| Testing base | `app4oXS3Kd5IKWgJ7` | Where LabOS builds. Contract §0.1. |
| Write target | `tblnc9SsbXU0C0FWh` | The only writable surface. |

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

## 3. Status snapshot — 2026-08-23

| | |
|---|---|
| **Week** | **2 of 5 — started 2026-08-23.** W1 closed on the LabOS side; P1 schema, identity and the ORM→envelope mapping are built and rehearsed. W3 stays gated on §10.19. |
| **Contract** | `v0.3 DRAFT`. §10 now runs to **22 items: 6 closed on 2026-08-23**, 6 opened by the live probe. Ratifies to `v1.0` when §10 closes. |
| **Their latest** | *API Integration Guide* **v2**, 2026-08-17. Delta: `labos-airtable-v2-guide-reconciliation-2026-08-22.md` |
| **Testing base** | `app4oXS3Kd5IKWgJ7` — *LabOS Testing Base*. Production `app0OCunbmuXl7Hc9`. All nine table IDs published (contract §0.1). **First requests made 2026-08-23 — read-only, both bases; nothing was written to either.** Every table ID confirmed live; the testing base is a schema-only clone holding no records. |
| **Write target** | `LabOS Raw Data Table` — `tblnc9SsbXU0C0FWh`. **The only writable surface**; LabOS enforces the allowlist client-side, since PAT scopes are per-base not per-table. |
| **Token** | ✅ **Both PATs delivered 2026-08-23** (testing + production), stored in the gitignored `.env`, in no commit or document. **Rotate after acceptance testing** — they arrived as plaintext email. |
| **Requested fields** | **4 of 11 granted** in v2: `Schema Version`, `Max Pressure Achieved`, `Deflection Unit`, `Complete LabOS JSON Response`. All 28 promised fields confirmed live. |
| **Done** | branch reconcile (closed) · schema review + reply · write contract v0.3 · v2 reconciliation + reply · Airtable client, schema probe and envelope builder (`feature/labos-airtable`) · P0/Ref 42 secret store (`bf4db01`, built + rehearsed off-node, **not deployed**) · **live probe of both bases · wire-level option translation · W2/P1 attempt schema — 132 tests (2026-08-23)** |
| **Awaiting their reply** | Luis replied 2026-08-23 with both PATs and pointed us at the populated proposal data; he is away until Monday, when a joint testing session is booked. The §5.1 write-back asks are no longer held — they go **with** the probe findings, since the probe turned two of them into blockers with evidence. Agenda: `labos-airtable-live-probe-findings-2026-08-23.md` §7. |
| **Blocked on the Airtable team** | **the proposal-extraction shift (§10.19) — highest severity: their sample job carries `DP = 9 PSF` where the PDF says `+60/60`, and LabOS cannot detect it** · `Test Type` has only one option, so 4 of 5 test types cannot be written (§10.17) · `Corrects Attempt ID` + `Correction Reason` (§10.14) · typed `Required Value`/`Required Unit` (§10.3) · the `Test Date` collapse (§10.13/§10.20) · confirm the write model (§10.21) |
| **Blocked on the manager** | test node up and reachable — offline since ~2026-07-24, so there is **no non-production rig** for firmware P3 |
| **Verified against the live base** | Airtable API client + write allowlist · schema probe (run against both bases, snapshots in `docs/airtable-schema/`) · payload envelope builder with wire-level option translation · attempt schema + ORM→envelope mapping · **132 offline tests** — all in `ifet-management` @ `feature/labos-airtable`, stdlib-only so none of it needs a production image rebuild |
| **Not blocked** | **verification stage 3 — a live upsert round-trip into the testing base** (nothing engineering-side is blocking; it needs **Luis's OK on Monday's call**, which the §8 message asks for, and its July payload spec is stale — see §0) · sync worker + durable queue (W4) · firmware P3 pressure and per-gauge deflection capture (write + unit-test only, no rig) |
| **W2 / P1** | ✅ **complete + rehearsed 2026-08-23** — attempt schema, Airtable linkage, JSON columns, ORM→envelope mapping, identity + lifecycle, both `/trials` endpoints wired, **132 offline tests**. Migration is tracked and rehearsed both directions. **Not deployed.** Evidence: `labos-p1-schema-and-migration-mechanism-2026-08-23.md` |
| **Newly known about production** | Migrations are **gitignored and bind-mounted from the node**, and `startup.sh` autogenerates one on **every container restart** (28 empty no-ops since January). A `models.py` change merged to `latest` therefore alters the production schema at the next restart with no review. Documented, not yet changed. |

> **The honest read, 2026-08-23.** The token arrived and the gate opened: six open items closed in one probe
> run, and §10.3 — the critical path since July — is answered. W3 is unblocked *on structure*.
>
> But the probe also found something worse than a missing spec. **The requirement values in their sample job do
> not match the proposal PDF they were extracted from** (§10.19): the extractor drops blank cells instead of
> holding the column position, so `DP (+) (PSF)` reads `9` where the proposal says `+60/60`. Those are the
> numbers that drive the rig. LabOS cannot defend against it — every shifted value is individually plausible —
> so **nothing may read requirements from Airtable for a live test until the extraction is corrected.** W3 can
> be built against this structure; it must not be trusted with a rig yet.

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

### Fixed in the 2026-08-23 reconcile

- **Subject ownership moved.** "What we've verified" now belongs to `labos-airtable-live-probe-findings-2026-08-23.md`; the 2026-07-29 verification report
  is re-labelled **historical** rather than "superseded in part", because its stage 1 and 2 were actually
  *executed* on 2026-08-23. Its banner now scores the plan against the outcome instead of just warning.
- **Six §10 items closed with evidence** rather than argument, and six opened. §10 went from 16 items to 22.
- **§10.16 closed against us** — the live base holds `Passed`/`Failed`. Their v2 example was right and the
  contract was wrong. Recorded that way in contract §4.3, in the reconciliation doc's §6.1 post-mortem, and
  here, because a reconcile that only ever finds the *other* side wrong is not being honest.
- **Gap J closed, gap I answered.** The internal plan's gap list had both open; J's `fld…`-ID snapshot now
  exists for both bases under `docs/airtable-schema/`, and I turned out to have a third answer neither side
  had proposed (row-per-parameter).
- **The held §5.1 message was released.** It was held so a second ask would not bury the first; Luis replied,
  so the reason expired. It now travels with the probe findings, which is strictly better — two of its asks
  became blockers backed by evidence.
- **Test count 95 → 98** in the four places that cited it.
- Stale future-tense headings ("the day the PAT arrives", "when the PAT lands") corrected — the PAT arrived.
- Retired base `appYBTqIL43pmS0xN` now survives **only** inside the two bannered sent-records and in
  statements that it is retired. Verified by sweep.
- **New standing safety rule recorded in three places** (INDEX §3, contract §10.19, internal plan gap I):
  nothing reads requirements from Airtable for a live test until their extractor is fixed.


---

## 4. Notion reconciliation — 2026-08-28

Notion had drifted a month behind the repo, and the **task board was the worst of it**: Phases 0 and 1
were finished while the board still read `To Do` / `Backlog`. Everything below is now reconciled.
**Repo docs stay authoritative** (§1); Notion pages are views.

### 4.1 Documents

| Notion page | What was done |
|---|---|
| **🗓️ Revised Roadmap & True Timeline (2026-08-28)** `3ca57bad43d581e5b7d4fc3dda389294` | **New.** The answer to the PM's escalation: revised dates, what would move them, dated targets per Airtable ask, and four asks back to IFET (maintenance window · `test` node · weight behind the extractor fix · the review decision). View of `labos-airtable-revised-roadmap-2026-08-28.md` |
| **📊 Delivery Status — LabOS × Airtable (2026-08-28)** `3ca57bad43d581f8b996e63764f5cbfc` | **New.** Human-readable status + a standalone *What we need from the Airtable team* section written to be lifted straight into a message. View of `labos-delivery-status-2026-08-28.md` |
| **🧪 LabOS — Naming, Architecture & Integration** (hub) `3a357bad43d5818cb726d24c5e803c69` | §1–§7 confirmed still accurate and said so. **§8 rewritten** — all six original open questions closed with what actually answered them, and a callout naming the four items that replaced them |
| **🗓️ 5-Week Integration Plan** `3a657bad43d581e59490f53a8eeedbf6` | Month-old progress callout demoted to *Historical*; **§"What we need from the Airtable team" fully rewritten** — its original five asks are all closed |
| **🗺️ Field Mapping (Working)** `3a357bad43d581c68ea1c85411429cac` | Added a **corrections table** (base ID, table name, `Airtable Mockup ID`, `Test Date` date-only, three option sets, `Required Value`/`Required Unit` absent) and **rewrote §5 open items**. §1–§3 tables not yet rewritten — tracked as a LabOS item inside its own §5 |
| **📕 Verification Report (2026-07-29)** `3ac57bad43d5811b84a2da22288d0edb` | Historical; stages 1–2 recorded as executed. **Red banner on Stage 3** — retired base, wrong table name, two non-existent fields, `Static Load` the only accepted type |
| **📕 Response — Schema Review & Contract v0.2** `3ac57bad43d581c49ff9cf1e125c40c3` | Historical. Names the one place **their spelling was right and ours wrong** (`Passed`/`Failed`) |
| **📕 Integration Contract v0.1** `3a357bad43d581669d73d203375acfd5` | Superseded — v0.3 is current, don't build against it |
| **📕 Codebase Readiness Evaluation (2026-07-20)** `3a357bad43d581f1bcfaed12cf59ac31` | Historical, **plus its factual error called out**: it assessed `main`, but production runs `latest`, which already had Alembic and `TestResult`. Several "gaps" it found were never real |
| **📕 Adaptation Plan** `3a357bad43d581e1a770ecf01d6185c4` | Historical; contract v0.3 wins on any disagreement. Inherits the same `main`/`latest` error |
| **📕 Change Summary for Review** `3a357bad43d5815e9f8bed140f9ba4f2` | Historical — describes as *proposed* what has since been built (P0, P1) and still isn't deployed |
| **📄 Internal Engineering Plan (5-week)** `3a657bad43d581fa9778e5c361abd190` | Current-position banner: structure holds, dates don't; **W3⇄W4 swap now in effect**; gap I answered but split |
| **🔒 Branch Reconcile Execution Record** `3a957bad43d581b4a091d1c1459de641` | Confirmed closed and still accurate; re-stated the node git guardrails, which remain load-bearing |
| **🏭 ifet** (project hub) `38b57bad43d58178b9b6dcef50401fc9` | Integration status line added; fleet table now records **`test` offline since ~2026-07-24** and why that matters (no non-prod rig to rehearse on) |

### 4.2 Delivery & Progress Tracker — Epic IFET-32

Every status below was verified against the code before it was changed, not inferred from the plan.

| Ref | Item | Was | Now |
|---|---|---|---|
| 32 | Epic IFET-32 | In Progress | *(unchanged)* — `Notes` + `Last update` refreshed |
| 34 | **Phase 0 · Foundations** | `To Do` | **Delivered** |
| 41 | Alembic migrations | `To Do` | **Delivered** — and bigger than planned; the chain lived only on the node |
| 42 | Server-side secrets | `To Do` | **Delivered** (`bf4db01`) |
| 43 | Airtable client + package | `To Do` | **Delivered** — title corrected to the real path `app/airtable/` |
| 35 | **Phase 1 · Schema & identity** | `Backlog` | **Delivered** |
| 44 | External-ID columns | `Backlog` | **Delivered** |
| 45 | Mock-up / Protocol / Section entities | `Backlog` | **Delivered — closed by design change.** Lightweight reference columns, *not* mirrored tables. The note says so explicitly so nobody builds it |
| 46 | Append-only Attempt model | `Backlog` | **Delivered** |
| 47 | Results-out fields | `Backlog` | **Delivered** |
| 54 | Persist attempts on `/trials` | `Backlog` | **Delivered** — firmware half (Ref 53) still open; they land together |
| 57 | Retry / backoff + error classes | `Backlog` | **Delivered** — built early, ahead of its W4 sprint |
| 56 | Idempotent Airtable upsert | `Backlog` | **In Progress** — mechanism built and unit-tested; unproven live, blocked on the write approval |
| 36 | **Phase 2 · Requirements IN** | `Blocked` | **Blocked** — *reason replaced*: old blocker (unknown structure) closed; new blocker is the extraction defect |
| 38 | **Phase 4 · Results OUT** | `Backlog` | **To Do — pulled forward ahead of Phase 2** |
| 30 | Implement integration with Airtable | In Progress | *(unchanged)* — notes refreshed |

Unchanged and correct: Refs 33, 37, 39, 40, 48–53, 55, 58–65.

**Sprint labels (`Week 1`…`Week 5`) were deliberately left alone.** They name the plan's *phases*, which
still hold; it is the calendar that moved, and that is recorded on the status page rather than by
relabelling forty rows.

**Not touched:** MCAIT / Cowork pages (different project), session logs (accurate as written).
