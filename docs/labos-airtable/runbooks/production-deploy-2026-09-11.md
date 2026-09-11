# Production deployment runbook — LabOS ↔ Airtable, 2026-09-11

**Node:** `management`, branch `latest` (**not** `main`, stale since Oct 2024). **This node is production.**
Secrets and the `.env` migration: `ifet-management/deployment/SECRETS.md` §2. Earlier P0/P1 runbook:
`p0-p1-deploy-2026-08-28.md` — this one supersedes its §3 onwards and reuses its go/no-go discipline.

**Nothing in this runbook has been executed.** It is written to be executed at an agreed window, by a
person, with the deployment owner informed.

---

## 0. Release identity

| | |
|---|---|
| `ifet-management` | branch `feature/labos-airtable`, **local only — must be pushed and merged into `latest` before the window** |
| `ifet-firmware` | branch `feature/labos-firmware-p3`, docs and evidence only; no rig code changes in this release |
| Alembic head | **`e2b9d4c70a15`** (`requirement_source_verification`) |
| Migrations to apply | **10**, **from the node's head — which is `7ed2a670841e`, not `3a65a83e0463`.** See §1.2a before §2 |
| Image | one image, `build: ./src/management_service/`, used by **both** `report-api` and `sync-worker` |
| Airtable Testing | `app4oXS3Kd5IKWgJ7`, **164** fields |
| Airtable Production | `app0OCunbmuXl7Hc9`, **142** fields — unchanged by this deployment |

**There is no separate migrator service, and that is the current design.** `report-api`'s entrypoint
`startup.sh` waits for Postgres, applies migrations to head, and only then serves — and a migration failure
is **fatal**, so the API never serves against a half-migrated schema. `sync-worker` overrides the command to
`python -m app.sync.service`. Do not introduce a migrator service as part of this deployment.

---

## 1. PRE-DEPLOY

Run every item. Record every output in the deployment evidence folder, **including the ones that come back
empty** — a recorded zero is evidence; an unrecorded one is an assumption.

### 1.1 Release state

```bash
# in a clean clone, not on the node
git -C ifet-management  status --porcelain          # must be empty
git -C ifet-management  log -1 --format='%H %s'
git -C ifet-firmware    status --porcelain          # must be empty
git -C ifet-firmware    log -1 --format='%H %s'
```

Both branches are **local only** at the time of writing. Pushing and merging into `latest` is a
prerequisite, not part of the window.

### 1.2 Database — where it actually is

**The node is ground truth, not the repository.**

```bash
# on management
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c 'SELECT * FROM alembic_version;'
```

**As at 2026-09-11 this returns `7ed2a670841e`, not `3a65a83e0463`.** Whatever it returns, record it and
go to §1.2a: the migration list in §2 is computed from that starting point, and the release's first
migration declares `3a65a83e0463` as its parent.

### ⚠️ 1.2a The node mints its own revisions — reconcile the branch point first

**This is a prerequisite, not a check.** It was found on 2026-09-11 and it will recur.

The **deployed** `startup.sh` (branch `latest` @ `90f9595`) still calls
`command.revision(..., autogenerate=True)` at every container start, so each restart writes an **empty
no-op** into `alembic/versions` on the node and advances `alembic_version`. Those files are `.gitignore`d
there, so they exist nowhere in git. The repository's `startup.sh` stopped doing this on 2026-08-23 — the
node has not received that change yet, which is the whole point.

As at 2026-09-11 there is exactly one such revision:

```
7ed2a670841e   revises 3a65a83e0463   created 2026-09-09 12:30   def upgrade(): pass
```

**And `b7c2e9a41d38` — the release's first migration — also revises `3a65a83e0463`.** Put both in one
`versions` directory and Alembic sees **two heads**, `alembic upgrade head` refuses, and `startup.sh` makes
that fatal, so `report-api` never serves. This is Case B of `p0-p1-deploy-2026-08-28.md` §2.

**Enumerate the node-only revisions** (read-only, on the node). Note that `git ls-files --others
--exclude-standard` will **not** list them — they are ignored, not merely untracked:

