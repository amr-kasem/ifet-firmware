# IFET Project — Documentation Index

**Maintained by:** Abdelrahman · **Scope:** the LabOS ↔ Airtable integration (Epic IFET-32) across both repos
and Notion. This file is a **map**, not a status report — it says which document owns which subject, and
nothing else. Status lives in the delivery plan.

---

## 0. Resume here

**Two documents carry everything current:**

| | |
|---|---|
| **What the integration *means*** | `labos-airtable/contract/write-contract-v0.4.md` — identity, requirements, review, envelope, sync guarantees, legacy item dispositions. Machine-readable companion: `labos-airtable/contract/field-register.csv` |
| **Where the work *stands*** | `labos-airtable/status/delivery-plan.md` — verified state, the full data path, open gaps, milestones, acceptance, asks. **Living document, edited in place** |

Start with the plan's §0 (probed state) and §1 (the whole data path). Everything else in this tree is
evidence, correspondence or a runbook.

**Five things that outlive any session:**

1. **Nothing is deployed.** Production `management` runs `latest`; live alembic head is `3a65a83e0463`, so
   even P1 is unapplied — **confirm that on the node, not from this repo.** Both integration branches are
   unmerged. `app/sync` **is** wired now (as of 2026-09-08) and proven against the live Testing base; what
   does not exist is the **inbound** half — no mirror, no importer.
2. **Do not drive a rig from Airtable requirement values.** Their PDF extractor shifts columns, so a 60 PSF
   requirement reads as 9, and every shifted value is individually plausible. Contract §10.19.
3. **The node is ground truth for migrations, not the repo.** Check `SELECT * FROM alembic_version;` on the
   live database before any schema work.
4. **A simulated rig must never be able to reach a real broker.** With `ifet-management-tunnel.service`
   active, `127.0.0.1:1883` and `127.0.0.1:8000` are **production**. Use `../simulation/mf_harness/`, never
   `../simulation/ifet_device_node/`, whose config carries system-1's own `device_id`. Plan §5 DG10 · §11.
5. **A test with an injected transport is never evidence about the wire.** Every local suite injects a
   sender that accepts any payload — right for testing the queue, and exactly how a sender that would have
   rejected *every photograph* passed 270 tests. Any path reaching Airtable needs a live probe, or a test
   that stubs the client at its boundary rather than replacing the sender. Plan §0.3a · §0.3b.

---

## 1. Single source of truth — which document owns which subject

