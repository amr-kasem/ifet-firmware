# LabOS ↔ Airtable — real delivery status

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

**Author:** Abdelrahman · **Date:** 2026-08-28 · **Epic:** IFET-32 · **Contract:** `v0.3 DRAFT`
**Type:** status assessment. A *view* — every claim names the document or the command that backs it.

---

## 0. The one-paragraph verdict

> **Update, later on 2026-08-28 — the blocker below is cleared.** The verification report went to the
> Airtable team and the status page went to IFET management. §5's item 1 is closed; everything downstream
> now waits on *their* reply rather than on us. Sent record:
> `docs/labos-airtable/correspondence/sent/2026-08-28-labos-airtable-live-base-verification-report.docx` · findings §8.
> The rest of this assessment stands as written — it is the position that prompted the send.

**The LabOS build is ahead of where the week counter says; the delivery is behind, and the reason is
entirely on our side of the line.** Two of five milestones are complete, verified, and green
(132 offline tests, re-run today). The 5-week calendar window opened 2026-07-23 and **expired on
2026-08-27** — we are on day 36 of a 35-day plan with W3/W4/W5 not started. The single blocking
dependency is a list of four asks to the Airtable team that has been **written since 2026-08-23 and never
sent**. Nothing external is late. We are.

Second finding, and the more serious one: the proposal-extraction defect is now **quantified against the
sample job**, and it is worse than "a data-quality concern". It has already corrupted a *completed* test
record in the production base.

---

## 1. What is actually built, and verified today

Re-verified on 2026-08-28, not taken from the previous session's notes.

| | Evidence |
|---|---|
| **132 offline tests pass** | `python3 -m unittest discover -s tests -t .` → `Ran 132 tests … OK`, 0.012s, stdlib only |
| **Airtable client, envelope builder, schema probe** | `app/airtable/{client,contract,envelope,mapping,probe,errors}.py` |
| **Live schema probe, both bases** | re-run today, read-only, **0 failures / 4 warnings** on each. Identical results to 2026-08-23 |
| **P1 attempt schema + migration** | `alembic/versions/b7c2e9a41d38_p1_airtable_identity_and_attempts.py`, rehearsed |
| **Autogenerate-at-boot removed; real 30-revision chain in git** | `ifet-management` `94cb452` |
| **Both PATs held safely** | `ifet-management/.env`, mode `600`, gitignored. Not in git, not in a browser-served config |

**Deployed: nothing.** Both integration branches (`feature/labos-firmware-p3`,
`feature/labos-airtable`) are pushed, clean, and unmerged. Production runs `latest`, untouched.

---

## 2. The schedule, stated honestly

| | |
|---|---|
| Plan window | 2026-07-23 → 2026-08-27 (5 weeks) |
| Today | **2026-08-28 — day 36 of 35.** The window has closed |
| Milestones complete | **W1** (foundations + client/probe/envelope) · **W2** (P1 schema & identity) |
| Milestones not started | **W3** requirements-IN · **W4** bidirectional sync · **W5** screens, hardening, cutover |

**2 of 5 delivered against 5 of 5 elapsed.** W4 was flagged in the internal plan as the crunch
(sync queue, ~13 points, highest risk) and it is entirely ahead of us. A 5-week plan cannot absorb
three remaining milestones including its own riskiest one; **the end date needs to move, and the
conversation about how far is now overdue rather than upcoming.**

The plan's own documented mitigation — swap W3⇄W4 and build the sync plumbing against the canonical
envelope while ratification is pending — is still available and is now the right call, because W3
cannot be *trusted* until §3 clears regardless of when we build it.

---

## 3. ⚠️ The extraction defect, measured against the sample job

Previously recorded as "values shift one column" (contract §10.19, findings §5.2). Today it was checked
end to end for the first time: **the sample proposal PDF `IFET-26-0066.pdf` against what the production
base actually stores.** The characterization holds, and the blast radius is bigger than recorded.

**Proposal, `IFET-26-0066` — Sliding Glass Door, mock-up 1.** Column positions read off the PDF text
layer and cross-checked against the header offsets, so the true row is not in doubt:

| Proposal column | Proposal says | Airtable `Value` | |
|---|---|---|---|
| LMI (impacts) | `9` | `9` | ✅ |
| SMI (impacts) | *(blank)* | `10` | ❌ value invented |
| # Dials | `10` | `Full` | ❌ |
| Static / Type | `Full` | `+60/60` | ❌ |
| **DP (+) (PSF)** | **`+60/60`** | **`9`** | ❌ **the dangerous one** |
| Water (PSF) | `9` | *(blank)* | ❌ lost |
| Forced Entry (*) | *(blank)* | *(blank)* | ✅ |
| Cyclic (PSF) | `+60/60` | `+60/60` | ✅ |
| Impact | *(blank)* | *(blank)* | ✅ |

**Four of the six populated requirement values are in the wrong field.** The mechanism is confirmed: the
blank `SMI` cell is dropped, and every value from `SMI` through `DP` slides exactly one column left. The
trailing `Cyclic` value is unaffected, which is what makes the row look plausible at a glance.

### Why this is a safety item, not a data-quality item

1. **`DP (+) (PSF)` reads `9` where the design pressure is `+60/60`.** A rig driven from that value loads
   the specimen to **9 PSF instead of 60** — under-loaded by a factor of ~6.7. The test passes trivially
   and certifies a door that was never actually loaded. Nothing downstream can catch it: 9 PSF is a
   perfectly ordinary number in that column, and it is in fact the *correct* value for the column next to it.
