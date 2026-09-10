# Project owner's answers, and the Impact remap — 2026-09-10

**Received:** WhatsApp, Luis (project owner), 2026-09-10, in reply to
`sent/2026-09-08-po-five-test-approval-request.md`.

**Already replied and agreed, same day:** the Impact simplification (§3 below). **Still to send:** the
short block at the end — acknowledgements for 1, 2 and 4, the three parameters we now owe, question 5,
and two corrections.

**One correction to the record first.** `sent/2026-09-08-po-five-test-approval-request.md` says the
outgoing list "is numbered 2–4" and that question 1 dropped out. It did not — the message as actually
sent carried all four, numbered 1–4, and he answered all four. That file is append-only and stays as it
is; this is the correction. **Question 5 (`STATIC_PROGRAMME`) was genuinely never asked** — it was in
`po-followup-2026-09-08.md`, which was never sent, along with the deflection and "implemented"
corrections. All three are still owed.

---

## What he said, verbatim

> "Impact" — Airtable provides missile type, weight, number of impacts, and target velocity → LabOS
> records each impact → Airtable receives one result per impact, including pass/fail and photos
>
> Not sure what weight is there for. once we now the type, LMI or SMI, we know the rest. Target velocity
> is either SMI, which is just one option, or LMI Level D or E. I think it would be easier if i tell LabOS
> which one it is, D or E, and that info goes to AirTable. We should discuss with AirTabe team.

> 1. ANSI Z97.1 should be recommended first, but not block other tests — correct? **YES**
> 2. Forced Entry and ANSI can both use the shared Test Result field rather than separate result fields —
>    correct? **I would think NO since they are different under different standards**
> 3. Should the target Impact Velocity be shown to the operator in LabOS? **We will be entering it**
> 4. Can Impact Location remain detailed LabOS data rather than a separate Airtable field? **I'm assuming
>    you mean the physical Locations. That will not be shown on LabOS or Airtable. that is in the test
>    plans.**

## What we replied, and he agreed — 2026-09-10

> I'll simplify the Impact requirement so LabOS uses the impact classification — SMI, LMI Level D, or LMI
> Level E — rather than treating missile weight and target velocity as separate required inputs. Once the
> classification is selected, LabOS will use the corresponding test parameters and send the selected
> classification along with the test result to Airtable.
>
> I'll keep the number of impacts as a separate requirement, since that defines how many impact attempts
> are required.

**"Impact classification" is the settled term** and is used throughout below and in the register. It
names one value from a closed set of three; everything else about the missile follows from it.

---

## 1. ANSI ordering — closed, no change

Recorded-not-enforced is confirmed. Question 1 is answered **YES**. No schema, no code, no document
change. The `ANSI_IMPACT` page's "what we cannot do yet" paragraph is now a statement of an approved
design rather than an open question.

## 2. Separate result fields — DG8 reopens

He said **NO** to the shared column, with the reason *"they are different under different standards"*.
The standing rule in the register was *"revisit only if a named operational report requires one"*. He did
not name a report; he named a reason. **He is the product owner and that is the decision** — the rule was
ours, and it exists to stop us inventing fields nobody asked for, which is not what happened here.

| Register row | Was | Becomes |
|---|---|---|
| `Forced Entry Result` (`LabOS Raw Data Table`, singleSelect) | `OMITTED` — DG8 closed by A9 | **build** — populated for `Test Type = Forced Entry`, blank on the other four |
| `ANSI Result` (`LabOS Raw Data Table`, singleSelect) | `OMITTED` — decided with Forced Entry | **build** — same shape, for `ANSI Z97.1` |
| `Failure Notes` (multilineText) | `OMITTED` — carried in `Notes` + JSON | **unchanged** — he did not ask for it, and we do not add it on inference |

**`Test Result` stays, and both new fields are in addition to it, not instead of it.** Three reasons,
worth stating to him because "separate fields" can be read as "replace the shared one":

