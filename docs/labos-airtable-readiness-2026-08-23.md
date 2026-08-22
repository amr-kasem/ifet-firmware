# LabOS ↔ Airtable Integration — Readiness Report

**As of:** 2026-08-23 · **Epic:** IFET-32 · **Author:** Abdelrahman
**Contract:** `v0.3 DRAFT` · **Week:** 1 of 5, closing

> **What this document is.** One readable place to see where the integration stands, what has been built, what
> has been proven against the live system, and what is genuinely left. It is a **view** — the authoritative
> sources are named in each section, and `INDEX.md` §1 says which document owns which subject. Where this
> summary and an authoritative document disagree, the authoritative one wins and this file is the bug.

---

## The bottom line

LabOS's side of the integration is **built and, as of today, verified against the real Airtable bases**. The
external dependency that blocked everything for a month — the access token — arrived on 2026-08-23, and the
first live probe closed six open questions in a single run and answered the one that had been the critical
path since July.

Two things now stand between here and a working integration, and **neither is LabOS work**:

1. **The requirement data in Airtable does not match the proposals it was extracted from.** This is a safety
   issue, not a data-quality annoyance — see [The one serious risk](#the-one-serious-risk).
2. **Four of the five test types cannot be written back**, because the Airtable field that receives them
   offers only one option.

Everything LabOS can do without the Airtable team is done, queued, or deliberately gated. A joint testing
session is booked for **Monday 2026-08-25**, where both items above are the agenda.

---

## Readiness at a glance

| Area | State | Notes |
|---|---|---|
| **Airtable API client** | 🟢 Built · verified live | Write allowlist, retry classes, rate limiting. Talked to both bases today. |
| **Schema probe** | 🟢 Built · run against both bases | Read-only. Closed six contract items in one run. |
| **Payload envelope builder** | 🟢 Built · corrected against live schema | Now sends the base's own option spellings. |
| **Offline test suite** | 🟢 98 tests passing | stdlib only, no network, no token needed. |
| **Field-ID snapshots** | 🟢 Captured, both bases | Committed. Makes an Airtable rename a non-event. |
| **Secret handling** | 🟢 Done | Tokens in a gitignored `.env`; never in git, docs, or browser-served config. |
| **Reading requirements (W3)** | 🟡 Unblocked to build · **not safe to trust** | Structure understood. The *data* is wrong — see below. |
| **Writing results back (W4)** | 🟡 Partially blocked | Only static-load results can be written today. |
| **Live write round-trip** | ⚪ Not yet run | Ready to go. Needs the Airtable team's go-ahead. |
| **Corrections vs. retests** | 🔴 Blocked | Two fields still absent; the builder refuses to fake it. |
| **Firmware P3 (rig capture)** | 🟡 Write + unit-test only | **No test rig** — the non-production node has been offline since ~2026-07-24. |
| **Production deployment** | ⚪ Deliberately gated | Nothing deployed. Nothing should be yet — see [Deployment posture](#deployment-posture). |

🟢 done · 🟡 partial or conditional · 🔴 blocked · ⚪ deliberately not started

---

## What has been built

All of it lives on integration branches — `feature/labos-airtable` in `ifet-management`,
`feature/labos-firmware-p3` in `ifet-firmware` — and **none of it is deployed**.

| Component | What it does | Why it is built the way it is |
|---|---|---|
| `app/airtable/client.py` | REST client — upserts, pagination, schema reads | The **write allowlist is enforced before the socket opens.** Airtable tokens are scoped per *base*, not per table, so the token we hold can write the four tables the Airtable team marked read-only. Nothing on their side prevents it; this client is the enforcement. |
| `app/airtable/errors.py` | Retry taxonomy | Retry behaviour is decided by the *error type*, not by whoever calls it — so a future sync worker cannot get it wrong by omission. |
| `app/airtable/contract.py` | The written contract, as data | Lets the schema diff and payload validation be mechanical instead of by eye. The prose contract stays authoritative. |
| `app/airtable/envelope.py` | Builds the outgoing record | Translates LabOS's vocabulary to Airtable's at the wire boundary — field names *and*, since today, option values. |
| `app/airtable/probe.py` | Read-only schema probe | Issues `GET`s and nothing else, so it is safe to point at production. One call answers questions that would otherwise cost an email round-trip each. |
| `tests/` | 98 offline tests | No network, no token. The fixtures now mirror the real base, including its quirks. |

**Two constraints were chosen deliberately, and both paid off today:**

- **Standard library only.** `report-api`'s `app/` directory is bind-mounted into the running container, so
  pure-stdlib code can be deployed without rebuilding the image — and on this project a production image
  rebuild is a scheduled event, not a convenience. Adding a dependency would have made the probe undeployable
  without one.
- **The probe reads and never writes.** That is why it could be pointed at the live production base today
  without a risk conversation.

---

## What today's probe actually proved

Read-only, both bases, nothing written to either.

**Six open questions closed with evidence rather than correspondence:**

| Question | Answer |
|---|---|
| Is `Photos` an attachment field? | No — it's a URL field, which is what our contract needs |
| Are the four ID fields plain text or record links? | Plain text — exactly as LabOS proposed |
| Is `Impact Result` a fixed list or free text? | Free text |
| Has the access token been delivered? | Yes, both bases |
| Do the blank/null rules hold against the live schema? | Yes |
| Is the result option `Pass` or `Passed`? | **`Passed` — their guide was right and our contract was wrong** |

That last row matters beyond the detail. A verification pass that only ever finds the *other* side wrong isn't
being honest; this one corrected us, and our code changed rather than our expectations.

**Also confirmed:** every table ID we had transcribed from their PDF is real and correctly named, and all 28
promised fields exist. The testing base turns out to be a structural *clone* of production — identical table
and field IDs — which is a quiet win: one schema snapshot binds both environments, so a cutover cannot
silently re-point at different fields.

**And the question that had blocked Week 3 since 2026-07-23 is answered.** Test requirements are stored as
one Airtable record per requirement line — a `Section Name` like `DP (+) (PSF)` paired with a `Value`. That is
neither of the two shapes either side had proposed, but it is addressable, so **the requirements-reading work
can proceed.**

---

## The one serious risk

**Airtable's requirement values do not match the proposals they came from.**

Checking their populated sample job against the source PDF, the values are shifted one column: where the
proposal has a blank cell, the extractor skips it instead of holding its position, so everything after it
slides left.

| Requirement | Proposal PDF | Airtable |
|---|---|---|
| **DP (+) (PSF)** | **+60/60** | **9** |
| Water (PSF) | 9 | *(blank)* |

Those are the numbers LabOS reads **to drive the rig**. Taken at face value, that record runs a structural
test at roughly a seventh of the specified design pressure and — if the specimen holds — records it as
*Passed*. A false pass on a hurricane-rated door, produced by every component working exactly as designed.

**LabOS cannot detect this.** Every shifted value is individually plausible; `9` is a legal design pressure.
No plausibility check on our side is sufficient, because only the original proposal proves it wrong.

> ### Standing rule until the Airtable team fixes their extraction
> **Nothing reads requirements from Airtable to drive a live test.** The requirements work may be *built*
> against this structure; it must not be *trusted* with a rig.

This is recorded in three places so it cannot quietly lapse: this report, contract §10.19, and the internal
plan's gap list.

---

## What is blocking, and on whom

| # | Blocker | Owner | What it gates |
|---|---|---|---|
| 1 | Requirement values shifted by one column | Airtable team | Any live test driven from Airtable — i.e. the point of Week 3 |
| 2 | `Test Type` offers only `Static Load` | Airtable team | Writing back anything but static load — Week 4 |
| 3 | `Corrects Attempt ID` + `Correction Reason` absent | Airtable team | Telling a corrected result from a genuine retest |
| 4 | Typed `Required Value` / `Required Unit` | Airtable team | Removes a parsing hazard from the read path |
| 5 | Approval to run one test write | Airtable team | The final verification step |
| 6 | `Test Date` cannot hold a time | Airtable team | Test duration being reportable at all |
| 7 | **No non-production rig** — test node offline since ~2026-07-24 | IFET / manager | Firmware P3 can be written and unit-tested, but not run |

Items 1–6 are the Monday agenda. Item 7 is the one long-running dependency that isn't the Airtable team's.

**Nothing on this list is LabOS work.** That is the honest summary of where Week 1 ends.

---

## Where the five-week plan actually stands

| Week | Milestone | State |
|---|---|---|
| **W1** | Foundations + contract lock | 🟢 **Complete on the LabOS side.** Secret store built, client/probe/envelope built and now live-verified, schema snapshots captured. Contract lock still needs the Airtable team. |
| **W2** | Schema & identity | ⚪ Ready to start — needs no field names, so it is not externally blocked |
| **W3** | Requirements-IN | 🟡 Unblocked *to build* today; **not safe to trust** until blocker 1 clears |
| **W4** | Bidirectional sync | 🟡 Buildable; only static-load results can be written until blocker 2 clears |
| **W5** | Manual screens, hardening, cutover | ⚪ Unchanged |

The week counter has not moved because the *external* gate stayed shut, not because LabOS work stalled — the
build ran ahead of the token deliberately, which is why six contract items closed within an hour of it
arriving.

**If ratification slips further**, the planned mitigation stands: swap W3 and W4, building the sync plumbing
against the agreed envelope first and binding the read side when the data is trustworthy.

---

## Deployment posture

**Nothing has been deployed, and nothing should be yet.**

- The Airtable code is on an integration branch, not on the branch production runs.
- Both safety flags (`AIRTABLE_SYNC_ENABLED`, `AIRTABLE_ALLOW_PRODUCTION_WRITE`) are off, so even if it were
  deployed it would make no Airtable calls.
- The contract is still `v0.3 DRAFT` with the write path unratified.
- There is no non-production rig to rehearse on (blocker 7), and rehearsal off-production is a precondition.

The stdlib-only constraint means that when a deploy *is* right, it needs no image rebuild. That property is
already banked and does not expire, so waiting costs nothing.

The one deployment actually queued — the P0/Ref 42 secret store — is built and rehearsed off-node and remains
**gated by decision**, not by readiness.

---

## What happens next

**Monday 2026-08-25, with the Airtable team** — agenda and the full message:
`labos-airtable-live-probe-findings-2026-08-23.md` §7 and §8.

1. Walk through the extraction defect; agree a fix and find out how many jobs are affected.
2. Get the four missing `Test Type` options added.
3. Get approval for the single test write — the last verification step before Week 2.
4. Re-raise the correction fields and the typed requirement fields.

**Immediately afterwards, on the LabOS side:**

- Run verification stage 3 (write, then update the same record, confirming no duplicate is created).
- Ratify the contract to `v1.0` once the blocking items close.
- Begin W2 schema and identity work, which needs nothing external.
- Rotate both tokens once acceptance testing is done — they arrived by email, so replacing them is routine
  hygiene rather than a response to any misuse.

---

## Where to look for detail

| For | Read |
|---|---|
| Every document, and which one is authoritative | `INDEX.md` |
| The spec both teams build against | `labos-airtable-write-contract-v0.3.md` |
| Open items, canonical list (22 of them) | `labos-airtable-write-contract-v0.3.md` §10 |
| What the live bases actually contain, and today's evidence | `labos-airtable-live-probe-findings-2026-08-23.md` |
| The message going to the Airtable team | `labos-airtable-live-probe-findings-2026-08-23.md` §8 |
| Internal plan, gaps, week sequencing | `labos-airtable-integration-internal-plan-2026-07-23.md` |
| Correspondence history | `labos-airtable-v2-guide-reconciliation-2026-08-22.md` §5, and the two 2026-07-29 records |