2. **It has already reached a completed record.** `SMI (impacts)` carries `Value = 10` with
   `Result = Passed`, `Status = Completed` — but the proposal has **no SMI value at all**. A test in the
   production base is recorded as passed against a requirement that does not exist in the source document.
   This is not a future risk being prevented; it is existing data already affected.
3. **There is no correction we can apply.** We cannot reconstruct the intended column from the stored
   value, because the shift depends on which cells were blank in the original PDF — information that does
   not survive into Airtable. It has to be fixed at their extractor.

**The standing rule therefore hardens rather than relaxes:** *no rig is driven from an Airtable
requirement value, and no LabOS result is written against one, until the extractor is fixed and a
re-extraction of affected jobs is confirmed.* Contract §10.19.

---

## 4. What the live bases look like today

Both bases probed read-only today. **Schema is byte-for-byte what it was on 2026-08-23 — nothing has
moved, because nothing was asked.**

| Ask (drafted 2026-08-23, unsent) | State today |
|---|---|
| Fix the proposal extractor | ❌ not raised · **blocks W3 and any live test** |
| `Test Type` option set — only `Static Load` exists | ❌ still one option · **blocks writing back 4 of 5 test types (W4)** |
| `Corrects Attempt ID` + `Correction Reason` | ❌ still absent · corrections and retests remain indistinguishable |
| `Required Value` (number) + `Required Unit` on Protocol Sections | ❌ still absent · `Value` remains free text holding `9`, `Full`, `+60/60` |
| Rename `Abborted` → `Aborted` | ❌ still misspelled in both bases (we send their spelling; harmless) |
| Approval for the single test write into the testing base | ❌ not requested · **stage 3 verification still gated** |

Confirmed unchanged and working: `Photos` = `url` · all four ID fields plain text · `Impact Result` free
text · `Test Result` = `Pending/Passed/Failed/Not Applicable/Inconclusive` (their spelling, which we send).

We also hold read access to the production dashboard interface
(`app0OCunbmuXl7Hc9/pagGRZZBAH691m3x5`). Interfaces are not exposed by Airtable's metadata API, so it is
a human review surface only — useful for eyeballing what operators see, not an integration surface.

**Their instruction — *"nothing will change in original base except LabOS Raw Data Table"* — has been
honoured. Nothing has been written to either base, including the raw table.**

---

## 5. Where the delivery actually stands, by owner

**On the Airtable team:** nothing. They answered every question asked of them within a day, delivered
both PATs on 2026-08-23, and have had no open request since.

**On us:**

1. ~~The four asks in §8 — written, approved, unsent for 5 days.~~ ✅ **SENT 2026-08-28**, as a formal
   verification report. Now waiting on their reply, not on us.
2. Stage 3 verification — **now a script**, `ifet-management` `tests/stage3_live_write.py`, dry-run verified.
   Gated only on the approval the report asks for.
3. Notion is **four pages behind**: Field Mapping, Response, Verification Report, 5-Week Plan.
4. W3/W4/W5 not started.
5. A re-baselined end date, which needs to be proposed rather than discovered.

---

## 6. Deploy hazard — still live, unchanged

Until the `startup.sh` change ships, **every container restart on `management` appends a no-op revision
and moves the Alembic head.** Deploy `startup.sh` and the P1 migration **together**, and re-confirm
`SELECT * FROM alembic_version;` returns `3a65a83e0463` immediately beforehand. A head we do not descend
from means two heads, and `upgrade head` then silently refuses.

Ground truth for migrations is **the node, not the repo**.

---

## 7. The shortest path out, in order

1. **Send the §8 message today.** Re-framed for a Friday send rather than a Monday call; the four asks
   and their ordering are unchanged. Lead with the extraction defect and include the `IFET-26-0066`
   table from §3 above — a measured example of their own sample job is far harder to deprioritize than
   a description of the problem.
2. **Ask for a new joint slot** in the same message, since the Monday one lapsed.
3. **On their OK, run stage 3** — one upsert round-trip into the testing base `app4oXS3Kd5IKWgJ7`,
   table `tblnc9SsbXU0C0FWh`, upsert on `LabOS Attempt ID`, test type `Static Load` (the only option
   that exists). Production base is never touched. Do **not** run the stale stage-3 payload in
   `docs/labos-airtable/correspondence/verification-report-2026-07-29.md` — it targets the retired sandbox and sends fields
   that do not exist.
4. **Start W4 ahead of W3**, per the plan's own documented mitigation. The sync queue needs no field
   names and is the highest-risk remaining work; W3 cannot be trusted until item 1 lands anyway.
5. **Propose a re-baselined end date** with the message, rather than letting it be inferred.

---

## 8. Sources

| Claim | Backed by |
|---|---|
| Build state, test count | `unittest` run 2026-08-28 · `ifet-management@94cb452` |
| Live schema, both bases | `python3 -m app.airtable.probe` re-run 2026-08-28, read-only |
| Extraction defect | `pdftotext -layout IFET-26-0066.pdf` vs. Protocol Sections in `app0OCunbmuXl7Hc9` |
| Open items | `docs/labos-airtable/evidence/write-contract-v0.3-superseded-2026-09-06.md` §10 (authoritative) |
| Outbound message | `docs/labos-airtable/evidence/live-probe-findings-2026-08-23.md` §8 (authoritative) |
| Week sequencing, W3⇄W4 swap | `docs/labos-airtable/status/internal-plan-2026-07-23.md` |
| Deploy hazard, migration chain | `docs/labos-airtable/evidence/p1-schema-and-migration-mechanism-2026-08-23.md` · `docs/operations/ssh-session-record-2026-08-23.md` |
