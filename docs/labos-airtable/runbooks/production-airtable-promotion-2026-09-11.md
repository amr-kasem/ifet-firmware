# Production Airtable promotion spec — 2026-09-11

> **DO NOT APPLY FROM THIS REPOSITORY.** `apply_schema.py` refuses the production base unconditionally
> and has no flag that overrides it — that refusal is deliberate and must not be removed. This document
> is what the **Airtable team** works from, after explicit approval. Everything below is derived from the
> two live bases read read-only on 2026-09-11, the field register and the write contract; nothing here is
> a stale count.

## The delta, in one line

**Production `app0OCunbmuXl7Hc9` is at 142 fields. This proposes 19 additions and nothing else.**
Expected count after promotion: **142 + 19 = 161**.

| Action | Count | Meaning |
|---|---|---|
| **ADD** | **19** | create in production; present in Testing and verified there |
| **KEEP** | **142** | already in production, unchanged — **type as well as presence** |
| **OPTION CHANGE** | **0** | no existing single-select gains, loses or renames a choice |
| **RENAME** | **0** | nothing is renamed. A rename needs its own explicit approval and there is none |
| **OMIT / DEPRECATED** | **3** | present in Testing, withdrawn from the contract, **never to be created here** |
| **DELETE** | **0** | nothing is removed from production. Ever, in this change |

## ⚠️ Field IDs do not travel between bases

Every `fld…` below is the **Testing Base** id, given so a reviewer can find the field and compare it.
Airtable mints a new id when the field is created in production, and **the two will not match**. Nothing in
LabOS depends on a production field id: the contract keys on the field *name*, and
`interface-schema.csv` carries `field_id_production` as a separate column that is filled in after the fact,
not assumed. Do not copy a Testing id into anything that expects a production one.

## The additions

### `Protocol Sections` — 8 fields

| Field | Type | Choices | Precision | Direction | LabOS source | Testing field ID | In production |
|---|---|---|---|---|---|---|---|
| `Applicability` | singleSelect | Required · Not Required · Unconfirmed | — | IN — LabOS reads | `at_mirror_sections.applicability` | `fldh3VS09fonTLHsS` | absent |
| `Required Option` | singleLineText | — | — | IN — LabOS reads | `manual_tests.required_option` | `fldflOxCkAK1BkU9l` | absent |
| `Required Unit` | singleSelect | PSF · in · s · cycles · impacts | — | IN — LabOS reads | `(validation)` | `fldTjNKeQe7oxxl33` | absent |
| `Required Value` | number | — | 0 | IN — LabOS reads | `projects.gauge_count / projects.impact_count` | `fldpL2dyGzKj9xowY` | absent |
| `Required Value Inward` | number | — | 0 | IN — LabOS reads | `projects.inward_design_pressure` | `fld1wR9ojdmESax0m` | absent |
| `Required Value Outward` | number | — | 0 | IN — LabOS reads | `projects.outward_design_pressure` | `fld7GLStvnPnYJPpd` | absent |
| `Requirement Code` | singleSelect | STATIC_PRESSURE · CYCLIC_PRESSURE · IMPACT_LMI · IMPACT_SMI · FORCED_ENTRY · ANSI_IMPACT · GAUGE_COUNT · STATIC_PROGRAMME · WATER_PRESSURE | — | IN — LabOS reads | `at_mirror_sections.requirement_code` | `fld9Fzjj25ngrVIOB` | absent |
| `Requirement Kind` | singleSelect | Magnitude · Directional Pair · Count · Enum · Not Applicable | — | IN — LabOS reads | `(interpretation)` | `fldWGpL9gJh89wSK8` | absent |

### `LabOS Raw Data Table` — 11 fields

