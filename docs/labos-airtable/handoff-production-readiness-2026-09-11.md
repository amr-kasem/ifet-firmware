# Handoff — LabOS ↔ Airtable production readiness, 2026-09-11

> ## ⚠️ SUPERSEDED the same day — §3 and §4 are done
>
> This was written before the TA6 cutover and its §4 step list has been executed in full. **TA6 is
> CLOSED / VERIFIED IN TESTING**: both fields applied to the Testing Base (`Forced Entry Result`
> `fldAHuPzZHZEj0Cjt`, `ANSI Result` `fldmCKJV95N9uL7xt`), Testing **162 → 164**, production untouched at
> **142**, and the real-wire probe green at **97/97** in one clean run. Do **not** re-run §4.
>
> **Start instead at:**
>
> | | |
> |---|---|
> | Where the work stands | `status/delivery-plan.md` — and its **DG14**, which is the one finding of the readiness pass that changed a decision |
> | How this is deployed | `runbooks/production-deploy-2026-09-11.md` |
> | What the Airtable team must do | `runbooks/production-airtable-promotion-2026-09-11.md` · `correspondence/airtable-team-actions-2026-09-11.md` |
> | What is still true of the old findings | `evidence/historical-findings-reassessment-2026-09-11.md` |
>
> §2 (the TA7 contract), §5 (production boundaries), §8 (the optimization-loop guard) and §9 (paths) are
> **still current**. §1's commit list and §6's gate list are historical.

**For a fresh session.** Derived from the repository, git history and committed evidence as of this date.
Where this document and the repository disagree, **the repository and the live bases win** — see §10.

---

## 1. Repository state

### `ifet-firmware` (this repo — docs, contracts, evidence)

| | |
|---|---|
| Branch | `feature/labos-firmware-p3` |
| HEAD | **the commit that adds this file** — a commit cannot name its own hash; run `git log -1` |
| Push state | **Local only** — 11 commits ahead of `origin/feature/labos-firmware-p3`, 0 behind. **Nothing published.** |
| Working tree | **Clean** |

Recent commits, oldest first:

```
57eff0f  docs: the last two claims the review found, closed        (pre-TA7)
ab739d0  docs: the product owner's answers, and the Impact remap they force
fab69b7  docs: supersede the production change spec before somebody applies it
b0f3736  docs: notice to the UI developer that the Impact contract is changing
f226bc0  docs: pre-TA7 baseline of both live bases, read-only
6946fb7  docs: prepare Impact Airtable contract cutover
b61cc7c  docs: finalize Impact Airtable schema cutover
9587f8d  chore: untrack a LibreOffice lock file and ignore the pattern
d2a2cc3  test: TA7 live-probe evidence from the Testing Base
43cb100  docs: mark TA7 closed, and record the deployment gate that is not
fcb97a7  docs: the change document stops contradicting the product owner   (TA6)
<HEAD>   docs: handoff for a fresh session — production readiness          (this file)
```

### `ifet-management` (sibling checkout — the code)

| | |
|---|---|
| Branch | `feature/labos-airtable` |
| HEAD | **`c47c246`** |
| Push state | **Local only** — 8 commits ahead of `origin/feature/labos-airtable`, 0 behind |
| Working tree | **Clean** |
| Alembic head | **`a4f18c2d3b90`** (`a4f18c2d3b90_impact_classification.py`), single head, computed from the revision graph |

```
153a1db  feat(airtable): apply Impact Number to the Testing Base — step 3   (pre-TA7)
a044e39  fix(airtable): publish Impact Number — the column had no writer
9fb4a23  docs(airtable): the approval document says built-not-deployed for Impact
fe57709  fix: refuse an unsupported static programme instead of running Full
260c029  docs: mark the Impact contract change in the UI API document
a148545  feat: model impact family and freeze Airtable impact ownership       (TA7a)
03a5a74  feat: add impact configuration lifecycle and completion gates        (TA7a)
d649d84  feat: prepare Impact Airtable contract cutover                       (TA7b)
49c3cce  feat: finalize Impact Airtable schema cutover                        (TA7b)
fd4dfae  test: verify Impact Airtable contract on the live Testing Base       (probe)
c47c246  feat: prepare the per-standard result fields for the Testing Base    (TA6)
```

