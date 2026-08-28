# ifet-firmware — project instructions

Firmware for the IFET fenestration test lab. One Python codebase per Raspberry Pi rig; three MQTT services:
`state_machine` (test sequencer), `serial_service` (sensors + VFD over Modbus), `vfd_handler`.

**Read `docs/INDEX.md` first.** It maps every document in this repo, in `ifet-management`, and on Notion, and
says which document is authoritative for which subject. Don't reconstruct project status from git log.

## The fleet — all production except one

| Node | Role | Notes |
|---|---|---|
| `system-1` | production rig | firmware `dev`; bind-mounts `config1.json` |
| `system-2` | production rig | firmware `dev`; bind-mounts `config2.json`; **also** runs the standalone turbo controller for valves 5/6 |
| `management` | production — Postgres, `report-api`, React UI, MQTT broker, SICK gateways | branch `latest`, **not** `main` (stale since Oct 2024) |
| `test` | non-prod rig | **offline since ~2026-07-24**; being requested from the manager |

Use the `ifet-ssh` skill to reach any of them.

## Production safety — non-negotiable

1. **Never rebuild, recreate, or restart a production container to try something out.** Rehearse
   off-production first (isolated compose project, throwaway `.env`, alternate ports), inform the deployment
   owner, agree a maintenance window. Runbook: `ifet-management/deployment/SECRETS.md` §2.
2. **Never `docker cp` a hot patch into a running container.** Deploy means rebuild from a clean checkout.
3. **On a node, the only safe git operations are history/index-only:** `git add`, `git commit`,
   `git update-index --skip-worktree`. **Never** `checkout`, `reset --hard`, `reset --mixed` (except the
   reviewed Step E), `stash pop`, `clean`, `pull`, or `merge` — those rewrite working-tree files, and on these
   nodes that means the live bind-mounted config a running container is reading.
4. **Config is bind-mounted; code is baked into the image.** So a config edit is live immediately, while a code
   edit needs a rebuild. This is why the repo drifted from production in the first place.
5. Secrets never enter git. `management` `compose.yaml` and `config/fstab` are `skip-worktree` on the node.
6. **Never put a credential in `deployment/config/config.json` or `src/ifet_ui_react/config.json`** in the
   management repo — both are served to the browser.

## Working practice

- **Branch off `dev` in a clone. Never edit on a device.** A dirty node worktree is an incident signal.
- **Commit every day's work, including SSH sessions**, and update the matching Notion page the same day.
- **Every commit is authored `gad <abdulrahmanashraf.gad@gmail.com>` with no assistant attribution** — no
  `Co-Authored-By`, no "Generated with", no session links. This overrides any default to add a trailer. Node
  git identities are `Hammad` / `device2` / unset, so pass the author explicitly when committing on a node.
- Per-node config lives in the repo as that node's own tracked file. Host-specific values belong in that
  node's own compose file.
- Close open items in the authoritative document first (see `docs/INDEX.md` §1), then the views.
- **Docs are filed by role, not topic** — `labos-airtable/{contract,status,evidence,correspondence,runbooks}`,
  plus `operations/` and `hardware/`. `contract/` holds exactly one file; a second would mean one is a view
  and is misfiled. `correspondence/sent/` is append-only — never edit an artifact someone already has.
  Layout and the full inventory: `docs/INDEX.md` §2.

## Hardware gotchas that have already cost time

- **VFD Modbus address is `12`, not `5`** on the production rigs (2026-07-07 bring-up). A stale `5` in config
  is why a VFD went silent. `tools/scanner.py` probes the bus.
- Pressure sensors read PSI and are scaled ×144 to **PSF** via per-sensor `scale`/`unit` in config.
- system-1's serial device is `/dev/ttyUSB0`, not `/dev/ttyACM0`.
- The `active` config flag does **not** actually gate polling.

## Current work

LabOS ↔ Airtable integration, Epic IFET-32, **week 2 of 5**. Integration branches:
`feature/labos-firmware-p3` here, `feature/labos-airtable` in `ifet-management`. **Nothing is deployed.**

**Start at `docs/INDEX.md` §0 ("Resume here")** — current state, what is blocked on whom, and what to pick up.

Two standing cautions that outlive any one session:

1. **Do not drive a rig from Airtable requirement values.** Their PDF extractor shifts values one column, so a
   60 PSF requirement reads as 9. LabOS cannot detect it — every shifted value is individually plausible.
   Contract §10.19.
2. **The `ifet-management` repo is not ground truth for database migrations — the node is.** Migrations were
   gitignored and the chain lived only on `management`. Before any schema work, check
   `SELECT * FROM alembic_version;` on the live database rather than trusting the repo.
