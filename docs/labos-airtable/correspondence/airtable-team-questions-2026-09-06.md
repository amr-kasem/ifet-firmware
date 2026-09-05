# Answers to the Airtable team's three questions, and what still needs them

**Author:** Abdelrahman · **Date:** 2026-09-06 · **Epic:** IFET-32 · **Status:** `DRAFT — NOT SENT`
**Supersedes:** `airtable-team-questions-2026-08-31.md` (never sent; its text is preserved)
**Evidence:** `../schema/baseline-2026-09-05/` · `../design/integration-design-2026-09-05.md` ·
`../design/field-register-2026-09-05.csv`

> **What this document is.** The authoritative *wording* of our reply. Item **statuses** stay owned by
> contract §10; this is a view of it. §1–§3 answer their three questions. §5 is the ask list — it contains
> **only questions that require their input**; our own gates (deflection calibration, the missing pressure
> source) are not their problem and are not in it. §7 is the reply, ready to paste.
>
> **Not sent. Do not send without review.**

---

## 0. What changed since 2026-08-31

**They shipped, and did not announce it.** Our read-only baseline of both bases on 2026-09-05 found three
changes against the 2026-08-23 snapshot:

| Change | Effect |
|---|---|
| `Test Type` now offers all five options — `Static Load · Cycles · Impact · Forced Entry · ANSI Z97.1`, **in both bases** | **§10.17 closes.** This was a P0: it blocked writing *any* Impact, Forced Entry or ANSI result. Gone. |
| `Test Date` → `dateTime` | **§10.20 closes** on delivery, exactly as their Q3 said. |
| `Correction Reason` added (multilineText) | §10.14 narrows — see §2, it needs a companion to be usable. |

Nothing else moved; the raw table went 29 → 30 fields. **The lesson for us is procedural: diff the baseline
before assuming §10 is current.** It is now a committed, repeatable export
(`ifet-management` `app/airtable/baseline.py`, read-only).

**The 2026-08-31 draft was never sent.** It is superseded by this document rather than sent alongside it —
its §2 read-side specification survives intact here, and its call agenda is obsolete.

---

## 1. Answer to Q1 — how we want requirements represented machine-readably

**Unchanged from the 2026-08-31 specification, and now argued from your own live data.**

Five typed fields on `Protocol Sections` (`tblqpvuJlSdkeS9PS`). **`Value` is unchanged** and stays the
human-facing display string — once these exist, LabOS never parses it again.

| Field | Type | Populated when | Notes |
|---|---|---|---|
| `Requirement Kind` | single select | always | `Magnitude` · `Directional Pair` · `Count` · `Enum` · `Not Applicable` |
| `Required Value` | number | `Magnitude`, `Count` | Signed. A genuine zero is `0`; absent is **blank** |
| `Required Value Inward` | number | `Directional Pair` | **Positive magnitude, PSF** |
| `Required Value Outward` | number | `Directional Pair` | **Positive magnitude, PSF** |
| `Required Unit` | single select | any kind carrying a number | `PSF · in · s · cycles · impacts` |

**Two numbers is the whole ask.** LabOS derives the entire preset programme from the design-pressure pair —
six static stages, eight cyclic stages, the water stage. Confirmed again on 2026-09-05 in our production
database: **minimum 6 static and 8 cyclic stages per project, 498 of 508 and 632 of 634 flagged `preset`.**
So Airtable models no ranges, no cycle sequences, no hold times. We read two numbers and compute the rest.

**And the pair is genuinely two independent numbers** — 36 of 78 projects (**46%**) have inward ≠ outward.
Collapsing `+60/60` into one value loses real data in nearly half of all jobs, unrecoverably.

**`Requirement Kind` is the field that earns its place.** Without it LabOS infers shape from `Section Name`,
so the day a section is added or renamed our parser is guessing again, silently. With it, a mismatch between
the declared kind and the fields present is a loud validation failure on our side **before a rig moves**.

> **Our commitment, so this is a two-way rule:** an unrecognised `Section Name`, or a `Requirement Kind` we
> do not implement, is displayed and recorded but **cannot start a test**. We will not best-effort parse
> something we do not understand. That is the discipline that would have caught §10.19 before it reached a
> rig.

