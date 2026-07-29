# Branch Reconcile Plan — LabOS ↔ Airtable pre-W1

**Author:** Abdelrahman · **Date:** 2026-07-24 · **Updated:** 2026-07-29 · **Status:** 🔒 **CLOSED** — Steps A–D done and published; §5 attribution rewrite closed as **WON'T DO**. Only Step E/F (deliberate node sync + deploy) remain, intentionally deferred to deploy time.
**Context:** Prerequisite for the LabOS↔Airtable integration (Epic IFET-32). Reconcile the plan baseline
to what production actually runs, then cut integration feature branches — **without disturbing the live nodes.**

**Progress:** ✅ Baselines captured (§1) · ✅ Container audit — no drift (§1a) · ✅ Worktrees cleaned in place, commits authored *gad* (§1b) · ✅ Published + unified + branches cut (§3, 2026-07-26) · ⏸ Step E/F deferred by design (folds into the next deliberate deploy) · 🔒 **Attribution cleanup CLOSED — history stays as-is; forward-only rule adopted (§5)**.

> **Closing decision (2026-07-29).** No history rewrite. Existing Claude-authored commits and
> `Co-Authored-By` trailers **stay in the published history** — the force-push risk to other contributors
> (Amr ~95 commits, Hammad, IFETINC) is not worth a cosmetic contributor-graph change, and every SHA cited
> in this doc, Notion, and project memory stays valid. Instead the rule is **forward-only**: every commit
> from here on is authored `gad <abdulrahmanashraf.gad@gmail.com>` with **no Claude trailer and no
> assistant co-author line**. Enforced in git config (local + global `user.name = gad`, done 2026-07-29).
> Nothing further to execute — the reconcile is finished.

> **Safety principle:** branch reconcile is git/repo housekeeping, NOT a production change. All git work
> happens in your own clones / on GitHub. The running nodes are never checked out, stashed, or restarted.
> They keep serving their deployed images until a *deliberate* rebuild-and-deploy later (see
> production-deploy-caution). The only hazard is **device-local uncommitted edits** — capture them before branching.

---

## 0. Safety review — VERDICT: ✅ code-change-safe (2026-07-24, verified read-only)

The reconcile was stress-tested against every path that could alter a running node. It changes nothing on the deployed nodes. Evidence, not assertion:

**Decisive finding — NO auto-deploy exists (verified on all 3 prod nodes):** no cron / systemd timer / Watchtower / updater container pulls git or rebuilds on push. Deploy is **manual only** (human SSHes in, pulls, rebuilds). So committing/pushing to origin `dev`/`latest` **cannot silently reach production.** The "zero-interruption update" is a manual op. system-2's 05:30 cron is a `docker compose restart` (existing images, pulls no code). All 3 HEADs (`5775e87`, `3642711`) are present on origin → tagging succeeds.