| Subject | **Authoritative document** | Views that must follow it |
|---|---|---|
| **What a field, guarantee or state means** — envelope, identity, immutability, upsert, §7.1 concurrency | `labos-airtable/contract/write-contract-v0.4.md` | `labos-airtable/contract/field-register.csv` · `ifet-management` `app/airtable/contract.py` — **a view, and currently stale at v0.3; the prose wins** |
| **Open integration items and what blocks what** | `labos-airtable/contract/write-contract-v0.4.md` **§10** | the plan's §4 and §8 · Notion *Field Mapping* §5 |
| **Airtable environments, base and table IDs, PAT scope** | `labos-airtable/contract/write-contract-v0.4.md` **§0** | `ifet-management` `app/config.py` · §4 below |
| **Field mapping and delivery state** | `labos-airtable/contract/field-register.csv` (73 rows) | `labos-airtable/contract/interface-schema.csv` (generated) · Notion *Field Mapping* |
| **What each base actually holds, per field, both bases** | `labos-airtable/contract/interface-schema.csv` — **generated, never hand-edited** by `ifet-management` `app/airtable/interface_schema.py` | the saved baselines in `labos-airtable/schema/` |
| **What we changed in the Testing Base, and why** | `labos-airtable/evidence/testing-base-changes-2026-09-06/` | the register's APPLIED rows |
| **Where the project stands · gaps · dates · asks** | `labos-airtable/status/delivery-plan.md` | Notion *Project Status & Revised Timeline* (**the page management holds**) · *Delivery Status* · *Internal Engineering Plan* · *5-Week Plan* |
| **What to do next, and what remains** | `labos-airtable/status/delivery-plan.md` **§6.0** — the ordered remaining work, keyed to milestone and `DG` IDs. It owns sequence; state stays in §5 and §8 | the milestone table (§6) · §10 asks |
| **What we verified against the live bases** | `labos-airtable/evidence/live-probe-findings-2026-08-23.md` | Notion *Verification Report* |
| **Every business input and output, per test type** — Airtable field → local storage → source or calculation → outbound field and phase, **including the requirements the 17 additions do not cover** | `labos-airtable/evidence/business-io-reconciliation-2026-09-08/` — 64 rows, the gap and unmet tallies | the plan's §0.3a · §5 |
| **That the wire actually works** — upsert merge semantics, all five types, the whole pipeline through the real worker | `labos-airtable/evidence/live-write-proof-2026-09-08/` — stages 3, 4 and 5 | the plan's §0.3b verification layers |
| **The pre-change schema baseline of both bases** | `labos-airtable/schema/baseline-2026-09-05/` | diffed by `ifet-management` `app/airtable/baseline.py` |
| **What LabOS really stores — types, derivations, units** | `labos-airtable/evidence/labos-real-data-types-2026-08-31.md` | contract §10.3 · §10.19 · §10.24 · §10.25 |
| **How our envelope compares to their own sample row** | `labos-airtable/evidence/reference-row-reconciliation-2026-08-28.md` | contract §10.24–§10.26 |
| **What the rigs actually receive, do and return** — the Management ↔ Firmware execution contract | `labos-airtable/evidence/firmware-production-runtime-contract-2026-08-31.md` | the plan's §5 gaps DG1–DG4 · contract §10.19 · §10.27 · `hardware/README.md` |
| **How a schema change reaches production** (alembic, bind mounts, autogenerate-at-boot) | `labos-airtable/evidence/p1-schema-and-migration-mechanism-2026-08-23.md` | `ifet-management` `startup.sh` + `compose.yaml` are the mechanism it documents |
| **How to deploy to `management`** | `labos-airtable/runbooks/p0-p1-deploy-2026-08-28.md` — **§2 is the decision point** | `ifet-management/deployment/SECRETS.md` §2 |
| **What the Airtable team actually received** | `labos-airtable/correspondence/sent/` — **the artifacts they hold** | every draft in `correspondence/` |
| **Secret handling** | `ifet-management/deployment/SECRETS.md` | this index |
| **Repo ↔ production ground truth and node git guardrails** | `operations/branch-reconcile-plan-2026-07-24.md` | Notion *Execution Record* |
| **What was run on a node, when, with what blast radius** | `operations/ssh-session-record-2026-08-23.md` | each session gets its own record |
| **How to exercise the firmware legs without a rig**, and why a simulated rig must never reach a real broker | `../simulation/mf_harness/README.md` | the plan's §5 DG10 · §11 |
| **Hardware config — Modbus, VFD, valve pins** | `hardware/README.md` | — |
| **Live task status** | Notion *Delivery & Progress Tracker* (Epic IFET-32) | — |

---

## 2. How this tree is organised

Folders encode **what a document is for**. A file's location tells you how much weight to give it.

```
docs/
  INDEX.md                     the map - start here, the only path referenced from outside docs/
  labos-airtable/              the integration (Epic IFET-32)
    contract/                  THE SPEC + its machine-readable register. Authoritative
    status/                    THE PLAN. One living document: state, gaps, milestones, asks
    evidence/                  what we verified, and how. Records, not opinions
    correspondence/            what was exchanged with the Airtable team
      sent/                    the exact artifacts they received
    runbooks/                  how to execute something risky, step by step
    schema/                    field-ID snapshots and pre-change baselines of both live bases
  operations/                  node and repository operations
  hardware/                    rig configuration and bring-up records
```

**Rules that keep it usable:**