```bash
cd ~/ifet-management/src/management_service/alembic/versions
ls *.py | sort > /tmp/node-versions.txt
# in a clean clone, on feature/labos-airtable
git ls-files src/management_service/alembic/versions/ | xargs -n1 basename | sort > /tmp/repo-versions.txt
comm -23 /tmp/node-versions.txt /tmp/repo-versions.txt      # the node-only files
```

**Then, off the node, in the clone:**

1. copy each node-only revision file into `feature/labos-airtable` and commit it, so the chain resolves
   everywhere;
2. re-point `b7c2e9a41d38.down_revision` to the node's **current** head;
3. re-run the rehearsal (`tests/rehearse_p1_migration.py`) and regenerate the revision graph — confirm one
   head, no branch points, all revisions reachable, both directions;
4. push, merge into `latest`, and **restart this runbook from §1.1**.

**Do it as late as possible, and do not restart the current stack in between** — another restart mints
another no-op and invalidates step 2. If the head has moved again when you reach §2, go back to step 1.

```bash
# how much real data is about to be migrated
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  SELECT (SELECT count(*) FROM test_results)          AS attempts,
         (SELECT count(*) FROM missile_impact_tests)  AS impact_tests,
         (SELECT count(*) FROM shots)                 AS shots;"
```

### 1.3 Backup — before anything else

```bash
# on management, before any container is touched
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" \
  > ~/labos-predeploy-$(date -u +%Y%m%dT%H%M%SZ).dump
ls -lh ~/labos-predeploy-*.dump          # must be non-trivial in size
```

**The database contents are certification evidence.** No migration runs until this file exists and its size
has been eyeballed.

### 1.4 Rehearse against the real data — a window prerequisite

The chain is rehearsed forward and back over the production *shape*
(`../evidence/migration-rehearsal-2026-09-11/`). It has **not** been rehearsed against a restore of the
node's data. Do that now, on a throwaway:

```bash
# off-production, isolated project name and port
docker compose -f src/management_service/tests/postgres_harness/docker-compose.yaml up -d
pg_restore -d "postgresql://m2:m2-throwaway-not-a-secret@127.0.0.1:15432/m2" \
  --no-owner --clean --if-exists ~/labos-predeploy-*.dump
M2_DATABASE_URL=postgresql+psycopg2://m2:m2-throwaway-not-a-secret@127.0.0.1:15432/m2 \
  python -m alembic upgrade head          # then verify, then downgrade one, then up again
docker compose -f src/management_service/tests/postgres_harness/docker-compose.yaml down -v
```

### 1.5 Open Impact attempts — a mandatory gate

```bash
DATABASE_URL="postgresql://$POSTGRES_USER:…@127.0.0.1:5432/$POSTGRES_DB" \
  python3 src/management_service/tests/check_open_impact_attempts.py
```

Read-only, one `SELECT`. **Record the output either way.**

| Exit | Meaning | Action |
|---|---|---|
| **0** | no open Impact attempts | **GO.** Paste the output into the evidence folder — a recorded zero is the point |
| **1** | some open | **Not a failed deployment — a deployment that needs a decision.** For each open attempt: set `impact_family`, `impact_level` and `target_velocity` explicitly on its test, **or** abort the attempt, **or** move the window. It will not finish under the new gate until one of those happens |
| **2** | could not check | **NO-GO.** Fix connectivity and re-run. Never assume zero |

> **Do not infer or backfill.** Nothing derives a classification from the free-text `missile` column, and
> nothing derives a target velocity from historical `shots.velocity`. The 39 historical tests keep `NULL` in
> all three columns and that is correct — the migration rehearsal asserts it.

### 1.6 Active work

```bash
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  SELECT test_type, count(*) FROM test_results
  WHERE status = 'In Progress' GROUP BY 1;"
```

Any row here is a test somebody is in the middle of. Coordinate the window around them.

### 1.7 Environment and secrets

```bash
./deployment/scripts/check-secrets.sh        # must print: secret hygiene: PASS
test -f .env && grep -c '^[A-Z_]*=' .env     # compose refuses to start without it
```

Confirm on the node, by eye:

| Variable | Required value at this deployment | Why |
|---|---|---|
| `AIRTABLE_BASE_ID` | the **Testing** base `app4oXS3Kd5IKWgJ7` | production Airtable is not promoted in this release |
| `AIRTABLE_WRITE_ALLOWLIST` | `tblnc9SsbXU0C0FWh` only | a PAT is scoped per *base*, not per table; this allowlist is what keeps LabOS out of their other seven tables |
| `AIRTABLE_ALLOW_PRODUCTION_WRITE` | `false` | a correct token plus a correct base id is deliberately **not** sufficient authority to write production |
| `AIRTABLE_SYNC_ENABLED` | `false` **for the first start**, then `true` once §4 is green | the worker exits cleanly with one log line rather than draining a queue nobody has approved |
| `LABOS_PUBLIC_ORIGIN` | the node's reachable origin | attachment URLs are built from it |

**Never** put the Airtable token in `deployment/config/config.json` or `src/ifet_ui_react/config.json` —
both are served to the browser.

### 1.8 Airtable, read-only, both bases

```bash
cd src/management_service
python3 -m app.airtable.preflight --env ../../.env
python3 app/airtable/check_register.py
```

Both must be clean. Expected: **Testing 164 · production 142 · delta 22 · none of the 22 guarded fields in
production**, and `PASS — the documents match what we built`.

### 1.9 Queue health

```bash
curl -s localhost:8000/sync/status | jq .     # before the deploy, for comparison
```

### 1.10 GO / NO-GO

| # | Check | GO when |
|---|---|---|
| 1 | Both working trees clean, branches pushed and merged to `latest` | yes |
| 2 | `alembic_version` on the node **read today**, and the branch point reconciled per §1.2a | the chain resolves to **one** head with the node's own no-ops included |
| 2a | No further no-op minted since that reconciliation | `comm -23` of the node's and the repo's revision lists is empty |
| 3 | `pg_dump` taken, non-trivial, readable | yes |
| 4 | Chain rehearsed against a restore of **this** dump, up and down | yes |
| 5 | `check_open_impact_attempts.py` run and its output recorded | **exit 0**, or exit 1 with every open attempt explicitly resolved |
| 6 | No test `In Progress` that the window would strand | yes |
| 7 | `check-secrets.sh` PASS and the five variables above confirmed | yes |
| 8 | `preflight.py` and `check_register.py` clean | yes |
| 9 | Deployment owner informed, window agreed | yes |
| 10 | §2.1 agreed — who verifies the design-pressure pair for open imported jobs, and how | yes |
| 11 | §2.2 agreed — what happens to rig Static Load and Cycles rows until an operator is declared at run start | yes |

**Any NO ⇒ do not proceed.**

---

## 2. DATABASE

Ten migrations, in this order, from the node's head as reconciled in **§1.2a** — `3a65a83e0463` plus whatever no-ops the node has minted since (`7ed2a670841e` as at 2026-09-11):

```
b7c2e9a41d38  P1 — Airtable identity and attempts
c4e1f8a92b07  M2 — sync outbox and fencing
d1a6b93f2e57  manual test capture
e5f3a71c8d92  attempt-number uniqueness        ← rewrites labos_test_id, then constrains it
f7b2c04e19a5  artifact delivery
a3d8e5c71f04  run-start operator
b9c1f60d4e27  mirror and requirement freeze
c7e4a2b81f56  impact — one attempt per impact  ← splits existing impact attempts and renumbers
a4f18c2d3b90  impact classification            ← additive, three nullable columns + one CHECK
e2b9d4c70a15  requirement source verification  ← head; additive, six nullable columns on `projects`
```

**Two of them rewrite existing rows** (marked above). That is why §1.4 exists.

`report-api`'s entrypoint applies them. To apply them deliberately, before serving:

```bash
docker compose run --rm --entrypoint "" report-api \
  python -m alembic -c alembic.ini upgrade head
```

Verify:

```bash
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c 'SELECT * FROM alembic_version;'        # expect e2b9d4c70a15

docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  SELECT count(*) AS impact_tests,
         count(*) FILTER (WHERE impact_family IS NOT NULL) AS backfilled
  FROM missile_impact_tests;"                # backfilled MUST be 0

docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  SELECT count(*) AS projects,
         count(*) FILTER (WHERE requirement_verified_at IS NOT NULL) AS verified
  FROM projects;"                            # verified MUST be 0
```

