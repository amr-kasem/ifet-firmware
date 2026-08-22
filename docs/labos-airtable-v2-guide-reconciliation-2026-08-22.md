# Reconciliation — Airtable *API Integration Guide v2* (received 2026-08-17)

**Author:** Abdelrahman (LabOS) · **Date:** 2026-08-22 · **Status:** internal delta + ready-to-send reply
**Their doc:** `IFET_Phase_2_LabOS_Airtable_API_Integration_Guide_v2.pdf` (4 pp, generated 2026-08-17)
**Supersedes as the current outbound artifact:** `labos-airtable-team-doc-review-2026-07-29.md`
**Canonical open items:** `labos-airtable-write-contract-v0.3.md` §10 — *this document is a view of it*

---

## 0. Verdict

**Substantially better, and it unblocks real work — but it silently removed things the write model depends on.**

v2 gives us the two things correspondence could not: a **dedicated testing base**, and **real table IDs**. It
also fixes the security problem in v1 by keeping tokens out of the document entirely. Four of the eleven
fields we asked for were granted, including the one that mattered most — the JSON field, which is what keeps
the Airtable schema stable as test methods evolve.

Against that: v2 **collapsed the two date fields into one**, and dropped `Test Name`, the correction fields,
`Abort Reason` and the wall snapshot from the raw table. Two of those removals are load-bearing. And the
single longest-running open item — how test *requirements* come out of Airtable in machine-readable form —
is still not addressed, which means **W3 remains blocked by the same thing that blocked it three weeks ago.**

---

## 1. What v2 closes

| Contract §10 | Item | How v2 closes it |
|---|---|---|
| **4** | Writable table isolation | **Two bases.** Testing `app4oXS3Kd5IKWgJ7`, production `app0OCunbmuXl7Hc9`. This is the arrangement we asked for in the 2026-07-29 review §3. |
| **6** (part) | The 11 requested fields | **4 granted:** `Schema Version` · `Max Pressure Achieved` · `Deflection Unit` · `Complete LabOS JSON Response`. |
| **10** (part) | Leaked PAT | **Remediated.** v2 contains no token; delivery is explicitly out-of-band. LabOS never used or stored the v1 token. |
| — | Table identification | All nine table IDs published, including the write target `tblnc9SsbXU0C0FWh`. |

**`Complete LabOS JSON Response` is the most valuable thing in v2.** It is our `Result Detail (JSON)` under
their name, and it means most future test-method changes cost an Airtable schema change of exactly zero. Six
of the seven fields still missing can ride inside it.

---

## 2. What v2 changed that we have to respond to

### 2.1 The `Test Date` collapse — *blocking* (contract §10.13)

v2 replaces `Testing Start Date` and `Testing End Date` with a single **`Test Date`**.

Two consequences, both real:

1. **Test duration disappears from the record.** For a cyclic test that runs hours, or a static load test
   with timed holds, duration is part of the result, not metadata about it.
2. **The two-write lifecycle loses its timing.** LabOS writes once on start (`In Progress`, for live
   visibility) and once at terminal state. With one date field, the second write either overwrites the first
   date or leaves the end time unrecorded. Neither is correct.

**Ask:** restore both fields. **Fallback if refused:** `Test Date` means *start*, duration moves into
`Complete LabOS JSON Response`, and the two-write lifecycle (§10.8) has to be confirmed explicitly rather
than left implicit.

Worth noting: this also **dissolves open item 0** — v1's contradiction was that `Testing End Date` was
always-required while an `In Progress` row has no end date. v2 resolved that by deletion. The contradiction is
gone; so is the data.

### 2.2 `Corrects Attempt ID` and `Correction Reason` are absent — *blocking* (contract §10.14)

These are the **only two fields the JSON valve cannot rescue**, and the reason is structural: Airtable
automations have to *branch* on them. A value buried in a long-text blob cannot be filtered on, linked from,
or rolled up. Carrying them in JSON would satisfy LabOS and do nothing for Airtable.

What breaks without them, concretely — this is contract §3.1:

- A **retest** is two real test events. Both rows are valid data; the specimen was tested twice.
- A **correction** is one test event recorded wrongly. Only the second row is true.
- `Attempt Number` increments identically in both cases. **Nothing else distinguishes them.**

So any Airtable automation that counts attempts, computes a pass rate, or reports "tests performed" is
**wrong in one of the two cases**, and there is no way to tell which. This is not a hypothetical: the
PSI→PSF scaling fix on 2026-07-09 would have produced exactly this situation had the integration been live —
a result written as `40 PSF` that was really `40 PSI`, needing supersession rather than a silent edit.

The alternative — editing the original row — is what we are specifically designing against. For a lab whose
output is certification evidence, a number that changes with no record of when or why is the failure mode.

### 2.3 Seven further fields absent — *not blocking* (contract §10.15)

`Test Name`, `Abort Reason`, `Required Value`, `Required Unit`, `Cycles Required`, `Cycles Completed`,
`Test Rig`, `LabOS Version`, `Result Rationale`, and the six wall-snapshot fields.

LabOS will carry these in `Complete LabOS JSON Response` and is **not** blocking on them. Two exceptions
worth asking for as first-class fields, because both are things a human reads directly off the row:

- **`Test Name`** — without it, a raw row is identifiable only by `rec…` IDs. Anyone opening the table sees
  no indication of what was tested.
- **`Abort Reason`** — an `Aborted` row currently carries no cause at all.

Also worth confirming: is the wall-snapshot omission **deliberate**? We are content to drop it, but the
reason it existed was that Airtable's reservation record can move after the test, and then nothing records
where the test physically happened.

### 2.4 `Test Result` option spelling — *cheap to fix, expensive to miss* (contract §10.16)

Their v2 example writes `"Test Result": "Passed"`. Our contract specifies `Pass`. A single-select mismatch
either returns 422 or silently creates a duplicate junk option, and the same exposure applies to every select
field in the envelope. The schema probe settles it; we should also confirm it in writing.

---

## 3. What v2 did **not** address — and why it is now the critical path

**Contract §10.3 — the read-side parameter structure.**

v2 §6 step 5 says only: *"Perform testing in LabOS using the requirement values read from Airtable."* It
publishes the Protocol Sections table ID (`tblqpvuJlSdkeS9PS`) but no field specification for it.

This is the one item **the schema probe cannot settle.** A probe reveals which fields exist and their types;
it cannot tell us whether the contents are machine-readable. A field named `Requirements` of type long text
would pass a schema check and still fail this contract — because the operator would then re-type the design
pressures by hand, which is precisely the manual step the integration exists to remove.

What LabOS needs is either:

- **discrete typed fields** — `Design Pressure Inward (PSF)`, `Design Pressure Outward (PSF)`, `Hold Time (s)`,
  `Cycles Required`, `Deflection Points`, `Loading Sequence (JSON)`; **or**
- **one versioned `Required Testing Parameters (JSON)`** field on Protocol Sections.

Either is fine. Free text is not. **This gates W3**, and it has been open since 2026-07-23.

---

## 4. The read-only promise is not enforced by the token

Recording this because it creates a LabOS obligation that did not exist under the one-base model.

Airtable PAT scopes are **per base, not per table**. The testing PAT therefore carries
`data.records:write` — and `schema.bases:write` — across *every* table in `app4oXS3Kd5IKWgJ7`, including the
four hierarchy tables v2 marks READ only. Nothing on the Airtable side prevents a stray LabOS write.

**LabOS enforces it client-side:** the API client hard-codes a write allowlist of exactly
`tblnc9SsbXU0C0FWh` and raises on any attempt to mutate another table. Contract §0.1. This is not a complaint
about their design — it is the correct design — but the guarantee has to live somewhere, and it lives with us.

---

## 5. Ready-to-send reply