**Blanks must stay blank.** `Water (PSF)` blank and `Water (PSF) = 0` are different statements, and one of
them is a test.

*(Your §2.3 alternative — one long-text `Required Testing Parameters (JSON)` — we can still build against.
We are not re-proposing it: JSON in long text cannot be filtered, sorted, grouped or rolled up, and your own
interface pages cannot display it. The typed fields serve your side as well as ours.)*

---

## 2. Answer to Q2 — retests, and why `Corrects Attempt ID` cannot be dropped

**Your retest model is correct, and we adopt it as stated.** Each physical rerun gets a **new
`LabOS Attempt ID`** and an **incremented `Attempt Number`**, grouped under the **same `LabOS Test ID`**.
Nothing to change.

**A correction is a different event, and the shared Test ID cannot express it.**

| | Retest | Correction |
|---|---|---|
| What happened | the specimen was **tested again** | a result was **recorded wrongly** |
| `LabOS Attempt ID` | new | new |
| `LabOS Test ID` | same | same |
| `Attempt Number` | incremented | incremented |
| **Which attempt it supersedes** | — *(nothing is superseded)* | **must be stated** |

`LabOS Test ID` **groups** records. It does not order them and it does not say that one supersedes another.
Given two attempts sharing a Test ID, it cannot distinguish "we ran it twice" from "the first one was wrong".
Those have different meanings for a report, and only one of them invalidates earlier data.

**So we need `Corrects Attempt ID` back** — one `singleLineText`, written only on the correcting row. This is
the same ask as contract v0.2 and it is the last blocking item on the write side.

**`Correction Reason` arrived without it.** We appreciate the field; as it stands it is a reason with nothing
to point at. The pair is what makes a correction expressible.

**How LabOS behaves meanwhile:** a recorded verdict is immutable on our side — a correction mints a new
attempt and never rewrites the original. Until `Corrects Attempt ID` exists, that correction reaches your base
looking like an ordinary retest, and the distinction lives only in LabOS.

---

## 3. Answer to Q3 — `Test Date`

**Accepted, and confirmed delivered** — our 2026-09-05 baseline shows `Test Date` as `dateTime` in both
bases. §10.20 closes.

**We send UTC**, ISO-8601 with `Z`. A `dateTime` stores an instant, so your client-timezone display setting
changes how it reads, not what it holds. Our lab reports render `America/New_York` with the offset shown.

**One thing the type change does not settle: does `Test Date` mean the *start* of testing or its
*completion*?** The type is agreed; the semantics are not (§10.13 — a single instant cannot hold both).

This costs nothing to defer: **LabOS stores both instants regardless**, and both travel in
`Complete LabOS JSON Response`, so whichever convention you pick, nothing needs re-deriving. But a report
that mixes conventions across jobs is not correctable afterwards, so we would rather agree it than discover
it. See §5, Q6.

*(Related, and unaffected: `Testing Date` on `Protocol Sections` is a plain `date`. A date has no instant, so
we render it in `America/New_York` before writing — a test finishing 21:00 EDT would otherwise file as the
next day.)*

---

## 4. What we verified in your production base on 2026-09-05

Read-only, and shared because two findings affect the answers above.

**Your `Protocol Sections` table is an attribute/value model** — `Section Name` is the attribute, `Value` the
value. Nine attributes, one row each per specimen, across four protocols. This is *why* the §1 typed fields
matter: the requirements are there, they are simply untyped.

**Three of six specimens on `IFET-25-0111` have no TAS-202 requirements at all**, while all six carry TAS-203
cyclic pressures:

```
                    spec-1  spec-2  spec-3  spec-4  spec-5  spec-6
TAS-202 DP (+)      +75/75    —       —       —    +75/75  +110/110
TAS-202 Water        11.25    —       —       —     11.25     8.25
TAS-202 # Dials          1    —       —       —         1        1
TAS-203 Cyclic      +75/75  +75/75  +75/75 +110/110 +75/75  +110/110
```

