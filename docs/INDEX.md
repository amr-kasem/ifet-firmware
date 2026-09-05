# IFET Project — Documentation Index

**Maintained by:** Abdelrahman · **Reconciled:** 2026-09-06 (previously 2026-08-31)
**Scope:** every LabOS ↔ Airtable integration and status document, across both repos and Notion.

---

## 0. Resume here — state as of 2026-09-06

> ### ✅ Read this first — state as of 2026-09-06
>
> **Scope widened to all five test types, and the design package is drafted and awaiting review:**
> `labos-airtable/design/integration-design-2026-09-05.md` + `design/field-register-2026-09-05.csv`.
> **Nothing has been applied** — no Airtable schema mutation, no migration, no container.
>
> **The Airtable team shipped schema changes without announcing them.** Today's read-only baseline
> (`schema/baseline-2026-09-05/`) diffed against 2026-08-23 shows **all five `Test Type` options live in both
> bases** (**§10.17 closes** — the P0 that blocked every manual-test write is gone), **`Test Date` is now
> `dateTime`** (**§10.20 closes**), and **`Correction Reason` was added**. Always diff the baseline before
> assuming §10 is current.
>
> **Six decisions settled, five gates left, each with one owner:** G1 deflection calibration (**ours** —
> needs a rig), G2 the `+110/110` sign convention and the section→kind map (**theirs**), G3 the extraction
> defect (**theirs**), **G4 no measurement source for pressure** (**ours**), **G5 `Corrects Attempt ID` not
> delivered** (**theirs**). Design package §2 and §3.
>
> **G4 is the one to read — §3.1.** The firmware → Management trial payload is **exactly one field**,
> `deflections[]`: no pressure, no duration, no cycles, no timestamps. So **`Max Pressure Achieved` has no
> source at all**, and `Measured Value` has one only for operator-entered tests. Static pressure is an
> open-loop browser slider, so the configured setpoint is not an achieved value either. Both fields are
> omitted, on the same terms as deflection.
>
> **§3.2 — a completeness check, stated at the right strength.** `Cyclic present ∧ DP absent` proves the
> required input for LabOS's own execution is missing — certain, and it coincides with 3 of the 6 live
> specimens. It does **not** by itself prove an extraction defect; that needs Airtable to confirm the
> cross-protocol requirement (Q10). And the safeguard is an **execution rule**, not an acknowledgement: the
> backend refuses to start a pressure-driven test without a `proposal`- or `operator`-sourced pair.
>
> **Polling is full reads, not deltas.** There is **no whole-record modification timestamp anywhere in the
> base** — the three `lastModifiedTime` fields that exist are field-scoped. At 85 records that is four
> requests a cycle; revisit around 10⁴.
>
> **D7 decides the data model — read it before touching any constraint.** A LabOS `StaticTest`/`CyclicTest`
> row is a **stage**, not a test: one `DP (+) (PSF)` section expands into **6 static / 8 cyclic** derived
> stages (verified live — min 6, min 8, 498 of 508 `preset`). So **one Airtable attempt row per *programme
> run*, not per stage**, via a new `test_programme_runs` entity; `labos_test_id` identifies the programme.
> This revises P1's mapping — cheap now, expensive later — and it overturns the draft's
> "`airtable_section_id` unique across test rows", which would have rejected every correct programme.
>
> **Corrections never rewrite.** A recorded verdict is immutable (`verdict_at` set once, enforced in the
> database); a correction mints a **new attempt** carrying `Corrects Attempt ID`. That is what makes **G5**
> block more than it appears to. And delivery is **ordered per attempt** (`sync_outbox.attempt_seq`,
> head-of-line blocking per attempt, parallel across attempts) so a verdict can never land ahead of the
> measurements it refers to.
>
> **Also established today:** `Protocol Sections` is an **EAV table** (`Section Name` / `Value` free text) —
> the requirements *do* exist in Airtable, they are just untyped. LabOS holds **32 jobs / 79 specimens / 640
> attempts** against Airtable's **1 / 6**, so linkage is a going-forward exercise, not a backfill. The React
> UI source exists in **no** repo or node but is recoverable from the deployed bundle's sourcemap.
> Production `alembic_version` re-confirmed **`3a65a83e0463`**.
>
> **⏸️ Implementation is PAUSED pending review (2026-09-06).** Two deliverables are on the desk:
> `design/decisions-awaiting-approval-2026-09-06.md` — **eight decisions, A1 first** (programme run vs stage;
> it is structural and revises P1's mapping) — and
> `correspondence/airtable-team-questions-2026-09-06.md`, **drafted and NOT sent**. The outbox commits stand
> as groundwork: they import only `sqlalchemy`, `data.models.Base` and `airtable.errors`, so no open decision
> reaches them.
>
> **Sequencing rule:** the transport layer may be built against open gates; **nothing that reads the field
> register may.** `test_programme_runs`, the envelope changes, the mirror and the endpoints all wait.
>
> **Next:** review the two deliverables → send the correspondence (that is what starts G2/G3/G5 moving) →
> Testing Base changes. UI work stays deferred.

> ### State as of 2026-08-31 — superseded above, kept for the record
>
> **They replied, in one working day. The blocker is no longer "waiting on Airtable" — it is tonight's call.**
>
> Their message asks three things: how we want `Required Value` represented machine-readably (plus a unit per
> protocol section), confirmation of the retest row model **with the shared `LabOS Test ID` replacing
> `Corrects Attempt ID`**, and notice that `Test Date` becomes a `dateTime`.
>
> **Our answer is written and ready to send:** `labos-airtable/correspondence/airtable-team-questions-2026-08-31.md`
> — §2 is the read-side field spec they asked us for, §3 is why we decline the `Corrects Attempt ID`
> substitution, §5 is the agenda for the call, §7 is the reply to paste.
>
> **Two accepted, one declined:**
> - **Q1 — accepted, and it is the win here.** They are asking us to write the read-side spec, which is the
>   item that has been the critical path since 2026-07-23. Contract §10.3 / §10.15 / §10.23 / §10.24 close
>   together if they take the spec.
> - **Q3 — accepted.** `dateTime` closes §10.20 on delivery. §10.13 survives it: one instant still cannot hold
>   both start and end.
> - **Q2 — row model confirmed, substitution declined.** The shared `LabOS Test ID` is already in every payload
>   and answers a different question. §10.14 stays blocking.
>
> **What their message does *not* touch — and what tonight has to land:** the extraction shift (**§10.19**,
> P0), the four missing `Test Type` options (**§10.17**, P0), and the go-ahead for the single test write.
> Order the call by blast radius, not by their agenda.
>
> **Build facts unchanged:** 132 tests green, both bases probed read-only, nothing deployed — production
> `alembic_version` re-confirmed `3a65a83e0463` on 2026-08-31, and live `test_results` still has five columns.
> Nothing on our side waits on them except that one write approval.
>
> **Production read 2026-08-31 — `evidence/labos-real-data-types-2026-08-31.md`.** It confirmed the derivation
> to full float precision across 1127 rows, put real numbers behind two asks (**46%** of jobs have asymmetric
> design pressures; **one test in five** already has multiple attempts), and corrected three of our own claims.
> **It also opened contract §10.27 — a LabOS-side data-quality problem: deflection values are not plausible as
> inches** (`max_deflection` spans −1280.91 → 1288.86). That must be understood before we write
> `Deflection Value` to anyone, and it needs a place in the R-week plan.
>
> **Next actions, in order:**
> 1. **Send the §7 reply / run the call.** Then close the affected items in contract §10 **first**, and stamp
>    §8 of the correspondence doc.
> 2. **Get the maintenance window**, then work `labos-airtable/runbooks/p0-p1-deploy-2026-08-28.md` — read its
>    §2 first, `alembic_version` decides whether the deploy can happen that day.
> 3. **Start P4** — the durable sync queue and worker. The real remaining build; needs nothing external.
>
> Stage 3 remains ready: `ifet-management` `tests/stage3_live_write.py`, dry-run verified, production base
> refused unconditionally.

> ### State as of 2026-08-28, end of day — superseded above, kept for the send record
>
> **Both documents are sent. The five-day blocker is cleared.**
>
> - **To the Airtable team:** the live-base verification report —
>   `labos-airtable/correspondence/sent/2026-08-28-labos-airtable-live-base-verification-report.docx`. Wording of record: findings §8,
>   now stamped *Sent*, with the six things the sent version added over the draft.
> - **To IFET management:** *📌 LabOS × Airtable — Project Status & Revised Timeline (2026-08-28)*,
>   `3ca57bad43d581e5b28ece91494a45a7`, in answer to the PM's escalation.
>
> **The build facts below are unchanged and were re-verified 2026-08-28:** 132 tests green, both bases
> probed read-only, schema identical to 23 Aug. Nothing deployed.
>
> **New open item from the sent report: contract §10.23** — how is `+60/60` represented once `Required Value`
> is numeric? Blocking: unresolved, we are parsing pressures out of free text again.
>
> **Next actions, in order — none of them is "send something":**
> 1. **Wait on their reply.** Stage 3 is a script and is ready: `ifet-management`
>    `tests/stage3_live_write.py`, dry-run verified, production base refused unconditionally.
> 2. **Get the maintenance window**, then work `labos-airtable/runbooks/p0-p1-deploy-2026-08-28.md` — read its §2
>    first, `alembic_version` decides whether the deploy can happen that day.
> 3. **Start P4** — the durable sync queue and worker. The real remaining build; needs nothing external.
>
> Assessment: `labos-airtable/status/delivery-status-2026-08-28.md` · dates: `labos-airtable/status/revised-roadmap-2026-08-28.md`.

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
2. **A Monday message is written and unsent** — `labos-airtable/evidence/live-probe-findings-2026-08-23.md` §8. Luis
   was away for the weekend; a joint testing session is booked. Stamp the *Sent* line when it goes.
3. **⚠️ Deploy hazard.** Until the `startup.sh` change ships, every container restart appends a no-op
   revision on the node and moves the head. Deploy `startup.sh` **and** the P1 migration together, and
   re-confirm `SELECT * FROM alembic_version;` still returns `3a65a83e0463` immediately beforehand — a head
   we do not descend from means two heads and `upgrade head` silently refuses.

### The shortest path — do these two, in this order

**1. Send the Monday message.** Authoritative wording is
`labos-airtable/evidence/live-probe-findings-2026-08-23.md` **§8** — send it as written, don't re-draft it. The call is
**Monday 2026-08-25** with Luis; §7 is the agenda, ordered by what blocks the most. When it goes out, stamp the
*Sent* line at the end of §8 the same day.

**2. Then verification stage 3** — one live upsert round-trip into the **testing** base. The last step before
W3/W4. Three things to know before running it:

- **It is gated on Luis's explicit OK**, which is exactly what the §8 message asks for ("For Monday", item 3).
  Send first, get the go-ahead on the call, then run. Production base `app0OCunbmuXl7Hc9` is never touched.
- **⚠️ The stage 3 spec in `labos-airtable/correspondence/verification-report-2026-07-29.md` is stale — do not run its payload
  as written.** It targets the retired sandbox `appYBTqIL43pmS0xN` / `LabOS Raw Test Results`, and sends
  `Testing Start Date` / `Testing End Date`, which do not exist on the live table (it is `Test Date`, and it is
  date-only — §10.20). The *fourteen checks* it describes still stand; re-point them at the real target from
  contract **§0.1 + §2**: `PATCH .../app4oXS3Kd5IKWgJ7/tblnc9SsbXU0C0FWh`, upsert on `LabOS Attempt ID`.
- **The test record must be `Static Load`.** Four of the five test types are refused by the live `Test Type`
  option set (§10.17), so static load is the only type that can be written back at all until item 2 lands.

### After that — none of these are blocked either

- ~~**Notion is four pages behind**~~ — ✅ **synced 2026-08-28**, see §4.
- **Firmware `/trials` seam** (gap H, Refs 53 ↔ 54) — must land on both sides together.
- Answer the open question in `labos-airtable/evidence/p1-schema-and-migration-mechanism-2026-08-23.md` §7: may an operator
  edit a *terminal* attempt's notes/photos? Likely split — artifacts appendable, results require a correction.

### Two practical notes

- **Rehearsing the migration needs SQLAlchemy**, which is not on the system Python. Rebuild the throwaway env
  with `uv venv <dir> && VIRTUAL_ENV=<dir> uv pip install sqlalchemy alembic`, then
  `<dir>/bin/python tests/rehearse_p1_migration.py /tmp/x.db`.
- **Reaching a node:** use the `ifet-ssh` skill. Mutating commands are blocked by the auto-mode classifier and
  have to be handed to the user; read-only ones run fine. Session record:
  `operations/ssh-session-record-2026-08-23.md`.


> **Why this file exists.** The same fact was living in five places and starting to drift — three different
> open-item lists, a contract version that had moved on, a P0 task marked "next" after it was done, and a VFD
> Modbus address in the config docs that production stopped using in July. This index fixes the pattern rather
> than the instances: **each subject has exactly one owning document**, and everything else is explicitly a
> *view* of it.

---

## 1. Single source of truth — which document owns which subject

*Paths in this file are relative to `docs/`. Documents elsewhere in the repo, and in `ifet-management`, are
written out in full.*

| Subject | **Authoritative document** | Views that must follow it |
|---|---|---|
| **Open integration items / what blocks what** | `labos-airtable/contract/write-contract-v0.3.md` **§10** | §3 of this file · Notion *Field Mapping* §5 · Notion *Delivery Status* |
| **The write envelope** — fields, types, required-per-test-type, blank rules, upsert, immutability | `labos-airtable/contract/write-contract-v0.3.md` §4/§5 | Notion *Field Mapping* §2 · `ifet-management` `app/airtable/contract.py` — **a view; the prose wins on disagreement** |
| **Airtable environments, base IDs, table IDs, PAT scopes** | `labos-airtable/contract/write-contract-v0.3.md` **§0.1** | `ifet-management` `app/config.py` · §2 of this file · everything else |
| **Field-name mapping** LabOS ↔ Airtable, and ratification per row | Notion *[Field Mapping (Working)](https://app.notion.com/p/3a357bad43d581c68ea1c85411429cac)* | the contract's field tables |
| **Where the project stands** | `labos-airtable/status/delivery-status-2026-08-28.md` | Notion *Delivery Status* · §3 of this file |
| **Dates, sequencing, and what would move them** | `labos-airtable/status/revised-roadmap-2026-08-28.md` | Notion *📌 Project Status & Revised Timeline* (**the page management holds**) · Notion *5-Week Plan* |
| **Internal plan — gaps A–J, pre-closed decisions, week sequencing** | `labos-airtable/status/internal-plan-2026-07-23.md` | Notion *Internal Engineering Plan* (private copy) |
| **What we have verified against the live bases** | `labos-airtable/evidence/live-probe-findings-2026-08-23.md` | `labos-airtable/correspondence/verification-report-2026-07-29.md` (historical) · Notion *Verification Report* |
| **What LabOS really stores — types, derivations, units** | `labos-airtable/evidence/labos-real-data-types-2026-08-31.md` | the read-side spec in `labos-airtable/correspondence/airtable-team-questions-2026-08-31.md` §2 · contract §10.3 · §10.19 · §10.24 · §10.25 |
| **How our envelope compares to their actual data** | `labos-airtable/evidence/reference-row-reconciliation-2026-08-28.md` | contract §10.24–§10.26 |
| **What the rigs actually receive, do and return — the Management ↔ Firmware execution contract** | `labos-airtable/evidence/firmware-production-runtime-contract-2026-08-31.md` | `labos-airtable/evidence/labos-real-data-types-2026-08-31.md` (the read side of the same boundary) · contract §10.19 · §10.27 · `hardware/README.md` · the VFD/serial gotchas in `CLAUDE.md` |
| **How a schema change reaches production** (alembic, bind mounts, autogenerate-at-boot) | `labos-airtable/evidence/p1-schema-and-migration-mechanism-2026-08-23.md` | `ifet-management` `startup.sh` + `compose.yaml` are the mechanism it documents |
| **What we asked the Airtable team for, and why** | `labos-airtable/correspondence/sent/2026-08-28-…-verification-report.docx` — **the artifact they hold** | `labos-airtable/evidence/live-probe-findings-2026-08-23.md` §8 (the wording, plus what the sent version added) · `labos-airtable/correspondence/v2-guide-reconciliation-2026-08-22.md` §5 |
| **Our answer to their three questions of 2026-08-31, and the read-side field spec** | `labos-airtable/correspondence/airtable-team-questions-2026-08-31.md` — **the wording of record** | contract §10 items 3 · 8 · 13 · 14 · 15 · 20 · 23 · 24 · 25 (the *statuses*) · the sent artifact once it goes out |
| **How to deploy P0/P1 to `management`** | `labos-airtable/runbooks/p0-p1-deploy-2026-08-28.md` | `ifet-management/deployment/SECRETS.md` §2 |
| **How to run the stage-3 write** | `ifet-management` `src/management_service/tests/stage3_live_write.py` — **the script is the spec** | `labos-airtable/correspondence/verification-report-2026-07-29.md` §4 (the original fourteen checks; **its payload is retired**) |
| **Secret handling** | `ifet-management/deployment/SECRETS.md` | this index |
| **Repo/branch/production ground truth, and node git guardrails** | `operations/branch-reconcile-plan-2026-07-24.md` | Notion *Execution Record* |
| **What was run on a node, when, and with what blast radius** | `operations/ssh-session-record-2026-08-23.md` | — each session gets its own record |
| **Cross-team schedule and per-week deliverables** | Notion *[5-Week Integration Plan](https://app.notion.com/p/3a657bad43d581e59490f53a8eeedbf6)* | — |
| **Live task status** | Notion *Delivery & Progress Tracker* (Epic IFET-32) | — |
| **Hardware config — Modbus, VFD, valve pins** | `hardware/README.md` | — |

**Rule:** when an item closes, close it in the authoritative document **first**, then update the views the
same day. If two documents disagree, the authoritative one wins and the other is a bug.

---

## 2. Document inventory

### How this directory is organised

Folders encode **what a document is for** — the same distinction §1 makes between an authoritative document
and a view of it. A file's location tells you how much weight to give it.

```
docs/
  INDEX.md                     the map - start here, and the only path referenced from outside docs/
  labos-airtable/              the integration (Epic IFET-32)
    contract/                  THE SPEC. Authoritative. Everything else defers to it
    status/                    where we are - views, each naming its source
    evidence/                  what we verified, and how. Records, not opinions
    correspondence/            what was exchanged with the Airtable team
      sent/                    the exact artifacts they received
    runbooks/                  how to execute something risky, step by step
    design/                    proposals under internal review. Each file names where its parts fold
                               on approval - this folder is a staging area, never authoritative
    schema/                    field-ID snapshots of both live bases
  operations/                  node and repository operations
  hardware/                    rig configuration and bring-up records
```

**Rules that keep it usable:**

- **A document is filed by role, not by topic.** A status page about the contract belongs in `status/`, not
  `contract/`. If you cannot tell which folder something goes in, it is probably two documents.
- **`contract/` holds exactly one file.** If it ever holds two, one of them is a view and is misfiled.
- **`correspondence/sent/` is append-only.** Those are artifacts other people hold; they are never edited
  after sending. Corrections go in a new document.
- **Dates in filenames are when the work happened**, not when the file was last touched. That is how a
  superseded record stays findable.

---

### `labos-airtable/` — the integration

| Document | Purpose | Status |
|---|---|---|
| **`contract/write-contract-v0.3.md`** | **The spec both teams build against.** Identity, idempotency, the attempt lifecycle, retest vs. correction, the field envelope, blank rules, JSON shapes, retry classes, the live base/table IDs (§0.1), and **§10 — the canonical open-items list, 27 items, re-reconciled 2026-08-31**. | **`v0.3 DRAFT`** — ratifies to `v1.0` when §10 closes |
| `status/delivery-status-2026-08-28.md` | **Current assessment.** What is built and verified, the schedule stated plainly, the extraction defect measured against the sample job, what is blocked and on whom. | **current** |
| `status/revised-roadmap-2026-08-28.md` | **The dates.** R1–R6 to a pilot go-live of 2026-10-09, what would move them, a dated target per Airtable ask, and four asks back to IFET. | **current** |
| `status/readiness-2026-08-23.md` | Human overview written at the end of W2. Superseded on dates and open items by the two above; still the clearest single narrative of how the integration fits together. | superseded on status |
| `status/internal-plan-2026-07-23.md` | Internal superset: gaps A–J, nine pre-closed decisions, week sequencing with off-dashboard firmware work. | current (updated 2026-08-23) |
| `evidence/live-probe-findings-2026-08-23.md` | **First live read of both bases.** What the schema holds, six items closed and six opened, the proposal-extraction defect (§5.2), and **§8 — the message wording, now stamped *Sent*** with the six ways the sent version improved on it. | current |
| `evidence/reference-row-reconciliation-2026-08-28.md` | **Our envelope vs. the Airtable team's own sample row** `recxZWiVa5Wuy0ZV6`. The `Inches`/`in` divergence, the JSON-shape divergence, and why the empty testing base does not block stage 3. | **current** |
| **`evidence/labos-real-data-types-2026-08-31.md`** | **The real types behind the read-side spec.** That LabOS derives 14+ test stages from the design-pressure pair (so Airtable models no ranges); that `60 × 0.15 = 9` proves the extraction shift arithmetically; that deflection is three numbers per gauge, not one; and the true unit inventory, which corrects §4.4. | **current** |
| **`evidence/firmware-production-runtime-contract-2026-08-31.md`** | **What the rigs actually do.** Read-only audit of `system-1`, `system-2`, `management`. Establishes that Management owns 100% of programme derivation (Model B via callback pull, validated to full precision against project 78); that the firmware→Management result payload is `deflections[]` and nothing else — no pressure, duration, cycle count, timestamp or verdict; that **`recovery` is the `recovery_time` config constant (60 s), not a measurement**; that the implausible deflections are raw IO-Link counts × 0.0393701 mislabelled as inches, with the defect in the SICK gateway rather than the firmware; that **`Gauge 1..4` rows and every populated `result` are `populate_db.py` seed data**, separable by `deflection_gauge ~ '^[12]-[1-8]$'`; that **nothing writes `TestResult.result`**, so Pass/Fail has no owner; that cyclic cycles are open-loop at 2.02 s each and static pressure is driven by the operator's browser slider; and that water infiltration executes as a 900 s static hold at 0.15 × inward DP. Closes the `recovery` limb of contract §10.27 and sharpens §10.19. §20 is the meeting decision table. | **current** |
| `evidence/firmware-production-probe-2026-08-31.txt` | Command log for the above — every read-only command, the SELECT-only SQL, and what was deliberately **not** run. | current |
| `evidence/p1-schema-and-migration-mechanism-2026-08-23.md` | W2/P1 evidence: the attempt schema, and the discovery that migrations were gitignored, bind-mounted from the node, and autogenerated at every container boot. | current |
| `correspondence/sent/2026-08-28-…-verification-report.docx` | **The artifact the Airtable team actually received.** Five asks with a P0/P1/P2 priority table. | 📨 sent — do not edit |
| **`correspondence/airtable-team-questions-2026-09-06.md`** | **The reply on the desk.** §1–§3 answer their three questions — typed requirement fields argued from live production counts, why a shared `LabOS Test ID` cannot express supersession, and `Test Date` accepted with start-vs-completion still open. §4 reports what the 2026-09-05 baseline found in their base, including three of six specimens with cyclic pressures and no design pressure. §5 is the ask list, **only items needing them**, ordered by blast radius; our own gates are excluded. §7 is paste-ready. | **`DRAFT` — NOT SENT** |
| **`design/decisions-awaiting-approval-2026-09-06.md`** | **Eight decisions needing sign-off**, and the note on what the existing outbox commits do and do not commit us to. **A1 is structural** — programme run vs stage, which revises P1's mapping and determines every uniqueness rule. | **awaiting review** |
| `correspondence/airtable-team-questions-2026-08-31.md` | Their three questions and our answer. §2 the read-side field spec they asked for (typed `Required Value` + `Requirement Kind` + the unit-per-section table), §3 why the shared `LabOS Test ID` cannot replace `Corrects Attempt ID`, §4 `Test Date`, §5 the agenda ordered by blast radius, **§7 the reply, ready to send**. | **current — not yet sent** |
| `correspondence/v2-guide-reconciliation-2026-08-22.md` | Delta against their *API Integration Guide v2*, plus §5, the correspondence record. | historical |
| `correspondence/team-doc-review-2026-07-29.md` | Review of their **v1** schema doc, and §7, the message sent 2026-07-29. | ⚠️ superseded by their v2 — kept verbatim as the sent record |
| `correspondence/verification-report-2026-07-29.md` | The ownership boundary and the proposed HTTP requests. Stages 1–2 executed 2026-08-23. | 📕 historical — **its stage 3 payload is retired; the script and runbook replace it** |
| `runbooks/p0-p1-deploy-2026-08-28.md` | **The `management` deploy.** Its §2 is the decision point — whether `alembic_version` has moved decides if the deploy can happen that day at all. | **ready to execute** |
| **`design/integration-design-2026-09-05.md`** | **The draft design package for the five-test-type flow and the sync service.** Six decisions settled in session (deflection export blocked; the verdict stays in LabOS; operator is a *declared* identity; UTC on the wire with `date` fields rendered `America/New_York`; keep the DB names and fix the vocabulary at the boundary; free-text pressures preserved, typed fields for execution). **Five gates** with named owners — including **G4, no measurement source for pressure** (§3.1), which the register itself exposed by demanding a source for two fields that had none. The transactional-outbox architecture, the four-phase "eventually complete" write that amends v0.3's terminal rule (with the monotonic guard and the measurement freeze that make it safe), **full-read polling** because the base has no whole-record modification timestamp, remote-authoritative attachment dedup, per-entity uniqueness, the endpoint list, the programme-vs-stage identity resolution (**D7**) that decides every uniqueness rule, correction immutability, per-attempt delivery ordering, a nine-step sequence and a 50-case acceptance suite. | **`DRAFT` — under review, nothing applied** |
| **`design/field-register-2026-09-05.csv`** | **The machine-readable field mapping**, 57 rows, both directions, keyed on field *names* because IDs differ per base. Carries `write_phase`, the rule, and `AGREED`/`PROPOSED`/`BLOCKED` with the gate named. Folds into contract `v0.4`. | **`DRAFT`** |
| **`schema/baseline-2026-09-05/`** | **Pre-change baseline, both bases, read-only** (`app/airtable/baseline.py`). Schema JSON + flat field CSV, 8 tables and 142 fields each. Diffing it against 2026-08-23 is what found that the Airtable team **shipped all five `Test Type` options, `Test Date` as `dateTime`, and `Correction Reason`** — closing §10.17 and §10.20. Record CSVs are deliberately **not** here: both repos are public and `IFET Projects` carries customer emails and invoice amounts. They live outside every work tree. | **current** |
| `schema/schema-{testing,production}-2026-08-23.json` | Field-ID snapshots of both bases, for drift detection at deploy. | current |

### `operations/` — nodes and repositories

| Document | Purpose | Status |
|---|---|---|
| `branch-reconcile-plan-2026-07-24.md` | Repo ↔ production reconcile. Node baselines, container audit, and **the git guardrails for a live node** — still load-bearing for any deploy. | 🔒 CLOSED — Step E/F fold into the next deploy |
| `ssh-session-record-2026-08-23.md` | The 2026-08-23 session on `management`: every command, what it returned, and what was *not* touched. All read-only. | current |

### `hardware/` — rigs

| Document | Purpose | Status |
|---|---|---|
| `README.md` | Hardware configuration — Modbus RTU, Delta C2000 Plus VFD over serial and TCP, valve pin maps. | current (VFD address corrected to `12`) |
| `system1-sensor-vfd-debug-2026-07-07.md` | system-1 bring-up: sensors, the VFD-at-address-12 finding, PSF scaling. | historical |
| `system1-sensor4-5-addition-2026-07-08.md` | system-1 sensor 4/5 addition. | historical |

### `ifet-management/`

| Document | Purpose | Status |
|---|---|---|
| `deployment/SECRETS.md` | Where every credential lives, the secret-hygiene guard, and the gated migration runbook. | current — **deployment gated** |
| `src/management_service/tests/stage3_live_write.py` | **Stage 3, as a script.** Dry-run by default; `--live` requires `--approved-by`; the production base is refused unconditionally. | ready, awaiting approval |
| `src/management_service/DATABASE_MIGRATIONS.md` | Alembic usage. | pre-existing |

### Airtable (theirs — read-only to us)

| Resource | Link / ID | Notes |
|---|---|---|
| Production dashboard | [interface page](https://airtable.com/app0OCunbmuXl7Hc9/pagGRZZBAH691m3x5) | Human-facing only; interfaces are not exposed by the Meta API |
| Testing base | `app4oXS3Kd5IKWgJ7` | Where LabOS builds. **Completely empty** — 0 records in every table |
| Production base | `app0OCunbmuXl7Hc9` | Holds the sample job `IFET-26-0066` and their reference row `recxZWiVa5Wuy0ZV6` |
| Write target | `tblnc9SsbXU0C0FWh` | The only writable surface, in either base |

### Notion — [LabOS hub](https://app.notion.com/p/3a357bad43d5818cb726d24c5e803c69)

All reconciled 2026-08-28 (§5). Ordered by who reads them.

| Page | Audience | Status |
|---|---|---|
| *📌 Project Status & Revised Timeline (2026-08-28)* | **management — sent to the PM** | **current — the executive view** |
| *📊 Delivery Status (2026-08-28)* | internal | current |
| *🗓️ Revised Roadmap & True Timeline (2026-08-28)* | internal | current |
| *🗓️ 5-Week Integration Plan* | cross-team | current — dates superseded, asks rewritten |
| *🗺️ Field Mapping (Working)* | cross-team | ⚠️ §1–§3 tables predate the live probe — **corrections table at the top**; §5 rewritten |
| *Delivery & Progress Tracker* (Epic IFET-32) | cross-team | live board — statuses reconciled against the code |
| *📕 Verification Report* · *Response v0.2* · *Contract v0.1* · *Readiness Evaluation* · *Adaptation Plan* · *Change Summary* | internal | historical — all bannered |
| *Internal Engineering Plan* | private | current-position banner added |
| *Branch Reconcile — Execution Record* | internal | 🔒 closed |

---

## 3. Status snapshot — 2026-08-28

*A view. The assessment is `labos-airtable/status/delivery-status-2026-08-28.md`; the dates are
`labos-airtable/status/revised-roadmap-2026-08-28.md`; the open items are contract §10.*

| | |
|---|---|
| **Milestones** | **2 of 5 delivered and verified** — W1 foundations, W2 schema & identity. W3/W4/W5 not started. The original window (2026-07-23 → 2026-08-27) has **closed** |
| **Revised target** | **Pilot go-live Friday 2026-10-09**, six working weeks from 2026-08-31, **W4 pulled ahead of W3** |
| **Deployed** | **Nothing.** Production runs the July build. Both integration branches are pushed, clean, unmerged |
| **Tests** | **132 offline, green** — re-verified 2026-08-28, stdlib-only |
| **Contract** | `v0.3 DRAFT`. §10 now runs to **26 items** — 23–26 opened 2026-08-28 by writing up the verification report and diffing their reference row |
| **Correspondence** | ✅ **Both documents sent 2026-08-28** — the verification report to the Airtable team, the status page to IFET management. **The blocker is now their reply, not our send** |
| **Their latest** | *API Integration Guide* **v2**, 2026-08-17 · their sample row `recxZWiVa5Wuy0ZV6`, written 2026-08-10 |
| **Tokens** | Both PATs held in the gitignored `.env` (mode 600). **Rotate after acceptance testing** — they arrived by plaintext email |
| **Ready and waiting** | **Stage 3 as a script** (`tests/stage3_live_write.py`, dry-run verified, production base refused unconditionally) · **the P0/P1 deploy runbook** (its §2 decides whether the deploy can run that day) |
| **Blocked on the Airtable team** | §10.19 extraction defect (**highest severity — already reached a `Passed`/`Completed` record**) · §10.17 `Test Type` has one option · §10.24 unit vocabulary (**our envelope refuses their `Inches`**) · §10.25 JSON shape · §10.14 correction fields · §10.23 how `+60/60` is represented · §10.3 typed requirement values · approval for the stage-3 write |
| **Blocked on IFET** | a **maintenance window** for the P0/P1 deploy · the **`test` node**, offline since ~2026-07-24, leaving no non-production rig · a decision on reviewing already-reported results, once the extraction blast radius is known |
| **Not blocked** | **W4 — the durable sync queue and worker.** Retry/backoff (Ref 57) and the upsert mechanism (Ref 56) are already built; the queue, the worker and the sync-status UI are not. This is the real remaining build |

> **The honest read, 2026-08-28.** The build is in good shape and further along than the week counter
> suggested — two milestones delivered, 132 tests green, both bases read end to end. The delivery is behind,
> and until today the reason was ours: a message written on 2026-08-23 and not sent. That is now closed.
>
> Two things carry forward. **The extraction defect is a safety item, not a data-quality one** — a rig driven
> from `DP = 9` would under-load a specimen sevenfold, pass it, and certify it, and a `Passed`/`Completed`
> record already exists against a requirement the proposal does not contain. And **free-text unit fields are
> quietly dangerous**: their row says `Inches`, ours says `in`, the column would accept both, and our own
> envelope refuses theirs — so it is unsendable rather than merely untidy.

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

- **Subject ownership moved.** "What we've verified" now belongs to `labos-airtable/evidence/live-probe-findings-2026-08-23.md`; the 2026-07-29 verification report
  is re-labelled **historical** rather than "superseded in part", because its stage 1 and 2 were actually
  *executed* on 2026-08-23. Its banner now scores the plan against the outcome instead of just warning.
- **Six §10 items closed with evidence** rather than argument, and six opened. §10 went from 16 items to 22.
- **§10.16 closed against us** — the live base holds `Passed`/`Failed`. Their v2 example was right and the
  contract was wrong. Recorded that way in contract §4.3, in the reconciliation doc's §6.1 post-mortem, and
  here, because a reconcile that only ever finds the *other* side wrong is not being honest.
- **Gap J closed, gap I answered.** The internal plan's gap list had both open; J's `fld…`-ID snapshot now
  exists for both bases under `labos-airtable/schema/`, and I turned out to have a third answer neither side
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

## 5. Notion reconciliation — 2026-08-28

Notion had drifted a month behind the repo, and the **task board was the worst of it**: Phases 0 and 1
were finished while the board still read `To Do` / `Backlog`. Everything below is now reconciled.
**Repo docs stay authoritative** (§1); Notion pages are views.

### 5.1 Documents

| Notion page | What was done |
|---|---|
| **📌 LabOS × Airtable — Project Status & Revised Timeline (2026-08-28)** `3ca57bad43d581e5b28ece91494a45a7` | **The page actually sent to IFET management on 2026-08-28.** Executive view — status at a glance, the extraction defect, the five remaining Airtable items, the R1–R6 plan, and the reporting commitment. Parented under `ifet`, not under the LabOS hub; linked from the hub. **This is the page the PM reads** |
| **🗓️ Revised Roadmap & True Timeline (2026-08-28)** `3ca57bad43d581e5b7d4fc3dda389294` | **New.** The answer to the PM's escalation: revised dates, what would move them, dated targets per Airtable ask, and four asks back to IFET (maintenance window · `test` node · weight behind the extractor fix · the review decision). View of `labos-airtable/status/revised-roadmap-2026-08-28.md` |
| **📊 Delivery Status — LabOS × Airtable (2026-08-28)** `3ca57bad43d581f8b996e63764f5cbfc` | **New.** Human-readable status + a standalone *What we need from the Airtable team* section written to be lifted straight into a message. View of `labos-airtable/status/delivery-status-2026-08-28.md` |
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

### 5.2 Delivery & Progress Tracker — Epic IFET-32

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

### 5.3 Sent artifacts

| Artifact | Recipient | Kept at |
|---|---|---|
| *LabOS – Airtable Integration: Live Base Verification, Data Integrity Findings, and Requested Actions* | IFET / Airtable integration team | `labos-airtable/correspondence/sent/2026-08-28-labos-airtable-live-base-verification-report.docx` |
| *📌 LabOS × Airtable — Project Status & Revised Timeline (2026-08-28)* | IFET management | Notion `3ca57bad43d581e5b28ece91494a45a7` |

The `.docx` is kept in-repo deliberately: it is what they actually received, and findings §8 is only the
draft behind it. §8 now records the six ways the sent version improved on that draft, so the next message
stays consistent with what they hold.