- **A document is filed by role, not by topic.** A status page about the contract belongs in `status/`, not
  `contract/`. If you cannot tell which folder something goes in, it is probably two documents.
- **`contract/` holds one prose spec**, plus the register CSV the spec itself names as its companion.
  A second prose spec would mean one of them is a view and is misfiled.
- **`status/` holds one file — the delivery plan — and it is edited in place.** Do not fork it, do not date
  it, do not add a second status document. That is how this tree sprawled to 25 files once already.
- **New dated `.md` files belong in `evidence/` and `correspondence/` only.** Those are genuinely
  point-in-time artifacts. Superseded status and design live in git history, not in the tree.
- **`correspondence/sent/` is append-only.** Those are artifacts other people hold; never edited after
  sending. Corrections go in a new document.
- **Dates in filenames are when the work happened**, not when the file was last touched.

### Inventory

| Document | Purpose |
|---|---|
| **`labos-airtable/contract/write-contract-v0.4.md`** | **The spec.** Environments (§0), ownership (§1), identity (§2), requirements (§3), review/measurements/envelope (§§4–6), sync and §7.1 concurrency mechanisms, legacy dispositions and release checks (§10) |
| **`labos-airtable/contract/field-register.csv`** | 73 mapping rows — **all 73 DECIDED** (44 BASELINE, **14 APPLIED**, 4 CONDITIONAL, 10 OMITTED, 1 PLANNED local-only). The seven former OPEN/PROPOSED rows were closed by A9 and are now OMITTED. **14 decided field additions** were applied. BASELINE means the field exists, never that mapping code exists. One LOCAL_ONLY row is queue metadata and is never created in Airtable |
| **`labos-airtable/contract/interface-schema.csv`** | **Generated.** 168 rows joining both live base schemas to the register: per-base field IDs, `in_testing`/`in_production`, and `labos_use` — including the 114 real fields LabOS deliberately ignores, which is the machine-readable form of "no billing, pricing, invoices or scheduling". Regenerate rather than edit |
| `labos-airtable/evidence/testing-base-changes-2026-09-06/` | **The change document IFET asked for.** 14 fields added 2026-09-06, 142 → 156, with before/after schema, field IDs and the reason for each. Also records the 7 fields deliberately not created, and the three things to settle before production |
| **`labos-airtable/status/delivery-plan.md`** | **The plan.** Probed state, the ten-leg data path, A1–A8, entities/API/concurrency/envelope, the ordered next-actions list (§6.0), gaps DG1–DG11 grouped by state (§5, with the legacy `G*` crosswalk), milestones M1–M7 + MF + MU, acceptance, committed-groundwork deviations, Airtable and IFET asks, operating rules |
| `labos-airtable/evidence/design-closure-2026-09-06.md` | Register/contract consistency checks and verified Notion updates at design closure |
| `labos-airtable/evidence/contract-implementation-audit-2026-09-07.md` | Read-only reconciliation of both PATs/bases, the public link, live management migration state and both codebases. Reopens the v0.4 lifecycle/envelope deviation with exact code evidence |
| `labos-airtable/evidence/write-contract-v0.3-superseded-2026-09-06.md` | The pre-closure v0.3 spec. Old `labos-airtable/contract/write-contract-v0.3.md` links resolve here |
| `labos-airtable/evidence/business-io-reconciliation-2026-09-08/` | **64 rows**: every business input and output for all five test types, traced Airtable field → local storage → source or calculation → outbound field and phase. Includes the requirements the 17 additions do not cover. Tallies the gaps and the six unmet measurements, and says what each needs |
| `labos-airtable/evidence/live-write-proof-2026-09-08/` | **The wire.** Stage 3 (15/15) — upsert merges on `LabOS Attempt ID`, blanks refused, no options invented. Stage 4 (5/5) — all five test types, three phases, one row each. Stage 5 (18/18) — the whole pipeline through the **real** worker and sender, plus retry, retest and the withheld measurements read back absent |
| `labos-airtable/evidence/live-probe-findings-2026-08-23.md` | First live read of both bases: schema held, six items closed and six opened, the extraction defect (§5.2), and §8 — the message wording, stamped *Sent* |
| `labos-airtable/evidence/reference-row-reconciliation-2026-08-28.md` | Our envelope vs. their own sample row `recxZWiVa5Wuy0ZV6` — the `Inches`/`in` and JSON-shape divergences |
| `labos-airtable/evidence/labos-real-data-types-2026-08-31.md` | The real types behind the read-side spec: 14+ stages derived from the design-pressure pair, `60 × 0.15 = 9` proving the shift arithmetically, deflection as three numbers per gauge |
| **`labos-airtable/evidence/firmware-production-runtime-contract-2026-08-31.md`** | **What the rigs actually do.** Management owns 100% of derivation; the firmware→Management payload is `deflections[]` and nothing else; **`recovery` is the 60 s config constant, not a measurement**; deflections are raw IO-Link counts mislabelled as inches; **nothing writes `TestResult.result`**; cyclic is open-loop and static pressure is an operator slider |
| `labos-airtable/evidence/firmware-production-probe-2026-08-31.txt` · `probe-real-data-2026-08-31.sql` | Command and SELECT-only logs for the two audits above, including what was deliberately **not** run |
| `labos-airtable/evidence/p1-schema-and-migration-mechanism-2026-08-23.md` | The attempt schema, and the discovery that migrations were gitignored, bind-mounted from the node and autogenerated at every container boot |
| **`labos-airtable/correspondence/five-test-requirements-approval-2026-09-08.md`** | 🖊️ **What each of the five tests requires and produces — the project owner's approval document.** One page per test, five answers requested. **Generated** by `app/airtable/test_requirements_doc.py` from the calculators, the importer's routing and the two CSVs — regenerate, never edit; `check_register.py` check 7 fails when it is stale. **NOT SENT.** TA5a, and it gates TA5b |
| **`labos-airtable/correspondence/testing-base-change-document-2026-09-08.md`** | **What we changed in the Testing Base and why, plus answers to their three clarifications.** 142 → 159, +17. Preflighted clean against both live bases 2026-09-08. **NOT SENT — held until the approval above comes back** (decided 2026-09-08). TA5b |
| `labos-airtable/correspondence/po-update-and-test-node-request-2026-09-08.md` | The product owner update: WhatsApp message plus the confirmation sheet for the three new tests, and the test-node ask. **NOT SENT** |
| **`labos-airtable/correspondence/airtable-team-questions-2026-09-06.md`** | Planned-change notice: the Testing Base additions, ownership, validation and the later actual-change document. **NOT SENT** |
| `labos-airtable/correspondence/airtable-team-questions-2026-08-31.md` | Historical answers and the original typed-field analysis. Superseded by the September 6 notice |
| `labos-airtable/correspondence/sent/2026-08-28-…-verification-report.docx` | 📨 **The artifact the Airtable team holds.** Five asks with a P0/P1/P2 table — do not edit |
| `labos-airtable/correspondence/v2-guide-reconciliation-2026-08-22.md` | Delta against their *API Integration Guide v2*, plus §5, the correspondence record |
| `labos-airtable/correspondence/team-doc-review-2026-07-29.md` | Review of their **v1** schema doc, and §7, the message sent 2026-07-29 |
| `labos-airtable/correspondence/verification-report-2026-07-29.md` | The ownership boundary and proposed HTTP requests. Stages 1–2 executed 2026-08-23; **its stage 3 payload is retired** |
| `labos-airtable/runbooks/p0-p1-deploy-2026-08-28.md` | The `management` deploy. **§2 decides whether the deploy can happen that day at all** |
| `labos-airtable/schema/baseline-2026-09-05/` | Pre-change baseline, both bases, read-only. Diffing it against 2026-08-23 is what found that they shipped all five `Test Type` options, `dateTime` `Test Date` and `Correction Reason`. Record CSVs are deliberately **absent** — both repos are public and `IFET Projects` carries customer emails and invoice amounts |
| `labos-airtable/schema/schema-{testing,production}-2026-08-23.json` | Field-ID snapshots for drift detection at deploy |
| `operations/branch-reconcile-plan-2026-07-24.md` | Repo ↔ production reconcile, node baselines, and **the git guardrails for a live node** |
| `operations/ssh-session-record-2026-08-23.md` | The 2026-08-23 `management` session — every command, what it returned, what was not touched. All read-only |
| `hardware/README.md` | Modbus RTU, Delta C2000 Plus VFD over serial and TCP, valve pin maps. VFD address is **12** |
| `hardware/system1-*.md` | system-1 bring-up and sensor 4/5 addition records |
| `ifet-management/deployment/SECRETS.md` | Where every credential lives, the secret-hygiene guard, the gated migration runbook |
| `ifet-management/src/management_service/tests/stage3_live_write.py` | Prior-contract verification script. Retain the production refusal; **adapt to v0.4 before acceptance** |