**Both must be 0.** A non-zero `backfilled` means something inferred an impact classification. A non-zero
`verified` means something asserted that a named person read a named document about a job that ran before
the column existed. Nothing is allowed to do either.

### ⚠️ 2.1 What the requirement gate changes on the day it lands

`e2b9d4c70a15` plus its code make **every Airtable-imported static or cyclic test non-executable until its
design-pressure pair is verified** — contract §3.3, DG14. This is deliberate and it is the point, but it
means the deployment changes operator-visible behaviour rather than only adding fields:

- **a job imported before the deploy, whose stages have not all run, will stop.** `PUT …/start` and
  `POST …/trials` return `409` with the §3.3 reason until somebody verifies the pair;
- **LabOS-only jobs are unaffected** — the operator typed those pressures, and there is no second source;
- **there is no screen for the verification yet** (TC5 screen 2), so until the UI lands it can only be done
  through `POST /projects/{id}/requirement-verification`. **Confirm before the window who will do that, and
  how**, for every open imported job;
- **do not work around it** by verifying on the operator's behalf from the imported value. That records one
  reading as if it were two and removes the only control there is.

List what will be affected before deploying:

```bash
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  SELECT p.id, p.name, p.inward_design_pressure, p.outward_design_pressure
  FROM projects p
  WHERE p.airtable_project_id IS NOT NULL
    AND EXISTS (SELECT 1 FROM static_tests s
                WHERE s.project_id = p.id AND s.finished = false)
  ORDER BY p.id;"
```

`alembic/versions` is bind-mounted from the node's checkout, so the ten files must be **in the node's
working tree** before the container starts. All 38 revisions are tracked in git as of this release — they
were gitignored historically, which is how the repo and the node diverged in the first place.

---

### ⚠️ 2.2 Rig Static Load and Cycles cannot publish a terminal without a declared operator

A rollout limitation of this release, not a defect — but it decides what the Airtable rows look like on day
one, so agree it before the window rather than discovering it from an operator.

`attempts.complete_rig_trial` terminates a rig-posted stage **only if an operator is known**, either from
the callback body or from `test.operator_name` declared at run start. Contract §4.5 requires an operator on a
terminal write and LabOS does not invent one.

Neither source exists today:

- firmware's `Api` class has **no `start_static_test` method at all**, and its `start_cyclic_test` sends
  **no body** — verified against `feature/labos-firmware-p3`, which is itself not deployed;
- `PUT /projects/{id}/static_tests/{idx}/start` is **not among the 25 routes the deployed app serves**, so
  nothing calls it today;
- the operator declaration is **TC5 screen 3**, and the UI does not exist yet.

**What happens without it.** The attempt stays `In Progress`. The `create` phase publishes, so an Airtable
row appears and stays at `In Progress` / `Pending`; the terminal phase is never queued. The refusal is
**visible** in `GET /sync/failures`, not silent — which is the designed behaviour.

**So, before the window, decide which is true for the first rig runs after deployment:**

| Option | Consequence |
|---|---|
| Call `PUT …/{static,cyclic}_tests/{idx}/start` with `{"operator_name": …}` from whatever drives the rig | rows complete normally |
| Accept it until TC5 lands | rig rows sit at `In Progress` in Airtable, and `/sync/failures` shows why. Nothing is lost; the attempt completes when an operator is supplied |

**Do not** default an operator name to get past it. A declared identity nobody declared is exactly what
contract §4's separate reviewer identity exists to prevent, and it would be indistinguishable from a real
one afterwards.

Impact, Forced Entry and ANSI Z97.1 are unaffected: they go through `PUT /test-results/{id}/finish`, which
carries the operator.

## 3. APPLICATION

Order matters. `sync-worker` must not drain a queue against a schema that is still moving.

```bash
# 1. migrator — see §2, run to completion and verified
# 2. API
docker compose up -d --build report-api
docker compose logs -f report-api          # expect "database at: …", "head is: a4f18c2d3b90",
                                           # "Migrations applied successfully", then uvicorn
# 3. worker — only after §4.1 and §4.2 are green, and only once
#    AIRTABLE_SYNC_ENABLED=true
docker compose up -d --build sync-worker
docker compose logs -f sync-worker
```

