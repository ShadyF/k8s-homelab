# AGENTS.md

## Scope
- This repo is the source of truth for the homelab k3s cluster. Flux syncs branch `master` from `cluster/base/`.
- Treat `cluster/base/ -> cluster/crds/ -> cluster/apps/` as the durable apply order.
- For Kubernetes changes, prefer updating manifests in this repo over imperative live-cluster changes.

## Layout that matters
- `cluster/base/`: Flux bootstrap, sync config, and cluster wiring.
- `cluster/crds/`: CRDs and prerequisites that must exist before apps.
- `cluster/apps/`: Flux-managed workloads grouped by namespace/platform area.
- `ansible/`: machine bootstrap/host automation; separate from Flux sync and uses its own Poetry project.
- `docs/`: documentation website content; root Poetry tooling is for this site.

## Commands and environments
- Docs site commands use the repo root: `poetry install`, `poetry run mkdocs serve`, `poetry run mkdocs build`.
- Ansible work should use the separate `ansible/pyproject.toml` environment, not the repo-root Poetry environment.
- There is no repo task runner; prefer exact commands already encoded in tracked configs and workflows.

## Secrets and substitutions
- Do not commit plaintext Kubernetes secrets. `.sops.yaml` encrypts `data` and `stringData`, and pre-commit runs `forbid-secrets`.
- `cluster/base/apps.yaml` enables SOPS decryption and `cluster-secrets` substitution for app manifests.

## Automation to avoid fighting
- Docs publishing is handled by `.github/workflows/mkdocs.yaml` and only triggers for docs-related paths.
- `.github/workflows/flux-schedule.yaml` rewrites `cluster/base/flux-system/gotk-components.yaml` during Flux upgrade automation; avoid manual churn there unless the task is about Flux bootstrap.