**The alembic head on the live `management` node is NOT this.** Nothing is deployed; check
`SELECT * FROM alembic_version;` on the node before any schema work, per `docs/INDEX.md`.

---

## 2. TA7 — **CLOSED / VERIFIED IN TESTING. Production deployment pending.**

### The agreed Impact contract — settled, do not reopen

- **`Requirement Code` owns the family for an Airtable-bound test.** `IMPACT_SMI` → `SMI`,
  `IMPACT_LMI` → `LMI`. Frozen once by `importer.bind`; the operator is never offered the choice.
- **The LMI level (D or E) is entered in LabOS.** A LabOS-only test may also set its own family, write-once,
  fixed as soon as any attempt exists — aborted included.
- **`Target Impact Velocity` is LabOS-owned**, operator-entered, ft/s. **Not derived** from the
  classification; no authoritative derivation table exists in this repository or the contract.
- **`Impact Classification` is derived output only** — `SMI` · `LMI Level D` · `LMI Level E`. No column
  holds the string and no API field sets it.
- **Number of Impacts stays Airtable inbound** via `Required Value` + `Requirement Code`. Unchanged.
- **One physical impact = one attempt.** `Impact Number` and `Impact Result` remain outbound, unchanged.
- **`Missile Type`, `Missile Weight`, `Impact Velocity` are withdrawn from the LabOS inbound contract.**
  They remain **physically present in the Testing Base and unread**; never created in production. Removal is
  a coordinated cleanup with the Airtable team, not a code side effect.
- **Impact Location stays LabOS-side evidence** (`shots.area`, JSON only). No Airtable field.
- **Production untouched.**

### Verification

| | |
|---|---|
| Probe result | **64/64 PASS in one authoritative run**, `20260910T223938Z` |
| Probe evidence | `docs/labos-airtable/evidence/ta7-live-probe-2026-09-11/` — read `probe-results-20260910T223938Z.json`; the README says which run counts and why three earlier runs are kept |
| Schema evidence | `docs/labos-airtable/evidence/testing-base-changes-2026-09-11-impact-classification/` |
| Pre-change baseline | `docs/labos-airtable/evidence/pre-ta7-baseline-2026-09-10/` |

Field IDs created in Testing (`LabOS Raw Data Table` `tblnc9SsbXU0C0FWh`):

| Field | ID | Shape |
|---|---|---|
| `Impact Classification` | **`fldMY7DiiuP9kbQbL`** | singleSelect, choices `SMI` · `LMI Level D` · `LMI Level E` |
| `Target Impact Velocity` | **`fldhywP9YpsmoWWT1`** | number, precision 2 |

Withdrawn but still present in Testing: `Missile Type` `fld5Bs0aQXXeVso2y` · `Missile Weight`
`fldmhdhonyyLcx4Ex` · `Impact Velocity` `fldJNfUVyqQEFOVWx`.

**Schema counts at TA7 close: Testing `app4oXS3Kd5IKWgJ7` = 162 · Production `app0OCunbmuXl7Hc9` = 142.**

**Probe records are still in the Testing Base**, tagged `Operator Name = LABOS-PROBE-TA7`, listed in
`ta7-live-probe-2026-09-11/probe-records-inventory.txt`. Cleanup is a separate, explicit, recorded
operation and has **not** been approved yet.

---

## 3. TA6 — **IMPLEMENTED LOCALLY / PENDING_SCHEMA. Not applied to Airtable.**

TA6 exists for one reason: the Testing Base change document told the Airtable team we would add dedicated
result fields *only if they named a report*, and the product owner had already answered on 2026-09-10 that
Forced Entry and ANSI Z97.1 are judged under **different standards** and must be distinguishable. Sending
the document without this would contradict a decision already taken.

### The settled contract — do not re-scope

| | |
|---|---|
| Fields | `Forced Entry Result`, `ANSI Result` — both on `LabOS Raw Data Table` |
| Source | **`test_results.test_result`** — the same value, not a new one |
| Type gating | `Forced Entry` and `ANSI Z97.1`, from `attempt.test_type` |
| Generic `Test Result` | **Unchanged**, still written for all five types, all three phases |
| Lifecycle | **terminal + verdict**, mirroring `Test Result`. Not verdict-only |
| Internal vocabulary | `Pending` · `Pass` · `Fail` · `Inconclusive` |
| Airtable wire vocabulary | `Pending` · `Passed` · `Failed` · `Inconclusive` |
| option_wire | The **same authoritative mapping** as `Test Result` — `Pass→Passed`, `Fail→Failed` |

