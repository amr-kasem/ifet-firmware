# Testing Base change — the per-standard result pair, 2026-09-11 (TA6)

**Testing Base `app4oXS3Kd5IKWgJ7`: 162 → 164 fields. Production `app0OCunbmuXl7Hc9` untouched at 142.**

Two fields created on `LabOS Raw Data Table` `tblnc9SsbXU0C0FWh`, and **nothing deleted, renamed or
retyped**.

| Field | Type | Field ID | Why |
|---|---|---|---|
| `Forced Entry Result` | singleSelect — `Pending` · `Passed` · `Failed` · `Inconclusive` | `fldAHuPzZHZEj0Cjt` | The Forced Entry verdict on its own axis. From `test_results.test_result`, gated to `Test Type = Forced Entry` |
| `ANSI Result` | singleSelect — the same four | `fldmCKJV95N9uL7xt` | The same for ANSI Z97.1 |

## Why these exist, given we had argued they should not

The register's standing rule was *"no dedicated scalar; revisit only if a named operational report
requires one"* — DG8, closed under A9 on 2026-09-06. The product owner reopened it on 2026-09-10:
question 2 came back **NO**, with the reason *"they are different under different standards"*. He did not
name a report, he named a reason, and the rule was ours. So the decision stands and the rule bends.

**They are additions to `Test Result`, not replacements for it.** `Test Result` is written at create (as
`Pending`), at terminal and at verdict, for all five test types; a type that stopped writing it would
vanish from every status view in the base. `Impact Result` is already exactly this shape sitting beside
it, so Forced Entry and ANSI are joining a pattern rather than getting a new one.

**`Failure Notes` was not added.** He named two fields. A third on inference is how a shared base fills
with columns nobody asked for.

## No new source of truth

Both fields carry the value of `test_results.test_result` — the *same* value as `Test Result`, projected
by test type, never a second lifecycle:

| Type | phase | `Test Result` | `Forced Entry Result` | `ANSI Result` |
|---|---|---|---|---|
| Forced Entry | terminal | `Pending` | `Pending` | *omitted* |
| Forced Entry | verdict | the verdict | the same verdict | *omitted* |
| ANSI Z97.1 | terminal | `Pending` | *omitted* | `Pending` |
| ANSI Z97.1 | verdict | the verdict | *omitted* | the same verdict |
| Static Load · Cycles · Impact | any | the verdict | *omitted* | *omitted* |

The non-applicable field is **omitted, never blank** — `mapping.py` yields `None` and §5 of the envelope
turns that into an absent key rather than an empty cell.

## The wire spelling, not the LabOS one

The choices are created as `Pending · Passed · Failed · Inconclusive`. LabOS's internal vocabulary is
`Pending · Pass · Fail · Inconclusive` and `contract.Field.option_wire` is what translates — the same
authoritative mapping `Test Result` already uses, not a second one. **A select created with `Pass`/`Fail`
would reject every verdict LabOS sends**, and would pass a type check while doing it, which is why
`preflight.EXPECTED_CHOICES` asserts the exact list rather than the type.

## Verified, not asserted

Read back from the Meta API immediately after the write, by a separate tool from the one that wrote:

- both fields on `LabOS Raw Data Table` `tblnc9SsbXU0C0FWh`, with the ids above;
- both `singleSelect` with choices exactly `['Pending', 'Passed', 'Failed', 'Inconclusive']`, in that
  order;
- a full before/after diff of **both** bases: Testing `+2`, `0` removed, `0` retyped; production
  `+0/-0/~0`, byte-identical in structure;
- Testing **164**, production **142**, neither new field in production.

`check_register.py` PASS · real `preflight.py` clean against both bases, **no warnings** · **408 tests
passed on Postgres 13, zero failures, zero skipped.**

## Files

`before-*.json` · `after-*.json` · `changes-*.json` — the apply tool's own capture and its applied diff:
exactly two `created` entries and seventeen `skipped`.
`meta-before-*` / `meta-after-*` — independent Meta API pulls of **both** bases, before the write and
immediately after.
`preflight-before.txt` · `preflight-after.txt` — note that *before* reports the pair as `PENDING`, and
*after* reports `none owed`.

**No record was written.** This was a schema change only; the live record probe is a separate step, in
`ta6-live-probe-2026-09-11/`.