**Guardrails that make the path safe** (refined after execution — the real distinction is *file-rewriting* vs *history-only* git ops):
1. **On a node, the ONLY safe git writes are history/index ops that never rewrite working files:** `git add`, `git commit`, `git update-index --skip-worktree`. These are how §1b captured the worktrees clean **without touching a single live file** (proven: every config sha identical before+after, containers not restarted). Cross-node merges, tags, and the feature-branch cut still happen **off-node in a clone**.
2. **NEVER run on a node:** `git checkout`, `reset --hard/--mixed`, `stash pop/apply`, `clean`, `pull`, `merge`. These rewrite working-tree files → would revert the **live bind-mounted config** the running container reads (and sys-2's 05:30 restart would then bake the revert in). The reconcile needs none of them on a node.
3. Any read-only patch capture writes to `/tmp` only.
4. Bucket-C secrets/machine-state never enter git → no secret leak, no cross-node config bleed at a future deploy.

**Residual caveats:**
- **Root crontab on system-1 + management unread** (sudo password needed; only system-2 had passwordless sudo). `/etc/crontab` + `/etc/cron.d` are OS-stock and no deploy script exists for a hidden root cron to call — low risk, not 100% ruled out. Close it with a one-line read-only root-crontab check when the sudo password is available.
- **First real risk is the eventual deliberate DEPLOY, not the reconcile:** pulling the committed `new_sensor.py` onto a node holding an identical *uncommitted* copy makes `git pull` refuse ("local changes would be overwritten"). Fix at deploy time (content is identical): `git checkout -- new_sensor.py` then pull. Deliberate step, gated.

---

## 1. Captured production baseline (read-only, 2026-07-24)

Reached 3 of 4 nodes. All diffs were **unstaged** (staged diff empty everywhere). No changes made to any node.

| Node | Repo | Branch @ HEAD | Dirty tracked files | Notes |
|---|---|---|---|---|
| **management** (`ManIfet`) | `/home/labadm/ifet-management` | `latest` @ `5775e87` | `compose.yaml`, `config/fstab`, `deployment/config/config.json`, `src/ifet_ui_react/config.json` | + untracked `reconf.sh`, 1 `.bak`. fstab shows a reflash (UUID change). |
| **system-1** (`ifet4`) | `/home/labadm/ifet-firmware` | `dev` @ `3642711` | `deployment/config/config1-site-b.json`, `config1.json`, `docker-compose-1.yaml`, `src/serial_service/sensors_handler/new_sensor.py` | **2 git stashes present.** + 3 `.bak`, untracked `deployment/split-serial-temp/`. |
| **system-2** (`Sys2`) | `/home/labadm/ifet-firmware` | `dev` @ `3642711` | `deployment/config/config2.json`, `src/serial_service/sensors_handler/new_sensor.py`, `src/serial_service/vfd_handler/vfd_node.py` | + 7 `config2.json.bak.*`. |
| **test** | — | **DISCONNECTED — out of scope** | — | Non-prod test rig, currently offline (user confirmed 2026-07-24). Not a production integration target; reconcile proceeds with the 3 nodes above. Capture opportunistically if/when it returns. |

**Repo topology reminder:** management repo is `github.com/amr-kasem/ifet-management`; its **default branch `main` is stale (Oct 2024)** while production runs `latest`. Local firmware working copy is on `feature/vfd-tcpip-support` @ `6438402` (AHEAD of prod `dev` @ `3642711`).

### 1a. Container audit — running == host tree (read-only, 2026-07-24)
Verified the RUNNING CONTAINERS against the host tree (sha256 in-container vs host). **No drift on any node** — the uncommitted host edits ARE what's executing in production, so the host tree is the accurate baseline (git HEAD is not). Mechanics:
- **Code is BAKED into images** (`new_sensor.py`, `vfd_node.py`): images rebuilt 2026-07-07 (sys-1) / 2026-07-09 (sys-2) right after the edits; in-container sha == host. Running code = uncommitted host code.
- **Config is BIND-MOUNTED** (`config1.json`/`config2.json`→`/app/config.json`; mgmt `config.json`→htdocs; report-api `app/`→`/app/app`): live by definition, shas match.
- system-1 serial device is live `/dev/ttyUSB0`; system-2 has sensor4/5 + PSF live; mgmt `SICK_API_HOST` env matches the swapped IPs.
- **Deploy mechanism inferred = rebuild image from tree.** Because code is baked, the running container is insulated from the host working tree → the "`git pull` refusal" risk is **build-time only, not runtime**. Deploy = rebuild from a clean checkout; container keeps its baked image until a deliberate rebuild.
- **Residual (mgmt):** only the `compose.yaml` `SICK_API_HOST` swap was verified (it's the whole captured diff); any *other* future compose change applies only on next `compose up`.

### 1b. Worktrees cleaned in place — ✅ DONE (2026-07-24, commits LOCAL, not pushed)
All 3 nodes now have clean worktrees. Each node's real running state was committed **in place** via history-only ops (§0 guardrail 1) — zero change to live files, containers not restarted (uptime unchanged, all config shas identical before+after). Every commit **authored + committed as `gad`** (`abdulrahmanashraf.gad@gmail.com`), no Claude trailer.

| Node | Commit | Branch | What was committed | Held back (not committed) |
|---|---|---|---|---|
| **system-1** | `176ac74` | `dev` | `new_sensor.py`, `config1.json`, `config1-site-b.json`, `docker-compose-1.yaml` (`git add -A`; no secrets in firmware) | — (2 stashes left intact) |
| **system-2** | `5048d9a` | `dev` | `new_sensor.py`, `vfd_node.py`, `config2.json` (`git add -A`) | — |
| **management** | `90f9595` | `latest` | `deployment/config/config.json`, `src/ifet_ui_react/config.json` (selective `git add`) | `compose.yaml` + `config/fstab` → `git update-index --skip-worktree` (live on disk, hidden, uncommitted; reversible via `--no-skip-worktree`) |

- Node git identities were **Hammad** (sys-1) / **device2** (sys-2) / **unset** (mgmt) → `gad` supplied explicitly per commit.
- Backups on each node: `~/configN-live-backup-2026-07-24.json` (firmware), `~/mgmt-backup-2026-07-24/` (paths preserved). Cruft parked in `~/wt-cruft-2026-07-24/`.
- mgmt secret scan: only empty `"password": ""` fields in the committed configs — no real secrets. (Watch item: that browser-readable config must never hold the Airtable token.)

---

## 2. Delta classification (the actual "reconcile")

**Decision 2026-07-24:** the repo becomes a faithful ground-truth mirror of the running nodes — commit **code + per-node non-secret config**; externalize secrets (P0); gitignore machine-instance state + cruft. *(Corrects this doc's earlier "keep all config local" line: since each node bind-mounts only its OWN config file, committing per-node config to its own tracked file causes no cross-node bleed.)*

### A. Real code → commit ONCE to the firmware baseline branch (shared, portable)
Genuine behavior changes running in prod but not in git. Verified baked into the running images (Section 1a).
- **`src/serial_service/sensors_handler/new_sensor.py`** — per-sensor `scale` (default 1) + `unit` (default PSI); `read()` multiplies by scale, logs unit. **Byte-for-byte identical on system-1 and system-2** → commit once.
- **`src/serial_service/vfd_handler/vfd_node.py`** (system-2 only) — adds one feedback log line. Commit with the above.

### B. Per-node NON-SECRET config → commit to each node's OWN tracked file (this is what makes the repo mirror ground truth; no bleed — each node bind-mounts only its own file)
- firmware: `deployment/config/config1.json`, `config1-site-b.json` (system-1); `config2.json` w/ sensor4/5 + PSI→PSF `scale:144`/`unit:PSF` (system-2).
- firmware: `docker-compose-1.yaml` (system-1) serial path `/dev/ttyACM0`→`/dev/ttyUSB0` — host-specific but no secrets, and it's system-1's own tracked compose → commit.
- management: `deployment/config/config.json`, `src/ifet_ui_react/config.json` — browser-read runtime config; confirmed NOT holding secrets (must stay that way — never put the Airtable token here) → commit.

### C. Externalize or gitignore → NEVER commit
- **Secrets:** management `compose.yaml` — plaintext DB creds today, `AIRTABLE_TOKEN` soon. Externalize to a gitignored `.env` / secret store as part of **P0 (Ref 42)**. NB: its `SICK_API_HOST` swap is captured in the Step-0 patch and gets handled when compose is templated in P0.
- **Machine-instance:** management `config/fstab` (reflash partition UUIDs — breaks on other media) → gitignore / never commit.
- **Cruft:** `*.bak.*` (all nodes), `deployment/split-serial-temp/` (system-1), `reconf.sh` (management) → add to `.gitignore`.
- **system-1's 2 git stashes** ("WIP on merged: e87e09a added docs") — INSPECT (`git stash show -p`) before dropping; do not blindly clear.

---

## 3. Execution status & remaining steps

### ✅ DONE — Steps A–D executed 2026-07-26, all off-node, nodes verified untouched

- **Capture** (§1) + **container audit** (§1a) + **worktrees cleaned in place** (§1b) — all 3 nodes clean, commits local (`176ac74` sys-1, `5048d9a` sys-2 on `dev`; `90f9595` mgmt on `latest`), authored *gad*. The in-place commits ARE the ground-truth capture — no separate patch step needed.

**Step A — Publish each node's reconcile commit — ✅ DONE (via bundle, not node push).**
The original plan had each node `git push` to origin. That was **replaced with a strictly safer mechanism**: on each node, `git bundle create /tmp/<node>.bundle 3642711..dev` (reads git objects, writes only to `/tmp`, makes **zero** network writes from a production node and never touches the working tree), then `scp` the bundle off and `git fetch` it into an off-node clone. This honours §3's "all off-node, in a clone" intent better than pushing from prod did.
```
reconcile/sys1-2026-07-24 -> 176ac74
reconcile/sys2-2026-07-24 -> 5048d9a
reconcile/mgmt-2026-07-24 -> 90f9595
```

**Step B — Baseline tags — ✅ DONE.** Annotated tags, verified to dereference to the right commits:
```
prod-fw-2026-07-24   -> 3642711   (ifet-firmware)
prod-mgmt-2026-07-24 -> 5775e87   (ifet-management)
```

**Step C — Firmware unification — ✅ DONE.** §2A's prediction held exactly: `new_sensor.py` is blob-identical on both nodes (`5a0596ae`), so `reconcile/sys1` fast-forwarded and `reconcile/sys2` merged with that file **auto-resolving to a no-op** (it doesn't even appear in the merge stat). Result verified **blob-for-blob against both nodes' running content** — all 7 prod-critical paths matched.
> **Decision (resolved 2026-07-26):** land on **`dev`, then merge forward** into `feature/vfd-tcpip-support`. Rationale: node HEADs are on `dev`, so `dev` must mirror prod for Step E to stay clean; `feature/vfd-tcpip-support` was strictly *ahead* of `dev` (no divergence) but rewrote the same config files, so conflict resolution belongs on the feature branch.

**Step D — Feature branches cut — ✅ DONE.** Final published state:

| Repo | Ref | Commit |
|---|---|---|
| firmware | `dev` | `dfacc6a` |
| firmware | `feature/labos-firmware-p3` | `dfacc6a` |
| firmware | `feature/vfd-tcpip-support` | `cc1a5ef` (dev merged forward) |
| management | `latest` | `90f9595` |
| management | `feature/labos-airtable` | `90f9595` |

**⚠️ Merge-forward finding — stale VFD address on the feature branch.** `feature/vfd-tcpip-support` carried `config1.json` VFD `"address": "5"`, but production answers on **12** (the 2026-07-07 bring-up finding). The merge auto-resolved in favour of production's `12`; **verified 12 in both `config1.json` and `config1-site-b.json` post-merge.** Had this been merged the other direction, the VFD would have gone silent on the next deploy. The single manual conflict (`config1-site-b.json`) was resolved as *feature-branch schema* (`transport`/`dry_run`/`timeout`/`tcp`) + *production's operational* `"frequency": 3` (site-b runs 3; `config1.json` runs 20).

### ⏸ REMAINING — deliberately deferred

**Step E — (later, deliberate) sync the nodes to origin without touching live files:** `git fetch && git reset --mixed origin/<branch>` — updates HEAD/index only, never rewrites the working tree. **NEVER `reset --hard`.** (mgmt's skip-worktree on `compose.yaml`/`fstab` persists.)

> **Correction to the earlier "the tree stays clean" claim.** That was true when `dev` was exactly the unified commit. `dev` has since gained two commits (scanner hardening, gitignore), and each node's worktree only ever held *its own* node's files. So `reset --mixed origin/dev` now leaves each node reporting a few modified files:
> - **system-1:** `.gitignore`, `tools/scanner.py`, `deployment/config/config2.json`, `src/serial_service/vfd_handler/vfd_node.py`
> - **system-2:** `.gitignore`, `tools/scanner.py`, `deployment/config/config1.json`, `config1-site-b.json`, `docker-compose-1.yaml`
>
> **This is harmless and expected** — none of those are live for that node (sys-1 bind-mounts `config1*`, sys-2 bind-mounts `config2`), and `reset --mixed` rewrites no files. **Verified: every node's OWN live config matches `origin/dev` byte-for-byte**, so each node's live files show clean. The dirty entries are just the other node's files reading as "reverse-diff" until a real deploy checks them out.

#### Step E runbook — reaching a clean worktree + clean repo on a node

Ordered, per node. Every command is refs/index-only or provably non-live; none rewrites the live bind-mounted config, none restarts a container.

```
git fetch --prune origin          # refs only. Prunes stale remote-tracking refs
git reset --mixed origin/dev      # HEAD + index only. NEVER --hard
git status                        # expect the short list below
git checkout -- <listed files>    # ONLY after confirming none is this node's live mount
git gc --prune=now                # optional: drop now-unreachable old objects
```

> **Do NOT `git pull` at step 2.** After a history rewrite the local branch has *diverged*, so `pull` would attempt a merge of the old and rewritten lines — rewriting working files. `fetch` + `reset --mixed` is the only safe path.

Expected `git status` after `reset --mixed` (verified; **the attribution rewrite does not change these lists**):

| Node | Shows as modified | Why safe to `checkout --` |
|---|---|---|
| **system-1** | `.gitignore`, `tools/scanner.py`, `deployment/config/config2.json`, `src/serial_service/vfd_handler/vfd_node.py` | sys-1 mounts `config1*`, so `config2.json` is inert for it; `scanner.py` is a manual tool; `.gitignore` is git metadata; `vfd_node.py` is **baked into the image** so the on-disk file cannot affect the running container |
| **system-2** | `.gitignore`, `tools/scanner.py`, `deployment/config/config1.json`, `config1-site-b.json`, `docker-compose-1.yaml` | sys-2 mounts `config2.json`, so all the `config1*` / compose-1 files are inert for it |

**The invariant that makes this safe:** each node's OWN live bind-mounted config already matches `dev` byte-for-byte (verified by sha256 against the live devices), so it never appears in the dirty list. Everything that *does* appear is the other node's file or non-runtime tooling.

Verify after: live config sha256 unchanged, `git status` clean, containers' uptime unchanged.

**Node-local leftovers (decision, not yet actioned).** `git fetch --prune` clears system-1's stale `origin/claude/dreamy-cerf-SSEGU`, `origin/claude/gracious-curie-2mbqK`, `origin/claude/happy-pascal-PEgpL` plus `origin/merged`, `origin/release*`, `origin/staging` on both nodes. Additionally both nodes carry local branches `backup` and `merged` (system-1 also `hammad-dev`) that hold old history. These are **node-local only — they have zero effect on GitHub's contributor graph.** Inspect before deleting; `backup` looks like a deliberate safety net.

**Note:** once a node resets onto the rewritten `origin/dev` (if §5 is executed), its `dev` branch history contains no Claude commits; the old ones remain only as unreachable objects until `git gc`.

**Step F — Nodes stay untouched until a deliberate deploy.** Deploy per production-deploy-caution: rebuild image from a clean checkout, explicit per-node, no container hot-patching.

#### Working practice going forward (prevents the drift that caused this reconcile)

The root cause was editing code/config directly on the devices and leaving it uncommitted, so images got built from dirty trees and git HEAD stopped being the truth. The loop that avoids repeating it:

1. **Branch off `dev` in a clone** — never edit on the device.
2. **Commit + push** (PR if review is wanted).
3. **Deploy deliberately:** on the node `git fetch --prune && git reset --mixed origin/dev`, confirm clean, then rebuild the image. No `docker cp` hot-patching.
4. **Per-node config lives in the repo** as that node's own tracked file (§2B). Host-specific values like `/dev/ttyUSB0` belong in that node's own compose file.
5. **Secrets never in git** — gitignored `.env` / secret store (P0, Ref 42).
6. **Treat a dirty node worktree as an incident signal** — it means undocumented drift; capture it rather than letting it accumulate.

### Node-safety evidence (verified after every mutating step, 2026-07-26)
Only two op classes ever ran on a node: `git bundle create` / `git show` (read-only, `/tmp`-only writes) and `git stash drop` (history-only). Confirmed after the fact:
- HEADs unchanged: sys-1 `176ac74`, sys-2 `5048d9a`, mgmt `90f9595`.
- All 3 worktrees report **0 modified files**; mgmt `skip-worktree` on `compose.yaml`/`fstab` still in force.
- Config sha256 **identical before and after** the stash drop (`config1.json`, `config1-site-b.json`, `docker-compose-1.yaml`).
- Containers never restarted: sys-1 `Up 4 days`, mgmt `Up 2 weeks`; sys-2 `Up 11 hours` = its own 05:30 EDT cron, not us.

---

## 4. Decisions
- [x] **Claude attribution cleanup — CLOSED 2026-07-29 as WON'T DO, see §5.** The rewrite was built and verified but is **not** being pushed, ever. Past history keeps its Claude authorship and `Co-Authored-By` trailers; **all future commits are `gad`, with no assistant attribution of any kind.** Rationale: no force-push means no contributor disruption and no SHA churn across this doc / Notion / memory; the graph cosmetics aren't worth it.
- [ ] **Management default branch:** promote `latest` → default on GitHub (so nobody branches off stale `main`), or just document that `latest` is the live line. **Still open** — this is a GitHub repo-admin setting on `amr-kasem/ifet-management`, deliberately not changed unilaterally. `main` remains at `12fe528` (Oct 2024) while `latest` is at `90f9595`.
- [x] **Firmware baseline branch (decided 2026-07-26):** `dev`, then merge forward into `feature/vfd-tcpip-support`. See Step C.
- [x] **system-1 stashes (resolved 2026-07-26):** both inspected, then dropped after salvaging one file.
  - `stash@{0}` — **superseded, dropped.** It mapped `/dev/ttyUSB0:/dev/ttyACM0`; the committed live compose uses `/dev/ttyUSB0:/dev/ttyUSB0`, i.e. the stash was an *earlier* approach to the same problem.
  - `stash@{1}` — **salvaged `tools/scanner.py`, dropped the rest.** The scanner rewrite is genuinely better (explicit `MODE_RTU`, probes register 0 instead of 1, treats `InvalidResponseError` as device-present, 50 ms RS485 inter-address pacing, optional baudrate arg) and is almost certainly the tool that located the VFD at address 12. Committed as `01775c3`; salvage verified **lossless** (sha256 `8ea6dbf5…` identical in the node's stash, the extract, and the pushed blob). Discarded remainder was superseded debug state: old `192.168.1.174` network for MQTT/API, sensors flipped `active: false`, `only_sensor.py` scratch edits.
  - Both patches archived **before** dropping, in two places: `~/wt-cruft-2026-07-24/stash{0,1}-*.patch` on system-1 and locally.
- [x] **Config-in-repo strategy (decided 2026-07-24):** commit code + per-node non-secret config → repo mirrors ground truth; secrets externalized (P0/Ref 42); machine-instance + cruft gitignored.
- [x] **Bucket-C cleanup (done 2026-07-26, `dfacc6a`):** `.gitignore` now covers `*.bak` / `*.bak.*`, `deployment/config/backups/`, `deployment/split-serial-temp/`, and `.venv/` `venv/` `venve/` (untracked virtualenvs found on system-1). Verified **no tracked file** is newly matched. The `.bak` files and `split-serial-temp/` were already gone from both node worktrees (parked in `~/wt-cruft-2026-07-24/` during §1b). Still open, folds into **P0**: externalize management `compose.yaml` secrets; decide on `reconf.sh`.
- [x] **test node:** disconnected + non-prod → out of scope. Reconcile proceeds with the 3 production nodes. Capture opportunistically if it returns. *(Re-confirmed offline 2026-07-26: connection refused.)*

### Secret-hygiene check (re-verified 2026-07-26 at push time)
Both pushed reconcile commits were scanned before publishing. Firmware: no secret-ish added lines. Management: the only credential-shaped fields in either browser-readable config are `mqtt.password = ''` (empty) in both `deployment/config/config.json` and `src/ifet_ui_react/config.json` — matching §1b. **Watch item stands: the Airtable token must never land in these two files** — they are served to the browser.

---

## 5. 🔒 CLOSED — Claude attribution cleanup: WON'T DO (decided 2026-07-29)

**Final status: closed, not executed. `origin` was never force-pushed and will not be.** The rewrite was
fully built and verified in a throwaway clone (evidence retained below for the record), then **abandoned by
decision**. The analysis below is kept as an audit trail, *not* as a runbook — **do not execute it.**

**Why closed rather than executed**
- A force-push across 5 branches + a tag diverges every other contributor's clone (Amr ~95 commits, Hammad 7,
  IFETINC 4) for a purely cosmetic contributor-graph change. Coordination cost > benefit.
- It would invalidate every SHA cited in this doc, the Notion *Branch Reconcile — Execution Record*, and
  project memory (`dfacc6a`, `176ac74`, `5048d9a`, `3642711`, …) — churn with no functional gain.
- The nodes' own clones would keep the old history regardless (§ "Note (accepted…)"), so the result would be
  inconsistent anyway.

**What replaces it — the forward-only attribution rule (in force from 2026-07-29)**
1. Author/committer for all new work: **`gad <abdulrahmanashraf.gad@gmail.com>`**. Set in git config
   (`--local` and `--global` `user.name = gad`) so it applies without per-commit flags.
2. **No `Co-Authored-By: Claude …` trailer, no `Generated with Claude Code` line, no `claude.ai/code`
   session links** in any new commit message, PR body, or tag. Assistant-written changes are committed under
   the repo owner's name like any other tool output.
3. Applies to both repos (`ifet-firmware`, `ifet-management`) and to the on-node commits (node git identities
   are `Hammad`/`device2`/unset → keep supplying `gad` explicitly, as §1b already did).
4. Historical commits are **left alone**. The 13 Claude-authored commits, 4 trailers, and 5 session links
   stay in published history as a fact of the record.

**Goal that was abandoned:** removing Claude from the repo's contributor graph. Not worth the blast radius.

### What's actually in the history

| Category | Count | Disposition |
|---|---|---|
| Commits authored **and** committed by `Claude <noreply@anthropic.com>` | 13 | Re-attribute author + committer → `gad` |
| Commits by `device2` / `Amr Kasem` carrying `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` | 4 | **Keep original author**, strip only the trailer |
| `https://claude.ai/code/session_01Apt9Ge…` links in commit bodies | 5 | Strip (decided — pure noise) |
| Merge subjects naming real branches / PR #5 (`claude/happy-pascal-PEgpL`, `claude/gracious-curie-2mbqK`) | 3 | **KEEP (decided)** — those branches and PR genuinely existed; rewriting them would falsify history and break the PR #5 reference |

- **Affected refs:** `dev`, `feature/vfd-tcpip-support`, `feature/labos-firmware-p3`, `reconcile/sys1-2026-07-24`, `reconcile/sys2-2026-07-24`, and tag `prod-fw-2026-07-24`.
- **NOT affected (verified):** `hammad-dev` and all 8 `archive/*` tags contain zero Claude authorship or trailers — so no stale ref would keep Claude reachable after a rewrite. This is what makes the cleanup viable at all.
- No tracked `CLAUDE.md` / `.claude/` files exist in the repo.

### Verification already completed (in a throwaway clone)

- **Zero content change.** Full tree diff old↔new on `dev` is **empty**; every branch's tip tree hash and commit count are unchanged (dev 143, vfd 146, p3 143, sys1/sys2 139, hammad-dev 102).
- **Authorship clean:** 0 Claude/anthropic in any author or committer field across all rewritten refs.
- **Other authors preserved:** Amr Kasem's ~95, Hammad's 7, IFETINC's 4 all intact. `gad` on `dev` goes 5 → 18 (absorbing the 13).
- **Dates preserved** (author and committer).
- **Live-device content preserved — verified against the running fleet by sha256:** system-1 `config1.json` `b86b98d6…`, `config1-site-b.json` `ac0eb4c9…`, `docker-compose-1.yaml` `7e7b3adb…`; system-2 `config2.json` `fee3b244…`, `vfd_node.py` `5d5554e8…`; `new_sensor.py` `275d2b2e…` on both. Each matches the rewritten history byte-for-byte.

### ⛔ Archived recipe — DO NOT RUN (kept only to document what was evaluated)

```
git clone https://github.com/amr-kasem/ifet-firmware.git rw && cd rw
git fetch origin --tags
for b in dev hammad-dev feature/vfd-tcpip-support feature/labos-firmware-p3 \
         reconcile/sys1-2026-07-24 reconcile/sys2-2026-07-24; do
  git branch -f "$b" "origin/$b"; done

FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f --tag-name-filter cat \
 --env-filter '
  case "$GIT_AUTHOR_EMAIL"    in *anthropic.com) GIT_AUTHOR_NAME=gad;    GIT_AUTHOR_EMAIL=abdulrahmanashraf.gad@gmail.com;;    esac
  case "$GIT_COMMITTER_EMAIL" in *anthropic.com) GIT_COMMITTER_NAME=gad; GIT_COMMITTER_EMAIL=abdulrahmanashraf.gad@gmail.com;; esac
  export GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL' \
 --msg-filter '
  grep -viE "^[[:space:]]*co-authored-by:[[:space:]]*claude" \
  | grep -viE "^[[:space:]]*co-authored-by:.*anthropic\.com" \
  | grep -viE "https://claude\.ai/code/session" | cat -s' -- --all
```
*(`git-filter-repo` is not installed on this machine; built-in `filter-branch` was used. The `--msg-filter` above already includes the agreed session-link strip.)*

### SHA map — **only valid while the refs are at these tips**

| Ref | Current (pre-rewrite) | After rewrite |
|---|---|---|
| `dev` | `dfacc6a` | `5506412` |
| `feature/vfd-tcpip-support` | `cc1a5ef` | `eba324f` |
| `feature/labos-firmware-p3` | `dfacc6a` | `5506412` |
| `reconcile/sys1-2026-07-24` | `176ac74` | `4b702f1` |
| `reconcile/sys2-2026-07-24` | `5048d9a` | `64df2b8` |
| tag `prod-fw-2026-07-24` → | `3642711` | `316246a` |

> **If any of those refs move before this is executed, regenerate the map** — the rewrite must be rebuilt from the then-current tips.

### ⛔ Archived procedure — superseded by the WON'T-DO decision

*(Retained for the record. If this is ever revisited, the map above must be regenerated and step 1 is
non-negotiable.)*

1. **Coordinate first — this is the real risk, and the reason it was deferred, then dropped.** The repo has other contributors (Amr Kasem ~95 commits, Hammad 7, IFETINC 4). A force-push doesn't destroy their clones, but their `dev` diverges: they must `git fetch` + reset (or re-clone), and rebase any unpushed local work. Tell them before, not after.
2. **Back up locally, NOT on origin:** `git bundle create ~/ifet-fw-pre-rewrite-<date>.bundle --all`.
   > ⚠️ **Do not push a `backup/*` branch or tag to origin.** Any ref on origin that reaches the old commits keeps the Claude-authored commits reachable, which would very likely keep Claude in the contributor graph — defeating the whole point. Reversibility must live in a local bundle.
3. Force-push the 5 branches and re-point `prod-fw-2026-07-24`. Leave `hammad-dev` and `archive/*` alone.
4. **Re-point all documentation** — this doc, the Notion *Branch Reconcile — Execution Record*, and the project memory all cite `dfacc6a` / `176ac74` / `5048d9a` / `3642711`. Every one of those SHAs changes.
5. **Re-verify the fleet** (expected: no change at all) — HEADs, `0` modified files, container uptimes.

### Why the fleet is not at risk

A force-push to `origin` **cannot reach the devices**: there is no auto-deploy anywhere on the fleet (§0 — no cron, no systemd timer, no Watchtower, no updater container), and the containers run **baked images**, so git on a node is inert with respect to what executes. The nodes each hold a complete independent clone *and* their working trees (both verified `0` modified). The only effect is bookkeeping: their local HEADs (`176ac74` / `5048d9a`) would stop matching an origin ref, resolved later at Step E against byte-identical content.

**Note (accepted, not a blocker):** this cleanup does **not** rewrite the nodes' own local git history — they keep the old commits in their clones. Making those match would mean rewriting git on production boxes, which is explicitly **not** recommended. Leave the nodes alone; a later deliberate Step E / deploy brings them into line.

### Sub-decisions — all resolved by the WON'T-DO close

- [x] **Go/no-go on the force-push → NO.** Never executing; `origin` history is final.
- [x] **Scope → not applicable.** Nothing rewritten on any ref.
- [x] **The 2 malformed `gad <gad>` commits** (`122e0ae` 2026-04-26, `373ea0a` 2026-04-23) — **left as-is.** They fall under the same no-rewrite decision; the broken email means GitHub can't link them to the account, which is accepted. New commits use the correct identity, so the problem does not recur.
- [x] **GitHub-side residue → accepted.** Claude stays in the Contributors sidebar and on PR #5. Cosmetic only; no action.

**Nothing in §5 remains open. The reconcile plan as a whole is closed.**

---

## 6. Next up (LabOS↔Airtable, Epic IFET-32)

**Live as of 2026-07-29:** the Airtable team's schema doc arrived and is reviewed —
`docs/labos-airtable-team-doc-review-2026-07-29.md` (review + reply) and
`docs/labos-airtable-write-contract-v0.2.md` (the write spec). P0/Ref 42 is now **urgent**, not just first:
a rotated `AIRTABLE_TOKEN` is about to exist and must land in a gitignored `.env`, never in the two
browser-readable management configs.

The reconcile is done; the integration branches exist and are based on real production state:
- **`feature/labos-airtable`** (management, off `latest`) — where the integration itself lives.
- **`feature/labos-firmware-p3`** (firmware, off `dev`) — off-dashboard P3 work.
- **P0 (Ref 42)** is the first real task and is now the only thing standing between here and W1: externalize the management `compose.yaml` secrets to a gitignored `.env`/secret store *before* an `AIRTABLE_TOKEN` exists to leak.
- Optional close-out from §0: the one-line read-only root-crontab check on system-1 + management, whenever the sudo password is at hand.

---
*Baselines captured read-only 2026-07-24 via ifet-ssh; worktrees then cleaned in place (§1b) using history-only
git ops that never rewrite working files — live configs and running containers verified untouched. Steps A–D
executed 2026-07-26 entirely off-node in throwaway clones, with node state re-verified after every mutating
step (see §3 node-safety evidence). Nodes are synced only later, deliberately, via `reset --mixed` (never `--hard`).*
