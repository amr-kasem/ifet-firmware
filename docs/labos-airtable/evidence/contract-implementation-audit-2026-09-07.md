# Contract implementation audit — 2026-09-07

**Scope:** read-only reconciliation of the v0.4 prose contract, field register, both live Airtable schemas,
the `ifet-management` integration branch, the firmware MF branch, and the live `management` node. No Airtable
record or schema write was issued. No node file, container or service was changed.

## 1. Separation of concerns confirmed

| Platform | Owns | Must not own |
|---|---|---|
| Airtable | Business hierarchy, permanent `rec…` IDs, job/specimen/protocol/section display, operational views and automations | Rig control, LabOS procedures, local evidence, or the authoritative execution record |
| LabOS on `management` | Local work whether Airtable exists or not, explicit Airtable linking, programme/run identity, frozen procedure and inputs, manual capture, review, outbox, reconciliation and result projection | Parsing Airtable's legacy `Value`, live dependence on Airtable, or direct writes to hierarchy tables |
| Firmware rigs | Execute Static Load/Cycles, acquire device telemetry, and return a stable stage event with the backend-issued run binding | Airtable access, pass/fail ownership, programme derivation, or choosing a result destination |

Decision A9 therefore remains the safety boundary: the runtime reads Airtable identity/display plus
`Requirement Code` and `Applicability`, but **no Airtable requirement value reaches a rig**. The other six
typed Protocol Section additions remain useful to Airtable and future versions, but are `IGNORED` by this
runtime release while the extractor defect exists.

## 2. Live access and schema evidence

| Check | Result |
|---|---|
| Local secret file | Present, mode `600`; testing and production PAT variables are populated. Values were neither printed nor copied |
| Testing PAT | Authenticated `schema.bases:read` and `data.records:read` against all four read tables |
| Production PAT | Authenticated `schema.bases:read` and `data.records:read` against all four read tables |
| Interface regeneration | 168 rows; 163 real fields: 10 read, 38 mapped outbound, 1 read-only, 114 ignored, plus 5 metadata/local rows. Exact byte-for-byte match with `contract/interface-schema.csv` |
| Testing Base | 8 tables, 156 fields; the four hierarchy tables are still empty |
| Production Base | 8 tables, 142 fields; read-only sample reads succeeded |
| Public shared-base link | `https://airtable.com/app0OCunbmuXl7Hc9/shr18UCpayz45a4D5` returns HTTP 200 without a token. Visual rendering could not be rechecked because no browser instance was available |

The 73-row register is now **73 DECIDED**: 44 BASELINE, 14 APPLIED, 4 CONDITIONAL, 10 OMITTED and 1
PLANNED local-only. The former seven OPEN/PROPOSED rows were resolved by A9 and are now OMITTED. The
generator's summary text still calls seven absent real fields "proposed" because it only distinguishes
`PLANNED` from other absent rows; all seven are actually `OMITTED` in the register. The generated CSV itself
is correct.

No write-scope test was performed: proving `data.records:write` by creating a row would be a mutation and is
part of the controlled vertical-flow acceptance. The Testing Base schema-write authority was exercised and
recorded on 2026-09-06 when the 14 additions were applied.

## 3. Production ground truth

Read-only SSH to `management` returned:

- branch `latest` at `90f9595`, clean worktree;
- PostgreSQL 13 live alembic head `3a65a83e0463`;
- the seven legacy containers up for two weeks;
- therefore neither P1 `b7c2e9a41d38` nor M2 `c4e1f8a92b07` is deployed.

This reconfirms that every integration path remains greenfield against LabOS production.

## 4. Code-flow evidence by test type

| Test | Existing management flow | Firmware flow | Contract implementation state |
|---|---|---|---|
| Static Load | `StaticTest` / `StaticTestResult`; GET by project + test index; POST `/trials` | MF binding/event code landed | Existing execution works; programme/run binding and idempotent backend callback are open |
| Cycles | `CyclicTest` / `CyclicTestResult`; GET next cyclic test; POST `/trials` | MF binding/event code landed | Same open backend half as Static |
| Impact | `MissileImpactTest` / `Shot` exist for report generation | none | No capture route or programme/run integration |
| Forced Entry | no model, table or route | none | No backend |
| ANSI Z97.1 | no model, table or route | none | No backend |

Firmware evidence is in `src/state_machine/state_machine.py`, `src/state_machine/api/api.py` and
`src/state_machine/tests/test_run_binding.py`. Management evidence is in `app/data/models.py` and
`app/main.py`. `app/main.py` imports neither `app.airtable` nor `app.sync`, so no current route creates a
contractual run or enqueues a phase.

## 5. Material v0.4 implementation drift found

`app/airtable/contract.py` now declares v0.4 and the live field types, but the code behind that declaration
still implements v0.3 lifecycle semantics:

| v0.4 contract | Current management code |
|---|---|
| Create writes `Test Result = Pending` | `envelope.build()` refuses any Test Result while In Progress |
| Terminal keeps result Pending; first review writes Passed/Failed/Inconclusive | terminal builder requires the final verdict immediately; no review builder/mapping exists |
| `Test Date` is absent at create and equals completion at terminal | start builder writes `Test Date` from `Testing Start Date` and terminal deliberately preserves it |
| Send real `Testing Start Date` and `Testing End Date` columns | builder explicitly skips both and carries them only through the old JSON-collapse path |
| Review writes `LabOS Verdict By`, `LabOS Verdict At`, rationale and Retest Required together | ORM/migration/mapping have no reviewer columns or review mutation |
| Programme and run are separate; attempt ordinal is per programme | committed models still treat legacy `TestResult` as the attempt and have no programme/run or mirror tables |

The existing green unit tests assert the stale behavior, so changing only the version constant made the
suite greener without making the envelope compliant. This reopens the ninth §8 deviation and blocks a live
Testing Base vertical write.

## 6. Verification run

- Management unit discovery: **140 passed, 2 skipped** in this workstation environment. The two sync
  modules skipped because SQLAlchemy is not installed here. This is not a reproduction of the earlier
  PostgreSQL-harness result; that recorded result remains evidence, but it must be rerun when lifecycle work
  changes.
- Testing schema probe: **0 failures, 1 warning**. The warning is expected from the probe's older read-side
  wording; live fields and types passed.
- Firmware tests were not rerun because this workstation has no `pytest` executable/module. The existing
  22-test and isolated-harness results remain the recorded MF evidence, not a fresh claim from this audit.

## 7. Required closure before a vertical write

1. Make the management lifecycle/envelope tests express v0.4 create → terminal → verdict phases, then fix
   the builder and mapping to pass them.
2. Add the programme/run, mirror/import and review persistence required by the authoritative contract; do
   not extend the legacy attempt model further as a substitute.
3. Validate one synthetic envelope for each of the five test types against the live Testing schema without
   writing, including omitted measurement guards.
4. Then perform the controlled Testing Base vertical flow and separately verify Airtable automations before
   production replication.