Rules, all covered by tests:

- FE terminal → `Test Result = Pending` **and** `Forced Entry Result = Pending`; no `ANSI Result`
- FE verdict → both carry the same final result
- ANSI terminal → `Test Result = Pending` **and** `ANSI Result = Pending`; no `Forced Entry Result`
- ANSI verdict → both carry the same final result
- Forced Entry never emits `ANSI Result`; ANSI never emits `Forced Entry Result`
- Static Load / Cycles / Impact emit neither
- The non-applicable field is **omitted, never blank**
- **No new source of truth.**

### Exactly what TA6 changed — **committed, not uncommitted**

`ifet-management` **`c47c246`** (6 files, +192/−13):

| File | Change |
|---|---|
| `app/airtable/contract.py` | Two `Field()`s, `CONDITIONAL, ABSENT, pending_schema=True`, options and `option_wire` copied from `Test Result`; each appended to its own `REQUIRED_BY_TEST_TYPE` entry (enforced on `COMPLETED` only, so an abort is never stranded) |
| `app/airtable/mapping.py` | Two type-gated keys sourced from `attempt.test_result` |
| `app/airtable/apply_schema.py` | Two `RAW_RESULTS` definitions, four choices each in the **wire** spelling |
| `app/airtable/preflight.py` | Both into `PENDING_SCHEMA`; `EXPECTED_CHOICES` entries |
| `tests/test_airtable_mapping.py` | New class `ThePerStandardResultIsGatedByTestType`, 8 tests |
| `tests/test_five_test_types.py` | Terminal/reviewed fixtures carry the dedicated field; pending-set assertion updated |

`app/airtable/envelope.py` is **deliberately untouched** — blank suppression and phase gating already exist.

`ifet-firmware` **`fcb97a7`** (2 files):

| File | Change |
|---|---|
| `contract/field-register.csv` | The two **already-existing** rows flip `OMITTED` → `PENDING_SCHEMA`, `labos_source` set. **No new rows** |
| `correspondence/testing-base-change-document-2026-09-08.md` | The contradicting line struck through and corrected; the two additions documented |

### Current results

| | |
|---|---|
| Test suite (SQLite) | **379 passed**, 14 skipped, 108 subtests. 15 failures, **all pre-existing** and Postgres-dependent (`test_business_acceptance.py`) — identical before TA6 |
| `check_register.py` | **PASS** |
| Real preflight | **Clean.** Reports both as `PENDING`. 22 guarded fields, none in production |
| Schema counts | **Testing 162 · Production 142** — unchanged, TA6 not applied |

### One discovered behaviour the TA6 probe must verify

Because the two fields are `ABSENT` until created, **the envelope carries them through the JSON valve**, not
as columns: an ANSI terminal payload contains `labos_extra.ansi_result: "Pending"` and **no `ANSI Result`
column**. This is correct — nothing is lost while the schema catches up — and it flips to a real column when
the fields are created and become `PRESENT`.

**The live TA6 probe must assert that the value moves out of the JSON valve and into the physical Airtable
column after schema creation.** The current unit test asserts only the invariant that holds in both states.

---

## 4. Exact next action — do not re-scope TA6

1. ~~Verify the current TA6 diff.~~ **Done** — see `c47c246` / `fcb97a7`.
2. ~~Run the strongest practical pre-cutover gates.~~ **Done** — §3 results.
3. ~~Commit the TA6 `PENDING_SCHEMA` preparation atomically (both repos).~~ **Done.**
   **Start here → step 4.**
4. Read-only preflight against Testing **and** Production.
5. `apply_schema` **dry run**.
6. Create exactly `Forced Entry Result` and `ANSI Result`, **Testing only**.
7. Independent Meta API read-back.
8. Capture the real `fld…` IDs.
9. Testing expected **current + 2** (162 → 164); Production **unchanged at 142**.
10. Finalise register / preflight / contract against the real IDs.
11. Regenerate the authoritative artifacts (see §9).
12. PostgreSQL 13 suite.
13. Real preflight.
14. Finalisation commit.
15. Focused real-wire TA6 probe — **extend `tests/ta7_probe_live.py`, do not build a new framework.**
16. Authoritative single-run PASS evidence.
17. Mark TA6 **CLOSED** if green.
18. Continue directly into production readiness.

