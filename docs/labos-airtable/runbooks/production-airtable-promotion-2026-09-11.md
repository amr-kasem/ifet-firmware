# Production Airtable promotion — internal execution notes, 2026-09-11

> **INTERNAL. This is not the document we send.**
>
> The **authoritative field contract** is
> `../correspondence/LabOS-Airtable-Production-Schema-Requirements-2026-09-11.md` and its generated
> companion `../correspondence/LabOS-Airtable-Production-Schema-Changes-2026-09-11.csv`. That pair is what
> the Airtable team works from, and it is the only place the field list lives.
>
> **This file deliberately does not restate the field list.** It used to, and a second copy of a field
> list is a second thing to forget to regenerate. What is here is the part the external document should
> not carry: our own ordering, verification and remediation procedure for the window.

## The delta, as the generated CSV computes it

Do not transcribe these numbers — read them from the CSV, or regenerate it:

```bash
python3 ../evidence/testing-base-changes-2026-09-06/make-production-change-spec.py
```

As at 2026-09-11 that prints **19 ADD · 0 CHANGE TYPE · 0 CHANGE OPTIONS · 3 DO NOT PROMOTE · 142 KEEP**,
and `production 142 today + 19 ADD = 161 after promotion`. The generator reads the live bases through
`interface-schema.csv`, so a rerun is the check.

## ⚠️ Field IDs do not travel between bases

Every `fld…` in the external document is a **Testing** ID. Airtable mints a new one on create and they
will not match. Nothing in LabOS depends on a production field ID — the contract keys on the field *name* —
and `interface-schema.csv` carries `field_id_production` as a column filled in after the fact, never
assumed.

## We cannot apply it, by construction

`apply_schema.py` refuses `app0OCunbmuXl7Hc9` unconditionally. There is no flag, argument or environment
variable that overrides it, and **that refusal must not be removed to make a promotion easier.** The
Airtable team applies these in their own base.

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