1. `Test Result` is written at **create** (as `Pending`), at **terminal** and at **verdict**, for all five
   types. It is the attempt's lifecycle state as much as its verdict; a type that did not write it would
   be invisible to every status view in the base.
2. **The precedent already exists and he approved it.** `Impact Result` is a dedicated per-type result
   field that sits alongside `Test Result` today. Forced Entry and ANSI are joining a pattern Impact is
   already in, not being given a new one.
3. A type-specific field that is blank on the other four types is exactly `Impact Number`'s shape, which
   the Airtable team is already being told about in the change document.

**Coupled change, both repos:** two rows in `field-register.csv` (direction `OUT`, real `labos_source`),
`contract.FIELDS`, `mapping.py`, `preflight.ADDED` 18 → 20, `apply_schema` on the Testing Base
(160 → 162), and the change document's Test Results section. `check_register.py` check 4 fails until the
register and `preflight.ADDED` agree, so these move together or not at all. Tracked as **TA6**.

## 3. The Impact remap — agreed, and it collapses the read surface to one field

This came from the remark above the numbered answers rather than from question 3, and **his version is
better than ours**. If the impact classification determines both the mass and the target velocity, then
two of the three fields applied on 2026-09-08 carry no information the classification does not.

### As applied 2026-09-08 (TA2)

| Requirement | Airtable field | Direction | Lands in |
|---|---|---|---|
| Missile specified | `Missile Type` — Protocol Sections, singleLineText | IN | `missile_impact_tests.missile` |
| Missile mass | `Missile Weight` — Protocol Sections, number | IN | `missile_impact_tests.missile_weight` |
| Target velocity | `Impact Velocity` — Protocol Sections, number | IN | `at_mirror_sections.impact_velocity` |
| How many impacts | `Required Value` + `Requirement Code` | IN | `projects.impact_count` |

### As agreed 2026-09-10

| Requirement | Airtable field | Direction | Lands in |
|---|---|---|---|
| How many impacts | `Required Value` + `Requirement Code` | **IN — unchanged** | `projects.impact_count` |
| Impact classification — SMI · LMI Level D · LMI Level E | **on the results table** | **OUT** — selected in LabOS, published with the result | `missile_impact_tests.missile` |
| Missile mass | **none** — a parameter of the classification | — | `missile_impact_tests.missile_weight`, from the table |
| Target velocity | **none** — a parameter of the classification | — | not stored as a target; achieved stays `shots.velocity` |

**Why the count is untouched and the rest is not.** `Requirement Code` already distinguishes `IMPACT_LMI`
from `IMPACT_SMI`, so Airtable has always told us large versus small. The single fact it never carried is
**Level D versus Level E** — and that is exactly what the classification adds. The inbound side therefore
needs nothing at all: the three fields added on Monday were solving a problem that one existing field and
one operator selection solve better.

**And it takes Impact out of the extractor's blast radius.** Contract §10.19: their PDF extractor shifts
columns, a 60 PSF requirement reads as 9, and every shifted value is individually plausible. A missile
mass and a velocity read from a proposal are two more individually-plausible numbers on that path. A
selection from a closed set of three is not — a wrong pick is visible to the person making it. This is a
safety improvement, not only a simplification.

### What it costs

- `Missile Weight` `fldmhdhonyyLcx4Ex` and `Impact Velocity` `fldJNfUVyqQEFOVWx` become **unused**. Both
  are **Testing Base only** — production `app0OCunbmuXl7Hc9` was never touched and is still at 142 — so
  nothing has propagated and dropping them costs register rows, not a migration.
- `Missile Type` `fld5Bs0aQXXeVso2y` is on **Protocol Sections**, the requirement table. As an outbound
  fact the classification belongs on the **LabOS Raw Data Table**. So one field moves rather than flips:
  the Protocol Sections one joins the unused pair, and a new `OUT` field is created on the results table.
