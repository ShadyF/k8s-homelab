# OpenClaw

OpenClaw is the default-namespace deployment for the OpenClaw agent router. Its main config lives in `cluster/apps/default/openclaw/configmap.enc.yaml`, where the embedded `openclaw.json` defines model routing, providers, and workspace paths.

## Logical model bundles

- **Codex/OpenAI-side bundle**: the active lane for the one OpenClaw instance. It serves `concierge`, `heba`, `boys`, `browser-ops`, `researcher`, and `coder`, but only `concierge`, `heba`, and `boys` keep QMD-backed recall lanes.
- **OpenRouter bundle**: retained for fallback or future reassignment.

## Workspace seed files

The repo-managed seed files for the four OpenClaw workspaces live in:

- `cluster/apps/default/openclaw/agents/concierge-workspace-configmap.yaml`
- `cluster/apps/default/openclaw/agents/researcher-workspace-configmap.yaml`
- `cluster/apps/default/openclaw/agents/browser-ops-workspace-configmap.yaml`
- `cluster/apps/default/openclaw/agents/coder-workspace-configmap.yaml`

These ConfigMaps define `AGENTS.md`, `BOOTSTRAP.md`, `IDENTITY.md`, and `USER.md` for each target workspace.

## Runtime bootstrap behavior

The OpenClaw PVC is mounted at `/home/node`, and OpenClaw keeps its state under `/home/node/.openclaw` on that volume.

The init container refreshes `AGENTS.md`, `IDENTITY.md`, and `USER.md` on every start.
`BOOTSTRAP.md` is only restored while `SOUL.md` is still missing.

That means:

- repo-managed role and user instructions stay in sync on pod restart
- one-time bootstrap does not get re-triggered after `SOUL.md` already exists
- runtime-generated files such as `SOUL.md` live on the PVC instead of in Git

## QMD + lossless-claw runtime setup

The OpenClaw PVC is mounted at `/home/node`, and OpenClaw keeps its state under `/home/node/.openclaw` on that volume.

The init container is now responsible only for PVC scaffolding and seed refresh:

- copy `/config/openclaw.json` into `/home/node/.openclaw/openclaw.json`
- ensure runtime directories exist under `/home/node/.openclaw`
- ensure `concierge`, `heba`, and `boys` each have a workspace, `memory/`, `MEMORY.md`, and agent-local QMD home directories
- install pinned `qmd` if it is absent from `/home/node/.openclaw/runtime/npm-global/bin/qmd`
- install pinned `lossless-claw` if `/home/node/.openclaw/extensions/lossless-claw` is missing
- refresh repo-managed workspace seed files

init is PVC scaffolding + seed refresh only
runtime is the owner of QMD collections and indexing

Each conversational lane keeps isolated memory paths on the PVC.

OpenClaw config keeps short per-agent workspace labels, but the final QMD collections for paths inside the workspace are agent-scoped by runtime:

- `<agent>-workspace-root-<agent>`
- `<agent>-workspace-memory-<agent>`
- `sessions-<agent>`

`researcher`, `browser-ops`, and `coder` stay stateless for memory search.

## Filesystem tool scoping

OpenClaw sandboxing remains off in this deployment. Filesystem safety is enforced instead with per-agent `workspaceOnly` guards inside the embedded `openclaw.json` config.

- `concierge` is limited to `/home/node/.openclaw/concierge-workspace`
- `heba` is limited to `/home/node/.openclaw/heba-workspace`
- `boys` is limited to `/home/node/.openclaw/boys-workspace`
- `coder` is limited to `/home/node/.openclaw/coder-workspace`

Those four agents currently hold the only filesystem-capable toolsets.

`researcher` and `browser-ops` keep `workspaceOnly` and `applyPatch.workspaceOnly` guards in place for future changes, but they do not currently receive filesystem tools.

Runtime state that must remain on the PVC:

