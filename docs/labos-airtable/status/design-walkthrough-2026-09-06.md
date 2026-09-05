# LabOS × Airtable — How We Reached the Design

**Notion document:** [Private draft](https://app.notion.com/p/3d257bad43d5810aa7a9c5bb68eed6ef) · **Role:** reader’s summary; view of contract v0.4.

**Prepared by Abdelrahman · 6 September 2026 · Reading time: about 5 minutes**
> **The design is closed; implementation remains incomplete and paused.** We reached contract v0.4 by checking the existing lab, comparing both Airtable schemas, resolving eight design decisions, then auditing the existing sync code. No integration deployment has occurred.

## 1. Purpose and scope
Connect assigned work to trustworthy test results while allowing LabOS to keep saving locally during Airtable outages.

| System | Responsibility |
| --- | --- |
| HubSpot | Approved commercial scope and proposal information. |
| Airtable | Project → specimen → protocol → section; assigned requirements and operational dashboards. |
| LabOS | Procedures, equipment control, local execution records, operator review and original evidence. |
The initial backend scope covers **Static Load, Cycles, Impact, Forced Entry and ANSI Z97.1**. UI work and water integration are deferred. Airtable never controls equipment.

## 2. Steps we took to reach the design
1. **Established ownership and checked the existing system.** We used the team’s integration brief, repository index and recorded production reads. This separated business operations from lab execution and avoided treating an old repository branch as production truth. **Evidence: E2, E3; architecture hub below.**
2. **Compared the proposed fields with both Airtable bases.** The August 23 probe exposed schema gaps. September 5 snapshots showed progress: both bases now had all five Test Type options, datetime Test Date and Correction Reason. We closed those gaps instead of continuing to request delivered fields. **Evidence: E1.**
3. **Traced requirements through the real procedures.** The August 31 investigation showed Management derives six static and eight cyclic stages from directional pressures. A recorded proposal comparison found 60 PSF represented as 9 in Airtable; the extractor could produce plausible but incorrect values. We chose independent positive inward/outward fields, explicit units and source verification before execution. **Evidence: E2, E3.**
4. **Checked whether the promised results actually existed.** The firmware callback supplied deflection data, without achieved pressure, timestamps or verdicts. Deflection scaling was unvalidated; “recovery” included a configuration constant. We chose to omit unreliable quantities and make review explicit in LabOS. **Evidence: E2.**
5. **Resolved the team’s questions and closed A1–A8.** Testing Base field setup was already authorized. We settled programme-level attempts, typed requirements, immutable corrections, measurement omissions, verification rules, API vocabulary and deferred scope. Test Date means completion; separate UTC start/end fields preserve both instants. The outgoing draft became an **unsent change notice**. **Evidence: E4, E5.**
6. **Audited the design against existing code.** The outbox had sequence-allocation races, unsafe competing claims, batch leases, no stale-owner protection and incomplete status reporting. These are latent defects in unwired code, not observed production data loss. The plan now requires PostgreSQL concurrency tests first and separately tracks measurement work. **Evidence: E6, E7.**

## 3. How the designed workflow operates
**Requirements in → execute locally → review → deliver results in order.**

1. **Fetch and select.** A background service reads the four hierarchy tables into a persistent local cache, normally every 60 seconds with a configurable interval. The picker reads that cache; Refresh requests a background update.
2. **Verify and start.** Import by permanent record IDs. Check supported requirement codes and applicability; independently verify actual execution values against the source proposal. Freeze requirements, procedure version and verification facts for the run.
3. **Execute and save.** One programme run has one Attempt ID; stages or impact shots are children. Save the run and its queued sync entry in the same database transaction. Airtable availability is not a prerequisite to saving.
4. **Finish and review.** Freeze execution evidence at completion/abort. The result stays Pending until first review. Physical retesting gets a new attempt; correcting a result also creates a new linked row and preserves the original.
5. **Synchronize.** One separate service uses the existing PostgreSQL database and writes only the raw-results table. Deliver start, finish and review updates in order for each attempt; unresolved writes cannot be overtaken. Airtable automation updates operational views.
6. **Show status and evidence.** Report Synced, Pending, Sync Failed or Retry Required from local state, including photo backlog. Keep original photographs locally and upload previews; export report links only after access is verified.

**Measurement rule:** configured targets never become “achieved” measurements. Unavailable rig pressure and uncalibrated deflection stay omitted; missing evidence cannot establish a passing certification. Forced Entry and ANSI use Test Type + Test Result for filtering, with detail in JSON. **Evidence: E4, E7.**

## 4. What exists today
| State | What it means |
| --- | --- |
| Decided | Contract v0.4; all eight decisions; 66 mapping rows; 14 planned Airtable field additions: eight requirements and six results. |
| Built groundwork | Existing client, earlier attempt/migration work and an isolated outbox. These predate full v0.4 compliance and do not establish a working programme/run integration. |
| Verified | Saved schema snapshots, recorded production investigations, register consistency and documentation closure. The 23 outbox tests use SQLite; they do not prove PostgreSQL concurrency. |
| Still outstanding | Testing Base additions/fixtures, programme/run migrations and APIs, hardened sync, attachment delivery, automation acceptance and production cutover. |
**Design decided, field present, code built, test passed and deployed are separate states.** No new schema changes, runtime fixes or deployment were performed to prepare this document. The September 6 notice remains unsent. **Evidence: E1, E5–E7.**

## 5. Delivery procedure and acceptance
| Step | Completion evidence |
| --- | --- |
| M1 — Testing Base setup | Capture before/after schema and field IDs; create linked synthetic fixtures, including asymmetric pressures and blank/unsupported examples. |
| M2 — PostgreSQL harness, then first complete flow | Test concurrent saves, two competing workers, slow/batched sends and stale owners. Then demonstrate import → run → finish → worker restart → one Testing Base attempt. |
| M3 — Remaining backend workflows | All five types, first review, immutable corrections, photo delivery and accurate sync status pass acceptance checks. |
| M4 — Actual-change document | Record applied versus outstanding changes, examples, validation, migration and rollback procedures. |
| M5 — Coordinated production cutover | Verify automation behavior, rehearse migrations, re-read the live migration head and agree an owner/window before deployment. |
| M6 / M7 — Measurement work | LabOS owns deflection calibration and achieved-pressure acquisition. Schedule against controlled hardware access; omissions remain until validated. |
M2 is one package: fixing sequence allocation alone leaves delivery ordering unsafe. Tests must prove that a late remote write cannot undo a reviewed result; rejecting only a stale worker’s local database update is insufficient.
M6/M7 can proceed separately and do not block the initial release with omissions. Hardware availability remains their scheduling dependency; no firm date is established. Local database testing does not wait for the offline test rig. The earlier October 9 pilot target has not been revalidated. **Evidence: E7.**

## 6. Evidence and related records
The attached packet contains dated schema extracts, production-investigation excerpts, the full v0.4 contract, register, closure checks, reviewed source code and amended implementation plan. **E1–E7 above refer to its numbered sections.** These are saved sources, not a fresh live-system audit.
[Open the Notion walkthrough and its attached evidence packet](https://app.notion.com/p/3d257bad43d5810aa7a9c5bb68eed6ef).

- **Architecture and responsibilities:** [Notion page](https://app.notion.com/p/3a357bad43d5818cb726d24c5e803c69).
- **Current field mapping:** [Notion page](https://app.notion.com/p/3a357bad43d581c68ea1c85411429cac).
- **Owner-facing status:** [Notion page](https://app.notion.com/p/3ca57bad43d581e5b28ece91494a45a7).

This document is a reader’s summary. Repository authority remains `docs/labos-airtable/contract/write-contract-v0.4.md`; procedures and acceptance are in `design/integration-design-2026-09-05.md`. Source snapshots: firmware `93abb60`, management `d61f6f5`.