- The mirror allowlist loses three entries. Read surface: 19 named fields → **16**.

### The thing that must not be waved through

*"LabOS will use the corresponding test parameters"* means **LabOS now holds numbers that come from no
document anybody signed.** Today a wrong missile weight is Airtable's wrong number and LabOS can be shown
to have copied it faithfully. After this change it is *our* constant, and a wrong one is silently ours on
every impact test we ever run — the classification is chosen by a human who can see it, but the mass and
velocity behind it are never shown to anyone again.

So the table has to be his, in writing, before it is code:

| Classification | Missile | Mass | Target velocity |
|---|---|---|---|
| SMI | ? | ? | ? |
| LMI Level D | ? | ? | ? |
| LMI Level E | ? | ? | ? |

**We do not fill this in from a reading of ASTM E1996 and ask him to check it.** A table pre-filled by us
gets approved by glance; a blank one gets answered. Two further asks go with it: is the set exactly these
three, and **when is the classification selected** — once per protocol, or per test at the rig? The last
one decides whether it lives on the protocol mirror or on the attempt, and it is a schema question, not a
UI one.

### Question 3 is answered by the same change

*"We will be entering it"* closes **TC1f**. No new column on `missile_impact_tests`, and no target pushed
onto the operator's screen from Airtable: selecting the classification *is* stating the target velocity.
The achieved per-shot velocity is unaffected and stays local on `shots.velocity`, published only inside
the JSON response.

### He asked for this to reach the Airtable team

*"We should discuss with AirTabe team."* It does — inside the change document (TA5b), not as a separate
thread. That document is the artifact they are waiting for and it currently describes the superseded
four-field shape, so it cannot go out until the three parameters are back.

## 4. Impact location — confirmed, and wider than we asked

We asked whether location could stay LabOS-side rather than becoming an Airtable field. He confirmed no
Airtable field and went further: it is **not shown in LabOS either** — *"that is in the test plans."*

He is answering about the **specified** location — the spots on the specimen the missile is meant to
strike, which the technician already has on the test plan. There are two different things called
location, and his answer covers one of them:

| | What it is | Status |
|---|---|---|
| **Specified** location | a requirement — "hit the corner" | **Test plan. Not LabOS, not Airtable.** Confirmed by him. Costs nothing: never built |
| **Observed** location — `shots.area` | a record of where impact 3 actually landed, beside that impact's photographs, carried in the JSON | **Unchanged.** Same class of thing as the photographs |

`Impact Locations` in Airtable stays uncreated, now by his decision as well as ours. **One clause goes
back to him on the observed half** — *"will not be shown"* is loose enough that if he did mean `shots.area`
we would be deleting evidence, and that is not a thing to assume in either direction.

## 5. `STATIC_PROGRAMME` — still open, and never actually asked

Not in the sent message, not in his reply. Re-asked below.

---

## Net effect on the register

| Row | Now | After TA6 / TA7 |
|---|---|---|
| `Missile Type` — Protocol Sections | `IN` · `APPLIED` | `IGNORED` on Protocol Sections; new `OUT` row for the classification on `LabOS Raw Data Table` |
| `Missile Weight` — Protocol Sections | `IN` · `APPLIED` | `IGNORED` — applied to the Testing Base, deliberately unread |
| `Impact Velocity` — Protocol Sections | `IN` · `APPLIED` | `IGNORED` — same |
| `Impact Locations` | `IGNORED` · `OMITTED` | unchanged, now **confirmed** rather than assumed |
| `Forced Entry Result` | `OUT` · `OMITTED` | `OUT` · applied |
| `ANSI Result` | `OUT` · `OMITTED` | `OUT` · applied |
| `Failure Notes` | `OUT` · `OMITTED` | unchanged |