| Field | Type | Choices | Precision | Direction | LabOS source | Testing field ID | In production |
|---|---|---|---|---|---|---|---|
| `ANSI Result` | singleSelect | Pending · Passed · Failed · Inconclusive | — | OUT — LabOS writes | `test_results.test_result` | `fldmCKJV95N9uL7xt` | absent |
| `Corrects Attempt ID` | singleLineText | — | — | OUT — LabOS writes | `test_results.corrects_attempt_id` | `fldV4ucQNEA0gYfMc` | absent |
| `Forced Entry Result` | singleSelect | Pending · Passed · Failed · Inconclusive | — | OUT — LabOS writes | `test_results.test_result` | `fldAHuPzZHZEj0Cjt` | absent |
| `Impact Classification` | singleSelect | SMI · LMI Level D · LMI Level E | — | OUT — LabOS writes | `derived from missile_impact_tests.impact_family + impact_level` | `fldMY7DiiuP9kbQbL` | absent |
| `Impact Number` | number | — | 0 | OUT — LabOS writes | `test_results.trial_number` | `fldk52wf0SO9zYDjB` | absent |
| `LabOS Photos` | multipleAttachments | — | — | OUT — LabOS writes | `uploads/ downscaled copy` | `fldsEfhtH9wXPAl1Y` | absent |
| `LabOS Verdict At` | dateTime | — | — | OUT — LabOS writes | `test_results.verdict_at` | `fldqCkqAh7aTckxSR` | absent |
| `LabOS Verdict By` | singleLineText | — | — | OUT — LabOS writes | `test_results.verdict_by` | `fldVedw9cOgne8UeX` | absent |
| `Target Impact Velocity` | number | — | 2 | OUT — LabOS writes | `missile_impact_tests.target_velocity` | `fldhywP9YpsmoWWT1` | absent |
| `Testing End Date` | dateTime | — | — | OUT — LabOS writes | `test_results.testing_end_date` | `fldTsjf78Y5fA85fz` | absent |
| `Testing Start Date` | dateTime | — | — | OUT — LabOS writes | `test_results.testing_start_date` | `fldYU1BtWVuWv5DBV` | absent |

**Datetime shape.** `Testing Start Date`, `Testing End Date` and `LabOS Verdict At` are created
**ISO, 24-hour, UTC** — the shape `apply_schema` used in Testing. Their existing `Test Date` is
`local`/`client` and stays exactly as it is; these are new columns LabOS owns, and a UTC instant that
renders in a viewer's own zone is what a certification record needs.

**Number precision.** `Target Impact Velocity` is precision **2** and this is not cosmetic — precision 0
silently truncates 50.25 ft/s, and it would pass a type check while doing it. `Impact Number` is an
integer ordinal, precision 0.

**Select choices are exact, and the spelling is theirs.** `Forced Entry Result` and `ANSI Result` must be
created as `Pending` · `Passed` · `Failed` · `Inconclusive`. A select created with LabOS's own `Pass`/`Fail`
would accept nothing LabOS sends. `Impact Classification` is exactly `SMI` · `LMI Level D` · `LMI Level E`.

## What must NOT be created

These three were added to the **Testing** Base on 2026-09-08 and withdrawn from the contract on
2026-09-10, when the product owner made the impact classification LabOS-owned. They are deliberately left
in Testing rather than deleted — removing a field from a shared base is a coordinated cleanup, not a side
effect — and they must **never** reach production, where they have never existed.

| Field | Table | Testing field ID | Why not |
|---|---|---|---|
| `Impact Velocity` | Protocol Sections | `fldJNfUVyqQEFOVWx` | WITHDRAWN from the read contract 2026-09-10. |
| `Missile Type` | Protocol Sections | `fld5Bs0aQXXeVso2y` | WITHDRAWN from the read contract 2026-09-10. |
| `Missile Weight` | Protocol Sections | `fldmhdhonyyLcx4Ex` | WITHDRAWN from the read contract 2026-09-10. |

This is enforced, not remembered: `make-production-change-spec.py` omits any register row marked
`DEPRECATED`, and `preflight.py` check 2 asserts all 22 guarded fields — the 19 additions **and** these
three — are absent from production on every run.

## Verification, before and after

```
# before — read-only, from a checkout, against both live bases
python3 -m app.airtable.preflight --env ../../.env

# after the Airtable team has applied the additions
python3 -m app.airtable.preflight --env ../../.env      # check 2 will now report the adds present
python3 -m app.airtable.interface_schema \
    --out  ../../../ifet-firmware/docs/labos-airtable/contract/interface-schema.csv \
    --register ../../../ifet-firmware/docs/labos-airtable/contract/field-register.csv \
    --env ../../.env                                    # fills in field_id_production
```

**Check 2 inverts on the day production is promoted.** It currently asserts that none of the guarded
fields is in production, and that assertion is what makes "production is untouched" a fact rather than a
claim. After promotion it must be rewritten to assert the 19 present and the 3 still absent — that edit is
part of the promotion, not a follow-up, and the run above is what proves which of the two states holds.

## Approval

| | |
|---|---|
| Proposed by | LabOS, 2026-09-11 |
| Requires | **explicit approval from the Airtable team**, and from the project owner for the schema change itself |
| Applied by | the Airtable team, in their own base |
| Expected result | production **161** fields, 0 removed, 0 retyped, 0 renamed |
| Working sheet | `../evidence/testing-base-changes-2026-09-06/production-change-spec.csv` — one row per field for all 161, generated |
