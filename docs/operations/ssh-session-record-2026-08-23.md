# ifet-ssh session record — 2026-08-23

**Operator:** Abdelrahman · **Node touched:** `management` only · **Access:** remote.it proxy, user `pi`
**Purpose:** establish production ground truth for the W2 / P1 database work before finalizing a migration.

> ## Safety posture — read this first
>
> **Every command in this session was read-only.** No file was written, no container was started, stopped,
> restarted or rebuilt, no service was reconfigured, no `sudo` was used, and no database row was inserted,
> updated or deleted. The database was addressed exclusively through `psql` `SELECT` and `\d` (describe), both
> of which only read.
>
> `system-1`, `system-2` and `test` were **not contacted at all.** Only `management` was reached.
>
> Per `CLAUDE.md`, production containers are never restarted or rebuilt to try something out, and the only
> safe git operations on a node are history/index-only. Neither rule was approached: nothing was deployed and
> no git command that writes was run on the node.

---

## 1. Why we connected

W2 / P1 (the append-only attempt schema) was being built against `app/data/models.py` in a local clone, with
a hand-written Alembic migration chained off the revision found in that clone.

The question that triggered this session was whether the repository was a safe stand-in for production. On
this project it has not been before — the July branch reconcile exists because production had drifted from
the repo. Writing a migration against an assumed baseline, for a database holding real certification
evidence, is exactly the case where the assumption should be checked rather than reasoned about.

**It was the right call.** The check invalidated the migration as written. Details in §4.

---

## 2. Session setup

| Step | Command | Result |
|---|---|---|
| Readiness | `bash bin/check-deps.sh` | `READY` — ssh/scp/sshpass present, `credentials.env` mode 600 |
| Proxy freshness | `bash bin/show-session.sh` | `STATUS: fresh` — existing addresses valid, **the user was not asked to re-paste** |

Proxy in use: `new-ifet-mgmt-ssh.at.remote.it:33002`. Host key verified against the pinned
`HostKeyAlias ifet-management`; no key change, no `forget-hostkey` needed.

---

## 3. Commands run, in order

All via `bash bin/ssh-exec.sh management -- '<command>'`.

| # | What was asked | What came back |
|---|---|---|
| 1 | `docker ps` — what is actually running | 7 containers: `report-api`, `db` (postgres:13), `ui` (httpd), `pgadmin`, `mosquitto`, `sick_gateway-1`, `sick_gateway-2` |
| 2 | `SELECT * FROM alembic_version` | **`3a65a83e0463`** |
| 3 | `ls -la alembic/versions` in `report-api` | **29** migration files |
| 4 | `SELECT count(*) FROM test_results` | **623** attempt rows |
| 5 | File-size histogram of the migrations | **28 × 580 bytes**, 1 × 8354 bytes |
| 6 | `cat` the head migration `3a65a83e0463` | `def upgrade(): pass` — an empty no-op, revises `35b3567319e9` |
| 7 | `\d test_results` and `\d projects` | 5 and 6 columns respectively — matching `models.py` exactly |
| 8 | Node repo: branch, `git status --short`, `git diff HEAD -- models.py` | branch `latest` @ `90f9595`, **working tree clean**, `models.py` matches `HEAD` |

Command 8 is the only one that ran `git` on a node. `rev-parse`, `log`, `status` and `diff` are all
read-only; none of them touches the working tree.

---

## 4. What this established

### 4.1 The repo *is* trustworthy for application code

`models.py` on `feature/labos-airtable` is byte-identical to `origin/latest`; the node is clean, on `latest`,
and its copy matches `HEAD`. The live `test_results` and `projects` tables match the model definitions
exactly. **The code being extended is the code production runs**, and the P1 rehearsal seed was accurate.

### 4.2 The repo is *not* trustworthy for migrations — the finding that changed the work

| Believed before | Found |
|---|---|
| Migration baseline is `38f6ba7c1141` | Production is at **`3a65a83e0463`**, which exists nowhere in git |
| Migrations are tracked in git | `**/alembic/versions/*` is **gitignored** — the repo has never tracked one |
| Repo has 1 migration, so production has ~1 | Production has **29** |
| A migration file is an inert repo edit | `versions/` is **bind-mounted** from the node — a file there is live at next restart |

The 29 decompose as **one real migration** (`886f54aa575c`, January 2026) and **28 empty no-ops**, one per
container restart, because `startup.sh` runs `command.revision(autogenerate=True)` at every boot and writes
the result onto the node through the bind mount.

Because those artifacts are gitignored, the divergence was **invisible to git by construction**. That is why
it had gone unnoticed.

### 4.3 The consequence worth escalating

`compose.yaml` bind-mounts `./src/management_service/app`, and `startup.sh` autogenerates-then-upgrades at
boot. Therefore:

> **A `models.py` change merged to `latest` and pulled onto the node will alter the production database schema
> at the next container restart — with no migration review and no human in the loop.**

This is independent of the Airtable integration and predates it. Documented, deliberately **not** changed in
this session: the fix is removing one line from `startup.sh`, which is baked into the image rather than
bind-mounted and therefore needs a rebuild — a scheduled production event.

---

## 5. What changed as a result

Nothing on any node. All changes were local, committed to integration branches, and **not deployed**:

- The P1 migration's `down_revision` corrected from `38f6ba7c1141` to **`3a65a83e0463`**.
- `.gitignore` narrowed to `**/alembic/versions/*_auto_generated_migration.py`, so hand-written migrations can
  be tracked and delivered at all — previously they could not.
- `tests/rehearse_p1_migration.py` rebuilt to construct the **production** pre-migration schema from the
  `\d` output above, rather than from `models.py`.
- The safety of the deploy path was then verified in Alembic's own source rather than assumed: autogenerate
  refuses to run when the database is behind file-head, so it raises, `startup.sh` catches it, and
  `upgrade(head)` applies the real migration cleanly. Self-sequencing.

---

## 6. What was deliberately not done

- **No deployment.** No merge to `latest`, no `git pull` on the node, no container restart.
- **No writes to the production database.** The P1 migration has *not* been applied; the 623 attempt rows are
  untouched.
- **No contact with `system-1`, `system-2` or `test`.**
- **No `sudo`** anywhere, local or remote.

---

## 7. Reproducing this check

```bash
cd /home/gad/.claude/skills/ifet-ssh
bash bin/check-deps.sh && bash bin/show-session.sh

bash bin/ssh-exec.sh management -- '
  docker ps --format "{{.Names}}\t{{.Image}}";
  docker exec ifet-management-db-1 sh -c "psql -U \$POSTGRES_USER -d \$POSTGRES_DB -tAc \"SELECT * FROM alembic_version;\"";
  docker exec ifet-management-db-1 sh -c "psql -U \$POSTGRES_USER -d \$POSTGRES_DB -c \"\\d test_results\"";
  docker exec ifet-management-report-api-1 sh -c "ls alembic/versions/*.py | wc -l";
'
```

Re-run it before any future schema change. The number of no-op migrations will have grown by one for every
restart since — which is itself the quickest way to confirm the mechanism is still in place.

---

## 8. Related records

| For | Read |
|---|---|
| The full W2 / P1 record and the migration mechanism | `docs/labos-airtable/evidence/p1-schema-and-migration-mechanism-2026-08-23.md` |
| The Airtable-side probe of the same day (HTTPS, not SSH) | `docs/labos-airtable/evidence/live-probe-findings-2026-08-23.md` |
| Where the integration stands overall | `docs/labos-airtable/status/readiness-2026-08-23.md` |
| Secret handling and the gated deploy runbook | `ifet-management/deployment/SECRETS.md` |