- `/home/node/.openclaw/runtime/npm-global`
- `/home/node/.openclaw/agents/concierge/qmd/xdg-config`
- `/home/node/.openclaw/agents/concierge/qmd/xdg-cache`
- `/home/node/.openclaw/agents/concierge/qmd/sessions`
- `/home/node/.openclaw/agents/heba/qmd/xdg-config`
- `/home/node/.openclaw/agents/heba/qmd/xdg-cache`
- `/home/node/.openclaw/agents/heba/qmd/sessions`
- `/home/node/.openclaw/agents/boys/qmd/xdg-config`
- `/home/node/.openclaw/agents/boys/qmd/xdg-cache`
- `/home/node/.openclaw/agents/boys/qmd/sessions`
- `/home/node/.openclaw/extensions`
- `/home/node/.openclaw/lcm/lcm.db`
- `/home/node/.openclaw/lcm/large-files`

To inspect the live collections for each conversational agent, export the agent-local QMD paths and list collections:

```bash
kubectl -n default exec deploy/openclaw -c gateway -- sh -lc '
  set -eu
  export XDG_CONFIG_HOME=/home/node/.openclaw/agents/concierge/qmd/xdg-config
  export XDG_CACHE_HOME=/home/node/.openclaw/agents/concierge/qmd/xdg-cache
  export QMD_SESSIONS_DIR=/home/node/.openclaw/agents/concierge/qmd/sessions
  qmd collection list
'
```

Healthy output for each agent should contain:

- `<agent>-workspace-root-<agent>`
- `<agent>-workspace-memory-<agent>`
- `sessions-<agent>`

## Concierge routing precedence

`concierge` should route requests in this order:

1. Explicit specialist commands such as `ask researcher`, `use researcher`, and `delegate to researcher` have the highest routing priority.
2. Hard task-type routing comes next.
3. Concierge judgment applies only to everything else.

Comparisons, buying advice, product research, and source-backed opinion gathering should default to `researcher`.
Browser automation and rendered UI work should default to `browser-ops`.
Code, config, test, script, or skill changes should default to `coder`.

## Specialist-output synthesis

`concierge` may shorten specialist output, but it should not omit the main conclusion, key evidence, caveats, recommendations, or material citations.

If the user explicitly asks for the full specialist output, `concierge` should pass it through with minimal transformation.

## Current agent intent

- `concierge`: default front door, planning, coordination, delegation, final synthesis, and QMD-backed recall
- `heba`: conversational lane with QMD-backed recall
- `boys`: conversational lane with QMD-backed recall
- `researcher`: source-heavy research and evidence gathering; stateless for memory search
- `browser-ops`: browser workflows, visible-state validation, and screenshots; stateless for memory search
- `coder`: code/config/test/script/skill changes when file-changing work is needed; stateless for memory search

## Manual stale-`SOUL.md` refresh

`SOUL.md` is persistent runtime state on the OpenClaw PVC.
If `concierge` behavior still contradicts the repo-managed routing policy after a reconcile, use this one-time refresh runbook:

```bash
pod=$(kubectl get pods -n default -l app.kubernetes.io/name=openclaw -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n default "$pod" -c gateway -- sh -lc '
  set -e
  cp /home/node/.openclaw/concierge-workspace/SOUL.md /home/node/.openclaw/concierge-workspace/SOUL.md.pre-delegation-refresh.bak
  rm /home/node/.openclaw/concierge-workspace/SOUL.md
'
kubectl rollout restart deployment/openclaw -n default
kubectl rollout status deployment/openclaw -n default --timeout=180s
```

After the restart, init-config restores `BOOTSTRAP.md` for `concierge` while `SOUL.md` is absent, and it stays in place until a later restart or re-init after `SOUL.md` exists.

## Future reassignment

If an agent is moved to a different model or provider lane later, update that agent's routing inside `openclaw.json` in `cluster/apps/default/openclaw/configmap.enc.yaml`.
