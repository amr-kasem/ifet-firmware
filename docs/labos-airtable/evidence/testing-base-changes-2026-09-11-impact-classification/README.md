# Testing Base change — the Impact classification pair, 2026-09-11

**Testing Base `app4oXS3Kd5IKWgJ7`: 160 → 162 fields. Production `app0OCunbmuXl7Hc9` untouched at 142.**

Two fields created on `LabOS Raw Data Table`, and **nothing deleted, renamed or retyped**.

| Field | Type | Field ID | Why |
|---|---|---|---|
| `Impact Classification` | singleSelect — `SMI` · `LMI Level D` · `LMI Level E` | `fldMY7DiiuP9kbQbL` | Which missile classification an impact ran under. **Derived** from `missile_impact_tests.impact_family` + `.impact_level`; no column holds the string and no API field sets it |
| `Target Impact Velocity` | number, precision 2 | `fldhywP9YpsmoWWT1` | The target the operator entered, ft/s. From `missile_impact_tests.target_velocity` |

## The direction reversal this completes

On 2026-09-08 three fields were added to **Protocol Sections** so Airtable could supply the missile, its
mass and a target velocity. On 2026-09-10 the product owner replaced all three with one classification
chosen in LabOS. Airtable's `Requirement Code` already distinguishes `IMPACT_SMI` from `IMPACT_LMI`, so the
only fact it never carried was the level — and that is the operator's.

So the impact requirement Airtable owns is now exactly the **count**, and LabOS publishes what it ran under.
**Two fields added that we write; three fields we stopped reading.** Read surface 19 → **16 named fields**.

## The three are still there, and that is deliberate

`Missile Type` `fld5Bs0aQXXeVso2y` · `Missile Weight` `fldmhdhonyyLcx4Ex` · `Impact Velocity`
`fldJNfUVyqQEFOVWx` remain **physically present in the Testing Base and unread**. Deleting a field in a base
shared with the Airtable team is not a side effect of a code change; removal is a cleanup agreed with them.

Being unread is enforced rather than asserted. `preflight` check **1a** imports the real
`mirror.SECTION_FIELDS` and fails if any of the three reappears on it — a field back on the allowlist starts
being copied again with nothing else changing, which is exactly the drift worth a gate. They were **never
created in production** and check **2** guards all twenty fields, withdrawn ones included, against it.

## Verified, not asserted

Read back from the Meta API immediately after the write, independently of the tool that did it:

- both fields on `LabOS Raw Data Table` `tblnc9SsbXU0C0FWh`, with the ids above;
- `Impact Classification` is `singleSelect` with choices exactly `['SMI', 'LMI Level D', 'LMI Level E']`;
- `Target Impact Velocity` is `number` with `precision: 2` — **type alone is not the contract here.** A
  select with the wrong choices accepts nothing LabOS sends, and precision 0 would silently truncate
  50.25 ft/s. Both would pass a type check and fail in front of an operator;
- Testing **162**, Production **142**, neither new field in production.

`check_register.py` PASS · real `preflight.py` clean against both bases, no warnings · **400 tests passed
on Postgres 13, zero failures.**

## Files

`before-*.json` · `after-*.json` · `changes-*.json` — the apply tool's own capture and its applied diff,
which contains exactly two `created` entries and fifteen `skipped`.
`meta-before-*` / `meta-after-*` / `meta-final-*` — independent Meta API pulls of **both** bases, before
the write, immediately after, and after the finalisation.
`preflight-before.txt` · `preflight-after.txt`.

**No record was written.** This was a schema change only; the live record probe is a separate step.