In **LabOS's** model this is decisive: cyclic pressures are derived from the design-pressure pair, so a
specimen with `Cyclic` and no `DP` cannot be executed — the input is missing. Whether it also indicates the
extraction defect depends on whether *your* model requires `DP` whenever `Cyclic` is populated, which is §5
Q7. We are not asserting more than we can support.

**And on `Fixed Window - 6`, all nine sections read `Passed` / `Completed` — including three whose
requirement value is blank** (`Impact`, `Forced Entry (*)`, `SMI (impacts)`). We are not inferring what that
means; §5 Q5 asks.

---

## 5. Open questions — these need your input

Ordered by blast radius, not by convenience. Our own open items (deflection calibration, and a missing
pressure measurement source in our firmware) are **not** in this list — they are ours to close.

### P0

**Q1 — the extraction defect, §10.19. Still open, still the highest item.** Your PDF extractor drops blank
cells, so values shift column: the sample job reads `DP (+) (PSF) = 9` where the proposal says `+60/60`, and
`60 × 0.15 = 9` identifies the shift arithmetically. **Standing rule on our side until it is fixed: LabOS
displays Airtable requirement values read-only and will not start a pressure-driven test from them.** What is
the status, and can we help test the fix?

**Q2 — sign convention.** `DP (+) (PSF)` reads `+110/110` and `+75/75`. We read that as
`+inward / outward`, both **positive magnitudes in PSF**. Is the second number ever negative-signed in other
jobs? Every example in the base is symmetric, so the data cannot answer this and **we will not infer it** —
this is the last thing standing between us and reading pressures machine-readably.

**Q3 — `Corrects Attempt ID`** (§2 above). One `singleLineText` on the raw table.

### P1

**Q4 — the five typed fields** in §1, plus ratification of the section→kind mapping below. **Is the list of
nine section names closed?** A tenth appearing later would silently change what LabOS reads.

| `Section Name` | `Requirement Kind` | `Required Unit` |
|---|---|---|
| `DP (+) (PSF)` | `Directional Pair` | `PSF` |
| `Cyclic (PSF)` | `Directional Pair` | `PSF` |
| `Water (PSF)` | `Magnitude` | `PSF` |
| `LMI (impacts)` · `SMI (impacts)` | `Count` | `impacts` |
| `# Dials` | `Count` | *(none)* |
| `Static / Type` · `Forced Entry (*)` · `Impact` | `Enum` | *(none)* |

**Q5 — two questions about `Protocol Sections`, from the data in §4.** (a) Which sections is LabOS expected
to produce results for? `# Dials` and `Static / Type` look like *parameters*, not tests, yet both carry
`Result` and `Status`. (b) When your automation rolls a LabOS attempt up into `Protocol Section.Result`, does
that field mean "the test passed" or "this row is closed"? It matters because a LabOS verdict and an
operational state would otherwise merge silently.

**Q6 — does `Test Date` mean start or completion?** (§3).

**Q7 — does your model require `DP` whenever `Cyclic` is populated?** (§4). If yes, three of the six live
specimens are provably incomplete and we can flag them automatically.

### P2

**Q8 — an attachment field for evidence.** We propose `LabOS Photos` (`multipleAttachments`) **beside** the
existing `Photos` url field, which we are not touching. Airtable accepts direct uploads to 5 MB; we downscale
lab-side, so no public LabOS server is needed and your copy survives our systems being offline. LabOS retains
the originals.

**Q9 — two verdict fields**, `LabOS Verdict By` (`singleLineText`) and `LabOS Verdict At` (`dateTime`). A
verdict whose author is not on the wire is not auditable. Until they exist we ship both inside
`Complete LabOS JSON Response`.

**Q10 — production replication.** Our production token is `schema.bases:read`, so we cannot apply any of the
above to the production base ourselves. **Who applies the agreed changes there, and when?** Acceptance
testing cannot conclude in production without it. We will deliver a change register with a rollback note per
change.

---

## 6. Not blocking — for your planning only

**A whole-record `Last Modified Time` on the four read tables.** Today the only `lastModifiedTime` fields in
the base are *field-scoped* (`Project Status Modified Time` watches Project Status alone), so LabOS reads all
four tables in full each cycle. At today's volume — 1 project, 6 specimens, 24 protocols, 54 sections — that
is four requests a minute and entirely fine. It stops being fine somewhere around ten thousand records.
Nothing needed now.