---

---

## 3. Chronological view — what happened, in order

**The tree is filed by role (§2), not by date, and it stays that way.** A folder tells you how much weight a
document carries; a date does not. This section is the *view* that reads as a history, so nobody has to
choose between the two.

Every dated artifact is listed once, newest first. Where a date established something that still binds, it
says so — those are the entries worth reading if you are picking this up cold.

| Date | What happened | Artifacts |
|---|---|---|
| **2026-09-08** | **Three Impact requirement fields applied** (156 → 159). **Pre-fill reinstated, narrowly: LabOS reads the typed fields and never parses `Value`.** The change document written — it also answers the Airtable team's three clarifications — plus the product-owner update. Both **UNSENT**. Manual test capture built: migration, 18 routes, OpenAPI handover | `evidence/testing-base-changes-2026-09-08/` · `evidence/testing-base-before-after-2026-09-08.csv` · `correspondence/testing-base-change-document-2026-09-08.md` · `correspondence/po-update-and-test-node-request-2026-09-08.md` |
| **2026-09-07** | Two independent passes found the same defects. The five-type validation **failed first** — `Test Result = Pending` refused at create, `Test Date` carrying the start instant, an upload gating a measured result. The audit found the phase model missing entirely | `evidence/schema-validation-five-types-2026-09-07.md` · `evidence/contract-implementation-audit-2026-09-07.md` |
| **2026-09-06** | **Design closed at v0.4.** Decision **A9** — LabOS standalone, Airtable is management's mirror. **14 fields applied** to the Testing Base (142 → 156); production untouched | `evidence/design-closure-2026-09-06.md` · `evidence/testing-base-changes-2026-09-06/` · `evidence/write-contract-v0.3-superseded-2026-09-06.md` · `correspondence/airtable-team-questions-2026-09-06.md` |
| **2026-09-05** | Pre-change baseline of **both** bases. Diffing it found they had shipped all five `Test Type` options and `dateTime` `Test Date` without telling us — **which is why the baseline is diffed, not trusted** | `schema/baseline-2026-09-05/` |
| **2026-08-31** | **What the rigs actually do.** Management owns 100% of derivation; the firmware→Management payload is `deflections[]` and nothing else; `recovery` is a config constant, not a measurement; **nothing writes `TestResult.result`** | `evidence/firmware-production-runtime-contract-2026-08-31.md` · `evidence/labos-real-data-types-2026-08-31.md` · `correspondence/airtable-team-questions-2026-08-31.md` |
| **2026-08-28** | Verification report **sent** — the artifact they hold. Their sample row reconciled against our envelope, exposing the `Inches`/`in` divergence. Deploy runbook written | `correspondence/sent/2026-08-28-…-verification-report.docx` · `evidence/reference-row-reconciliation-2026-08-28.md` · `runbooks/p0-p1-deploy-2026-08-28.md` |
| **2026-08-23** | First live read of both bases. Six items closed, six opened, and **the extraction defect found**. Separately: migrations were gitignored, bind-mounted from the node and autogenerated at every container boot | `evidence/live-probe-findings-2026-08-23.md` · `evidence/p1-schema-and-migration-mechanism-2026-08-23.md` · `operations/ssh-session-record-2026-08-23.md` |
| **2026-08-22** | Delta against their *API Integration Guide v2* | `correspondence/v2-guide-reconciliation-2026-08-22.md` |
| **2026-07-29** | Review of their **v1** schema doc; the ownership boundary and proposed HTTP requests | `correspondence/team-doc-review-2026-07-29.md` · `correspondence/verification-report-2026-07-29.md` |
| **2026-07-24** | Repo ↔ production reconciled, integration branches cut, and **the git guardrails for a live node** written | `operations/branch-reconcile-plan-2026-07-24.md` |
| **2026-07-08** | system-1 sensors 4 and 5 added | `hardware/system1-sensor4-5-addition-2026-07-08.md` |
| **2026-07-07** | system-1 bring-up. **VFD Modbus address** — and note it is **per-rig**: system-1 is `12`, system-2 is `5` | `hardware/system1-sensor-vfd-debug-2026-07-07.md` |