> **Subject:** LabOS response — API Integration Guide v2
>
> Thanks for v2 — the separate testing base and the published table IDs are exactly what we needed to start
> building against something concrete, and keeping the tokens out of the document is the right call.
> Confirming that LabOS never used or stored the token that appeared in the earlier PDF.
>
> Four of the fields we asked for are in the new raw table, including `Complete LabOS JSON Response`. That one
> does a lot of work for both sides: most future changes to our test methods can go inside it without you
> having to touch the Airtable schema or the automations that depend on it.
>
> Four things we need to settle before we can call the write contract final.
>
> **1. Test requirements coming *out* of Airtable — our longest-standing open item, and the one blocking the
> most work.** v2 says to "use the requirement values read from Airtable", but doesn't specify how those
> values are structured on Protocol Sections. We need them machine-readable: either discrete typed fields
> (`Design Pressure Inward (PSF)`, `Design Pressure Outward (PSF)`, `Hold Time (s)`, `Cycles Required`,
> `Deflection Points`, `Loading Sequence (JSON)`), or a single versioned `Required Testing Parameters (JSON)`
> field. Either works for us. If the values are free text, the operator ends up re-typing design pressures by
> hand — which is the manual step this integration is meant to remove. **This is the item we would most like
> to close this week.**
>
> **2. `Test Date` — could we have the start and end back as separate fields?** v2 merged them into one. Two
> problems: test duration is part of the result for anything cyclic or with timed holds, and we write twice
> per attempt (once at start so you get live visibility, once at the terminal state). With one date field the
> second write either overwrites the first or leaves the end time unrecorded. If two fields aren't possible,
> we'll treat `Test Date` as the start time and carry duration in the JSON field — but we'd need you to
> confirm the two-write pattern is fine on your side.
>
> **3. `Corrects Attempt ID` and `Correction Reason` — we'd like to re-request these two specifically.** We're
> happy to carry the other missing fields inside the JSON field, but these two won't work there, because your
> automations need to branch on them. The problem they solve: if a test is re-run, that's two genuine results.
> If a test was recorded wrongly and re-entered, only the second is true. In both cases the attempt number
> goes 1 → 2, and without a reference field the two are indistinguishable — so any roll-up counting attempts
> or computing a pass rate is wrong in one of the two cases, with no way to tell which. We never edit or
> delete a submitted row (that's the audit trail for certification evidence), so a correction has to arrive as
> a new row that says what it supersedes. With the field present, your automation can mark the old row
> superseded and exclude it from roll-ups.
>
> **4. Two smaller ones.** Could we add `Test Name` and `Abort Reason` as regular fields? Without `Test Name`
> a raw row is only identifiable by record IDs, so the table is hard to read for anyone opening it; and an
> aborted row currently records no cause. Everything else on our list we'll carry in the JSON field.
>
> One small thing to check: the example in v2 sends `"Test Result": "Passed"`, and we had `Pass` in our
> contract. We'll read the live option sets off the schema endpoint as soon as the token arrives and match
> whatever is actually configured — just flagging it since a mismatch on a single-select either errors or
> quietly creates a duplicate option.
>
> Also confirming we understand the wall/reservation fields are intentionally not part of the raw table, and
> that production automation stays off until you enable it.
>
> Whenever the testing PAT is ready, we have the verification steps prepared and can turn the schema check
> around the same day.

---

## 6. LabOS-side actions from this reconciliation

| # | Action | Status |
|---|---|---|
| 1 | Contract → `v0.3`; §0 records v2's environment, §10 reconciled | ✅ done 2026-08-22 |
| 2 | Retire base `appYBTqIL43pmS0xN` from all live docs; banner the two 2026-07-29 sent docs | ✅ done 2026-08-22 |
| 3 | Airtable API client with a **hard write allowlist** of `tblnc9SsbXU0C0FWh` (§4) | next |
| 4 | Schema probe — closes contract §10.1/.2/.5/.16 and verifies all nine table IDs in one call | next |
| 5 | Offline payload contract tests asserting the exact wire names (`Airtable Mockup ID`, `LabOS Report Link`, `Complete LabOS JSON Response`) | next |
| 6 | Send §5 reply; escalate the read-side parameter structure | pending review |