---

## 7. The reply — ready to paste

> Hi both,
>
> Thanks — and thanks for the schema changes. We ran a read-only check across both bases on 5 September and
> found all five `Test Type` options live, `Test Date` as a `dateTime`, and `Correction Reason` added. That
> clears the item that was blocking us from writing any Impact, Forced Entry or ANSI Z97.1 result, so that is
> a real unblock on our side. Answers to your three questions first, then what we still need.
>
> **1 — Machine-readable requirements.** Five typed fields on `Protocol Sections`: `Requirement Kind`,
> `Required Value`, `Required Value Inward`, `Required Value Outward`, `Required Unit`. `Value` stays exactly
> as it is, as the human-facing string. The ask is smaller than it looks: LabOS derives the whole test
> programme from the design-pressure pair, so you do not need to model ranges, cycle sequences or hold times
> — just the two numbers in PSF. We confirmed against our production data that a minimum of 6 static and 8
> cyclic stages per project all derive from that pair, and that 46% of jobs have inward ≠ outward, so the two
> directions do have to stay separate. In return: if we meet a section name or requirement kind we do not
> recognise, we display it and refuse to run it. We will not guess.
>
> **2 — Retests.** Your model is right and we are adopting it as-is: new Attempt ID, incremented Attempt
> Number, same Test ID. We do still need `Corrects Attempt ID`, for a different case. A retest means the
> specimen was tested again; a correction means a result was recorded wrongly and an earlier attempt is
> superseded. The shared Test ID groups records but cannot say which one supersedes which — given two
> attempts, it cannot tell "we ran it twice" from "the first was wrong", and those mean different things in a
> report. One `singleLineText` on the raw table covers it. `Correction Reason`, which you have added, is the
> other half of the same pair.
>
> **3 — `Test Date`.** Accepted, and confirmed delivered. We send UTC, ISO-8601 with a `Z`. One thing the type
> change does not settle: does it mean the start of testing or its completion? We store both instants either
> way and both travel in the JSON field, so there is no rush — but it is worth agreeing rather than
> discovering later.
>
> **What we still need from you, in order:**
>
> 1. **The proposal extraction issue.** Still our highest item. Values shift a column when blank cells are
>    dropped — the sample job reads `DP (+) (PSF) = 9` where the proposal says `+60/60`. Until it is fixed we
>    show Airtable requirement values read-only and will not start a pressure test from them. What is the
>    status, and can we help test the fix?
> 2. **Sign convention.** Does `+110/110` ever carry a negative second number? Every example in the base is
>    symmetric, so we cannot tell from the data and we would rather ask than assume.
> 3. **`Corrects Attempt ID`**, per point 2 above.
> 4. **The five typed fields**, and confirmation that the nine section names are a closed list.
> 5. **Two questions about `Protocol Sections`:** which sections should LabOS produce results for — `# Dials`
>    and `Static / Type` look like parameters rather than tests — and when your automation sets
>    `Protocol Section.Result`, does that mean the test passed, or that the row is closed?
> 6. **`Test Date`** — start or completion.
> 7. **Does your model require `DP` whenever `Cyclic` is populated?** On `IFET-25-0111`, three of six
>    specimens have cyclic pressures but no design pressure. In our model that specimen cannot be run at all,
>    so if the same holds for you we can flag it automatically.
> 8. **An attachment field**, `LabOS Photos`, alongside the existing `Photos` — so evidence lives in your base
>    rather than behind a link to our server.
> 9. **Two verdict fields**, `LabOS Verdict By` and `LabOS Verdict At`.
> 10. **Who applies the agreed changes to the production base**, and roughly when. Our production token is
>     read-only on schema, so acceptance testing cannot finish there without you. We will send a change
>     register with a rollback note for each change.
>
> Happy to take any of this on a call if that is faster.
>
> Best,
> Abdelrahman

---

## 8. Sent record

**Not sent.** Stamp the date, channel and recipients here when it goes, and copy the exact text sent if it
diverges from §7.
