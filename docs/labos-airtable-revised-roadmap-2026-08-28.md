# LabOS ↔ Airtable — revised roadmap and true timeline

**Author:** Abdelrahman · **Date:** 2026-08-28 · **Epic:** IFET-32
**Trigger:** the project manager asked for the true timeline and current position.
**Supersedes the dates** in the 5-week plan. It does **not** supersede its shape — the milestones are unchanged.

---

## 1. Where we actually are

| | |
|---|---|
| Milestones complete | **2 of 5** — W1 foundations, W2 schema & identity. Both verified 2026-08-28 |
| Deployed | **Nothing.** Production runs the July build |
| Original window | 2026-07-23 → **2026-08-27 — closed** |
| Tests | 132 offline, green |
| Blocking dependency | ~~Four asks, unsent~~ — ✅ **sent 2026-08-28** as a formal verification report. Now waiting on their reply |

**Why it is behind, stated plainly.** Weeks 1 and 2 were delivered on the LabOS side. The project then
stopped, waiting on answers that were never actually requested — the message was written and not sent, and
the joint call booked for 2026-08-25 lapsed. That is a LabOS-side failure, not an Airtable-side one; they
have answered every question ever put to them, usually within a day.

**Cleared 2026-08-28.** Both artifacts went out the same day this was written: the verification report to
the Airtable team (`docs/sent/…verification-report.docx`) and the project-status page to IFET management
(`3ca57bad43d581e5b28ece91494a45a7`). From here the critical path runs through *their* response times, and
R1–R3 proceed regardless.

Notion had drifted with it. The task board still showed two completed phases as `To Do` / `Backlog`. That is
reconciled as of today (INDEX §4).

---

## 2. The revised timeline

Target: **pilot go-live Friday 2026-10-09.** Six working weeks from Monday 2026-08-31.

The sequencing change that makes this credible: **W4 is pulled ahead of W3.** Results-out needs nothing
from the Airtable team, and it is the largest and riskiest piece left. Requirements-in cannot be trusted
until the extraction defect clears regardless of when it is built, so building it earlier buys nothing.

| Week | Dates | LabOS delivers | Depends on |
|---|---|---|---|
| **R1** | Mon 31 Aug – Fri 4 Sep | **Deploy P0 + P1 to production** in an agreed window (overdue, and it de-risks everything after it). Begin the durable sync queue | Maintenance window · `startup.sh` + migration ship together |
| **R2** | Mon 7 Sep – Fri 11 Sep | Sync queue + background worker. **Idempotent upsert verified live** against the testing base | Airtable's OK for the single test write |
| **R3** | Mon 14 Sep – Fri 18 Sep | Sync-status UI, retry/failure surfaces. **★ Milestone: results flow back, dark-launched** | — |
| **R4** | Mon 21 Sep – Fri 25 Sep | Requirements-IN: Airtable read service, selection UI (Project → Mock-up → Protocol → Test) | Build: nothing. **Trust: the extractor fix** |
| **R5** | Mon 28 Sep – Fri 2 Oct | Manual entry screens — Impact, Forced Entry, ANSI Z97.1, with photos and report links | `Test Type` options added, else only static load round-trips |
| **R6** | Mon 5 Oct – Fri 9 Oct | Hardening, observability, end-to-end run, contract → **v1.0**, **cutover to a pilot project** | Extractor fixed and re-import confirmed |

### What moves the date, and by how much

| If | Then |
|---|---|
| The extractor fix slips past **Fri 18 Sep** | R4 still builds, but the pilot cannot run from Airtable requirements. Go-live slips week-for-week, **or** goes ahead static-load-only with requirements entered by hand |
| `Test Type` options are not added by **Fri 25 Sep** | R5 delivers screens that cannot write back four of five test types. Go-live becomes static-load-only |
| No maintenance window in R1 | Every later milestone deploys into a bigger, riskier change set. This is the cheapest week to spend |
| The `test` node stays offline | Every rehearsal runs on a throwaway local stack, and the first real exercise of the sync path is on production. This is the largest unmanaged risk in the plan |

---

## 3. Settling the Airtable dependency — concrete

Two tracks run in parallel. Track A is the one that has not been started.

### Track A — the four asks

| # | Ask | Blocks | Target |
|---|---|---|---|
| 0 | ~~Send the message + request a slot~~ | — | ✅ **DONE Fri 28 Aug** |
| 1 | **Fix the proposal extraction.** Blank cells must hold their column. Re-import `IFET-26-0066`; report the blast radius **including jobs already marked tested** | R4 trust · pilot go-live | Fix agreed **Mon 31 Aug** · delivered **Fri 18 Sep** |
| 2 | **Add four `Test Type` options** — `Cycles`, `Impact`, `Forced Entry`, `ANSI Z97.1`. A config change on their side, minutes of work | R5 · four of five test types | **Fri 4 Sep** |
| 3 | **Approve one test write** into the testing base — one record, written then updated. Production base untouched. A one-line reply is enough | R2 | **Wed 2 Sep** |
| 4 | **Add `Corrects Attempt ID` + `Correction Reason`** | trustworthy attempt counts and pass rates | **Fri 11 Sep** |
| 5 | **Add `Required Value` + `Required Unit`** on Protocol Sections, leaving `Value` untouched | robustness of R4 | **Fri 11 Sep** |

Items 2, 3, 4 and 5 are each small on their side. **Item 1 is the only one with real engineering behind
it, and it is the only one that gates go-live.**

### Track B — what proceeds regardless

R1 and R2 need nothing from Airtable except item 3, and item 3 is a one-line reply. If Track A stalls
entirely, R1–R3 still deliver and the integration reaches *dark-launched results-out* on schedule; only
the pilot cutover moves.

---

## 4. ⚠️ The item that is not a schedule item

The proposal extractor puts requirement values in the wrong columns. On the sample job, `DP (+) (PSF)`
reads **9** where the proposal says **+60/60**.

Two consequences that belong to the business, not to engineering:

1. **A rig driven from that value would load a specimen to a seventh of its design pressure**, pass it, and
   record it as passed. LabOS cannot detect it — every shifted value is individually plausible.
2. **It has already reached a completed record.** `SMI (impacts)` on that job is `Passed` / `Completed`
   against a value the proposal does not contain. **Whether previously reported results need reviewing is a
   decision for IFET, not for LabOS** — we can supply the list once Airtable reports the blast radius.

Standing rule until it clears: **no rig is driven from an Airtable requirement value, and no LabOS result
is written against one.**

---

## 5. What is needed from IFET

| Ask | Why | By |
|---|---|---|
| **A maintenance window** for the P0/P1 deploy | Nothing is deployed; the gap grows with every milestone | **R1** |
| **The `test` node back online** | It is the only non-production rig. Without it the sync path is first exercised on production | **R1** |
| **Weight behind ask 1** with the Airtable team | It is a safety item and the only true gate on go-live | **Now** |
| **A decision on reviewing already-reported results** | Quality/business call, not an engineering one | On the blast-radius report |

---

## 6. Reporting cadence — the visibility gap

The trigger for this document was a fair complaint: no visible activity and no Notion updates.

- **Notion status page updated every Friday**, whether or not the news is good.
- **The task board reflects reality on the day**, not at milestone boundaries.
- **Anything that blocks for more than 48 hours gets raised in the chat**, rather than waiting for a call.

The failure this time was not the work rate. It was that a blocked project stayed silent.
