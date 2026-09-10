# Pre-TA7 baseline — both live bases, 2026-09-10

**Read-only.** No writes, no schema changes, no records created. Captured immediately before TA7 so
that any disagreement TA7 introduces can be diffed against a state somebody actually measured, rather
than against what the documents claimed.

## Live field counts, from the Meta API rather than from documentation

| Base | ID | Tables | **Fields** |
|---|---|---|---|
| Testing | `app4oXS3Kd5IKWgJ7` | 8 | **160** |
| Production | `app0OCunbmuXl7Hc9` | 8 | **142** |

Delta **18** — the applied additions, none of which are in production. Confirmed twice by independent
pulls: `preflight.py`'s own count and the raw capture in this directory.

## What is here

| File | What it is |
|---|---|
| `meta-testing-app4oXS3Kd5IKWgJ7-*.json` | The **raw** `GET /v0/meta/bases/{base}/tables` response, verbatim |
| `meta-production-app0OCunbmuXl7Hc9-*.json` | The same for production |
| `preflight-2026-09-10.txt` | `python -m app.airtable.preflight` output, all five checks |
| `inventory.md` | 70 LabOS-relevant fields, grouped by table: field id, type, per-base presence, direction, **runtime owner/consumer**, register state |

## No credentials, by construction and by check

The raw files are the Meta API's own response body — table, field, id, type, and Airtable's field
options. **No request is recorded, so no `Authorization` header exists in them**, and the tokens are
read from the gitignored `.env` and never printed. `meta/bases/…/tables` returns *schema only*: no
record content, no customer data, no commercial values. Scanned for credential-shaped content before
filing; clean. The `fld…` ids were already throughout this tree.

## What the inventory is actually for

It joins five things that had never been put in one place: the live schema of **both** bases, the
`mirror.py` read allowlist, `contract.py`'s write declarations, `mapping.py`/`envelope.py`'s writers,
and the register. Building it turned up one layer the delivery plan's own source-chain description had
missed — **`envelope.py`**, which applies `wire_name` and phase gating between `mapping.py` and the
wire. Several fields (`Test Status`, `Test Date`, the withheld measurements) are written there and
**nowhere in `mapping.py`**, so a reader checking `mapping.py` alone concludes they have no writer.
They do.

Two `RENAMED` pairs are the other thing worth knowing before reading any of this:

| Internal name (`contract.py`) | Wire name (Airtable, and the register) |
|---|---|
| `Airtable Mock-Up ID` | `Airtable Mockup ID` |
| `Result Detail (JSON)` | `Complete LabOS JSON Response` |

A join that does not follow `wire_name` in the right direction reports both as having no writer. Ours
did, on the first pass.

## Result

**No disagreement between live Airtable, runtime code, the field register, the generated documents and
the production change spec.** Preflight: 161 spec rows checked, 0 disagree. Every `IN` register row is
exactly a `mirror.py` allowlist entry and the reverse. Every non-`OMITTED` `OUT` row has a writer.

The single absent-but-not-`OMITTED` row is the local-only queue-metadata row, which is documented as
never created in Airtable.

**The disagreement that matters is not between the layers — it is between all of them and the
2026-09-10 decision.** `Missile Type`, `Missile Weight` and `Impact Velocity` are modelled consistently
everywhere as inbound requirements LabOS reads, and every one of those is now wrong by decision. That
is what TA7 changes, and this is the state it changes *from*.