Expected container state:

| Service | State | Notes |
|---|---|---|
| `db` | up, healthy | `restart: always` |
| `report-api` | up | `restart: always`, port 8000 |
| `sync-worker` | up | `restart: on-failure:5`. **Exit 0 is a valid state** — it means deliberately off (no token, or sync disabled), and the single log line explaining why is the point |
| `mosquitto`, `ui`, `sick_gateway-*` | unchanged | not part of this release |

**Exactly one worker, and it is enforced.** `app/sync/singleton.py` holds a Postgres advisory lock; a second
instance exits rather than racing. Raising `replicas` does not get you two workers, it gets you one worker
and one crash loop.

**Rollback triggers — stop and go to §6 if any of these appear:**

- `alembic_version` is not `a4f18c2d3b90` after §2;
- `backfilled` is not 0;
- `report-api` restarts more than twice;
- `GET /sync/status` reports parked entries that were not parked before;
- any write reaches a table other than `tblnc9SsbXU0C0FWh`;
- the production Airtable base changes in any way.

---

## 4. POST-DEPLOY

### 4.1 The service

```bash
curl -s localhost:8000/openapi.json | jq '.info'
curl -s localhost:8000/sync/status  | jq .
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c 'SELECT * FROM alembic_version;'
```

### 4.2 Airtable, still read-only

```bash
cd src/management_service
python3 -m app.airtable.preflight --env ../../.env
```

**Production must still read 142.** This is the check that turns "we did not touch production" from a claim
into a fact.

### 4.3 The queue

```bash
curl -s localhost:8000/sync/status   | jq '{queued, parked, failed, worker_heartbeat_at}'
curl -s localhost:8000/sync/failures | jq 'length'
```

`worker_heartbeat_at` is the worker's liveness surface — it has no health endpoint of its own, deliberately,
because a worker answering its own health check would report healthy from inside a process whose database
connection had gone.

### 4.4 A bounded smoke path, only if the window allows

Against the **Testing** base, with an obviously synthetic job, exactly as the TA6/TA7 probes do: import,
one manual attempt, finish, verdict, confirm one Raw Data row, confirm the re-send upserts onto the same
record. **Do not** run a probe that seeds hierarchy into a base during a production window without saying so
first — synthetic records are retained, never deleted.

### 4.5 Logs

```bash
docker compose logs --since 30m report-api  | grep -iE 'error|refus|traceback'
docker compose logs --since 30m sync-worker | grep -iE 'error|refus|parked'
```

A `refused to queue …` line is **not** a failure — it is the designed behaviour for a payload the envelope
would not send, and it is visible in `GET /sync/failures` by design.

---

## 5. AIRTABLE PRODUCTION PROMOTION

> ### ⛔ EXPLICIT EXTERNAL APPROVAL REQUIRED — DO NOT RUN DURING PRE-PRODUCTION PREPARATION
>
> This is a **separate** change to a base LabOS does not own, made by the **Airtable team**, after the
> change document has been sent and acknowledged. It is not part of the application deployment above, and
> the application is designed to be correct on either side of it.

**Authoritative field contract:** `../correspondence/LabOS-Airtable-Production-Schema-Requirements-2026-09-11.md`
and its generated CSV `LabOS-Airtable-Production-Schema-Changes-2026-09-11.csv` — 19 ADD, 0 rename, 0 retype,
0 option change, 0 delete; 142 → **161**. Our own execution notes are in
`production-airtable-promotion-2026-09-11.md`, which does **not** restate the field list.

1. Send the two canonical artefacts above. Wait for acknowledgement.
2. `python3 -m app.airtable.apply_schema --out-dir <evidence> --env ../../.env` — **dry run, Testing only.**
   It cannot target production; that refusal is unconditional and has no override. It is run here to confirm
   Testing is still exactly as documented, not to promote anything.
3. The Airtable team applies the 19 additions **in their own base**.
4. **Independent read-back** — a Meta API pull by a different tool from the one that wrote:
   `GET https://api.airtable.com/v0/meta/bases/app0OCunbmuXl7Hc9/tables`. Confirm each field's table, name,
   type, choices and precision, and capture the **production** `fld…` ids. They will **not** match the
   Testing ids.