---

## 5. Production boundaries

**DO NOT:**

- mutate the Production Airtable schema;
- write Production Airtable records;
- deploy Production;
- push branches unless explicitly instructed;
- invent missing business semantics.

Production **may** be read through the approved read-only preflight and verification paths. The production
PAT is read-only and `apply_schema` refuses the production base unconditionally, with no flag that overrides
it — do not add one.

---

## 6. Deployment gates still pending

| Gate | Kind |
|---|---|
| **Open-Impact-attempt check** (`tests/check_open_impact_attempts.py`) against the **actual deployment database** | **Production blocker.** Read-only. Record the output in the deployment evidence **even when the answer is zero**. Never infer or backfill classification/target velocity for historical or open attempts |
| **Migration rehearsal** of `a4f18c2d3b90` against the deployment DB shape | **Deployment-window prerequisite.** Rehearsed on a throwaway Postgres 13 (up, down with populated rows, up again); **not yet rehearsed against a dump of the deployment database** |
| **Production Airtable promotion** of the added fields | **External approval.** `production-change-spec.csv` proposes them; production stays at 142 until the Airtable team acts |
| **Airtable team acknowledgement** of the change document, incl. the three withdrawn fields left in Testing | **External approval** |
| **Cleanup of the TA7 probe records** in Testing | **Backlog** — explicit, recorded, after review |
| Deploy the three manual test types (TB4) | **Deployment-window prerequisite** |

---

## 7. Remaining epic

Currently-known next task names: **TA5b**, **TC5**, **TB4** — plus **TA6** and the TA7 deployment gate.

**Resolve their actual current meaning from `docs/labos-airtable/status/delivery-plan.md`**, which is the
living record, rather than relying on these labels. At the time of writing TA5b was blocked only by TA6, and
TC5 (the operator interface) was the epic's critical path — verify both.

---

## 8. Optimization-loop guard

**Do not reopen a settled decision** unless new evidence proves one of:

- a correctness failure;
- a safety failure;
- a data corruption or loss risk;
- a contract or compatibility violation;
- a security-critical issue;
- a missing required operator workflow;
- a deployment or migration failure;
- an unverifiable acceptance criterion.

**Everything else is backlog.** TA7 in particular is closed; §2 is not a proposal.

---

## 9. Evidence and document paths

| What | Path |
|---|---|
| TA7 live probe evidence | `docs/labos-airtable/evidence/ta7-live-probe-2026-09-11/` |
| Testing Base schema evidence (TA7b) | `docs/labos-airtable/evidence/testing-base-changes-2026-09-11-impact-classification/` |
| Pre-TA7 baseline, both bases | `docs/labos-airtable/evidence/pre-ta7-baseline-2026-09-10/` |
| Field register (authoritative mapping) | `docs/labos-airtable/contract/field-register.csv` |
| Write contract (authoritative spec) | `docs/labos-airtable/contract/write-contract-v0.4.md` |
| Interface schema (generated) | `docs/labos-airtable/contract/interface-schema.csv` |
| Production change spec (generated) | `docs/labos-airtable/evidence/testing-base-changes-2026-09-06/production-change-spec.csv` |
| Testing Base change document (**unsent**) | `docs/labos-airtable/correspondence/testing-base-change-document-2026-09-08.md` |
| Five-test approval document (generated) | `docs/labos-airtable/correspondence/five-test-requirements-approval-2026-09-08.md` |
| Delivery plan / task register | `docs/labos-airtable/status/delivery-plan.md` |
| Document map — read first | `docs/INDEX.md` |
| Deploy runbook | `docs/labos-airtable/runbooks/p0-p1-deploy-2026-08-28.md` |

Code (in `../ifet-management/src/management_service/`): `app/airtable/{contract,mapping,envelope,mirror,
importer,requirements,apply_schema,preflight,check_register}.py`, `tests/ta7_probe_live.py`,
`tests/check_open_impact_attempts.py`.

---

## 10. Bootstrap instructions for the next agent

Before modifying anything:

1. read repository AGENTS/instructions;
2. read this handoff;
3. verify git status and recent history;
4. inspect the referenced evidence rather than trusting this handoff blindly;
5. reconcile any discrepancy in favor of current repository/live evidence;
6. then continue from TA6 without reopening TA7.