**No row is flipped yet, deliberately.** `check_register.py` binds the register to the code: check 1
requires every `IN` row to be exactly the `mirror.py` allowlist, check 4 requires every `APPLIED` row to
be exactly a `preflight.ADDED` assertion. Flipping a row here without the matching change in
`ifet-management` turns a green checker red and hides the next real drift. The rows carry a dated note
pointing here instead; the flip happens with the code. Verified green after the annotations,
2026-09-10.

---

## The reply — copy the block below

Thanks Luis — that's the mapping settled. Three quick acknowledgements and three things I still need.

**ANSI ordering** — noted. LabOS records it as the recommended first test and doesn't block the others.
No change.

**Separate result fields** — agreed, we'll add them. Forced Entry and ANSI each get their own pass/fail
column, the same way Impact already has its own. The shared `Test Result` stays alongside them, because
it's what carries every test through Pending to final and it's what the status views filter on — so you
get both: one column that works across all five tests, and a per-standard column that only ever holds its
own standard's verdict.

**Impact location** — understood, it stays in the test plans and gets no field on either side. One thing
to flag so it isn't a surprise later: LabOS still records where each impact landed, next to that impact,
as part of the record of what happened — the same as the photographs. What it won't do is treat a location
as a required value or put one on the operator's screen. Say if you meant that too and we'll take it out.

**On the impact classification, three things before we build it:**

- Is the list exactly three — SMI, LMI Level D, LMI Level E?
- What missile, mass and target velocity should each one carry? I'd rather have those from you than read
  them out of the standard ourselves. Once LabOS works them out from the classification, nobody sees those
  numbers again — so if one is wrong it's quietly wrong on every impact test from then on, and it'll be
  our number, not yours.
- Is the classification chosen once per protocol, or per test at the rig? That one changes where we store
  it, so it's worth getting right now rather than later.

**One I meant to ask and didn't.** Proposals carry a `Static / Type` — *Full* in everything we've seen.
LabOS reads it, checks it, then runs the same six-stage programme regardless. If *Full* is the only one in
practice that's fine as it stands. If it isn't, tell me and I'll make LabOS refuse the others out loud
rather than quietly run Full.

**And two corrections to what I sent you.** I said Airtable receives deflection data for Static Load. It
doesn't, and it can't yet — the gauges were never calibrated to a real unit, so we'd be sending numbers we
can't stand behind. They're recorded and kept in LabOS. Same for max pressure, for a different reason: we
can read it, nothing stores it yet. The sheet has this right on the Static Load page; my summary didn't.
And I said the Impact workflow was implemented — the shape you specified, one attempt per impact, is built
and tested now, but it wasn't when I wrote that, and nothing in this work is deployed yet.

Once the classification parameters are back I'll finalise the mapping and send it to the Airtable team.

---

## Notes for us, not for sending

**The three classification parameters are the only thing blocking TA5b.** Answers 1, 2 and 4 are all
foldable without him: 1 changes nothing, 2 is two fields on our own results table, 4 confirms an omission.
The change document cannot go out describing four Impact requirement fields when the shape has been
agreed away.

**The reply does not pre-fill the parameter table, and that is deliberate.** We could look up ASTM E1996
and send him three rows to confirm. He would confirm them, and the numbers would then be ours wearing his
signature. Blank rows get read; pre-filled rows get glanced at. This is the one place the simplification
moves risk *towards* us, and it is worth the extra round trip.

**Answer 2 reverses a decision we recorded as closed by A9** — DG8. Nothing about the reversal is
expensive, and the register's own wording invited it. Worth noting only because A9 closed seven rows on
the same reasoning, and this is the first to come back.

**The `sent/` record has a factual error about what was sent.** It says the list was numbered 2–4 and that
question 1 never went. All four went. The file is append-only so it stays wrong; this document is the
correction, and it matters because that file is what a later reader would use to work out which questions
are still open.

**Question 6 was confirmed verbally on 2026-09-08** and is unaffected by any of this.