5. Expected final count: **161**.
6. Re-run `preflight.py`. **Check 2 must be inverted first** — it currently asserts the 19 are *absent* from
   production, which is what makes today's "untouched" a fact. Rewriting it to assert 19 present and 3 still
   absent is part of the promotion.
7. Regenerate `interface-schema.csv` to fill in `field_id_production`.
8. Airtable automations and roll-ups — §6 of the schema requirements document.

---

## 6. ROLLBACK AND REMEDIATION

### 6.1 Application

Roll back to the previous image and commit:

```bash
git -C . checkout <previous-latest-sha>
docker compose up -d --build report-api sync-worker
```

`app/` is **bind-mounted**, so the code that runs is the code in the node's working tree — a rollback is a
checkout plus a restart, and a rebuild is belt and braces rather than the mechanism.

### 6.2 Database — prefer forward, not down

**Do not run `alembic downgrade` on production as a first response.** Two of the ten migrations rewrite
existing rows, and their downgrades are rehearsed but destructive in the sense that matters: they
un-normalise and re-merge evidence.

| Situation | Action |
|---|---|
| The requirement gate is stopping legitimate work and nobody can verify | **Roll the app back**, which removes the gate; the six columns are additive and harmless to an older app. Do **not** patch the gate out of a running deployment, and do not verify from the imported value to get past it |
| App fails, schema fine | Roll back the **app only**. The old code runs against the new schema: all ten migrations are additive from its point of view — new columns and new tables it does not read, plus `labos_test_id` values it does not interpret. `a4f18c2d3b90` in particular adds three nullable columns and one CHECK |
| Migration fails part-way | Alembic is transactional per revision on PostgreSQL, so the failed revision is rolled back and the ones before it are applied. `alembic_version` tells you exactly where it stopped. Fix forward from there; restore from §1.3 only if the state is not one the chain can continue from |
| Data is wrong after a rewriting migration | **Restore §1.3's dump.** That is what it is for. Do not attempt a partial repair on certification evidence |

```bash
# last resort, with the containers stopped
docker compose stop report-api sync-worker
pg_restore -d "$DATABASE_URL" --no-owner --clean --if-exists ~/labos-predeploy-*.dump
```

### 6.3 Partial Airtable promotion

`apply_schema` is **create-only and idempotent**: it has no PATCH or DELETE path at all, and it prints SKIP
for a field that already exists. So a promotion that stops half-way is safe to resume.

1. Capture what succeeded — Meta API read-back, not the tool's own log;
2. **do not delete any field that was created.** Deleting a field in a shared base destroys whatever is in
   it and is never the remedy for a partial change;
3. re-read the schema and re-apply **only the missing** additions;
4. anything ambiguous goes to the Airtable team as a question, not as another write.

### 6.4 App deployed, Airtable not promoted — **the expected intermediate state**

This is safe, and it is the state this release actually ships in.

LabOS points at the **Testing** base, where all 19 fields exist. If an environment were pointed at a base
missing some of them, `contract.py` would mark them `ABSENT` and the envelope would carry their values
through `Complete LabOS JSON Response` as `labos_extra.*` instead of as columns — nothing is lost while the
schema catches up, and the value moves into the real column the moment the field exists and the contract is
updated to say so. The TA6 probe asserts **both** halves of that transition.

### 6.5 Airtable promoted, app rollout fails

Also safe. The 19 additions are **additive and unused**: no existing field is renamed, retyped or removed,
so every view, roll-up and automation that worked before still works. An old LabOS simply never writes the
new columns and they stay blank. Remediation is to finish the app rollout; there is nothing to undo in the
base, and nothing should be deleted from it.

---

## 7. Evidence to file

Into `../evidence/deploy-<date>/`:

- `git log -1` for both repos, and the image id;
- `alembic_version` before and after;
- the row counts from §1.2;
- **`check_open_impact_attempts.py` output — even when it is zero**;
- the restore-rehearsal output from §1.4;
- `check-secrets.sh`, `preflight.py` and `check_register.py`, before and after;
- `GET /sync/status` before and after;
- the `backfilled = 0` query result;
- the completed §1.10 go/no-go table, signed.