**Two documents are deliberately absent from this table**, because they are not point-in-time:
`contract/write-contract-v0.4.md` and `status/delivery-plan.md`. Both are **living and edited in place**, so
their history is in `git log`, not in a filename. That is the whole reason the tree is filed by role — a
dated status file forks the moment someone writes a second one.

To see how either changed on a given date: `git log --follow -p -- <path>`.

## 4. External references

### Airtable

| | | |
|---|---|---|
| Testing base | `app4oXS3Kd5IKWgJ7` | Where LabOS builds. **Empty at the September 5 baseline** — re-read before fixture setup |
| Production base | `app0OCunbmuXl7Hc9` | Holds sample job `IFET-26-0066` and their reference row `recxZWiVa5Wuy0ZV6` |
| Read tables | `tblLYcRC7q6Srjfk3` `tblcrGv0WJn6FTTGO` `tblutO1Q8TNC4BLk0` `tblqpvuJlSdkeS9PS` | Projects · Mock-Ups/Specimens · Tests Protocols · Protocol Sections |
| Write target | `tblnc9SsbXU0C0FWh` | `LabOS Raw Data Table` — **the only runtime write surface** |
| Production dashboard | [interface page](https://airtable.com/app0OCunbmuXl7Hc9/pagGRZZBAH691m3x5) | Human-facing; interfaces are not exposed by the Meta API |

### Notion — [LabOS hub](https://app.notion.com/p/3a357bad43d5818cb726d24c5e803c69)

Every Notion page is a **view**. Its source is the contract or the delivery plan, named in §1 above.

| Page | Audience |
|---|---|
| [*📌 Project Status & Revised Timeline*](https://app.notion.com/p/3ca57bad43d581e5b28ece91494a45a7) | **management — the page the PM reads** |
| [*Airtable Schema Reference / Field Mapping*](https://app.notion.com/p/3a357bad43d581c68ea1c85411429cac) | cross-team |
| [*Internal Engineering Plan*](https://app.notion.com/p/3a657bad43d581fa9778e5c361abd190) | private |
| [*5-Week Integration Plan*](https://app.notion.com/p/3a657bad43d581e59490f53a8eeedbf6) | cross-team — dates superseded |
| *Delivery & Progress Tracker* (Epic IFET-32) | cross-team — live board |
| *Verification Report* · *Contract v0.1* · *Readiness Evaluation* · *Adaptation Plan* · *Branch Reconcile Record* | internal — historical, all bannered |

**⚠️ Outstanding:** the Notion views still point at the retired per-date status pages. They need repointing at
`status/delivery-plan.md`, and *Delivery Status* / *Revised Roadmap* should be merged the way the repo just
was — the plan is now one document, so they are one page.
