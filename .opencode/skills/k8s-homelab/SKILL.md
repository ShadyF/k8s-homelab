---
name: k8s-homelab
description: Guidance for working safely in this Flux-managed k3s homelab repo where the cluster is synced from manifests in this repository.
compatibility: opencode
---

# k8s-homelab

Use this skill when working in this repository.

## Repo model
- This repo is the source of truth for the homelab Kubernetes cluster.
- The live cluster is synced with **Flux**.
- The Kubernetes manifests that define the cluster live in this repo.
- Permanent cluster changes must be made here, not directly with imperative `kubectl` changes.

## Core rules
- Prefer changing manifests in this repo over changing live cluster state.
- Use read-only `kubectl` commands by default for inspection and debugging.
- Temporary live changes are acceptable only for short-lived testing/debugging and must be reverted or clearly reported.
- Do not leave permanent drift between the cluster and this repo.
- Do not create git commits or push changes for this repository. The user handles all commits and pushes themselves.

## Manifest and GitOps conventions
- Prefer Flux-native resources such as `HelmRelease` and `HelmRepository` over Helm CLI usage.
- Pin chart versions exactly.
- Keep Helm overrides in `values:`; if values become large, prefer `ConfigMap` + `valuesFrom`.
- Set `targetNamespace` correctly for Flux-managed Helm releases.
- For new apps, follow the existing namespace/app layout under `cluster/apps/<namespace>/<app>/`.

## Security and image defaults
- Do not use `latest` image tags; prefer explicit immutable tags.
- Keep image tags Renovate-friendly.
- Set resource `requests` and `limits`.
- Prefer secure pod/container defaults such as `runAsNonRoot`, dropping `ALL` capabilities, and `readOnlyRootFilesystem` where possible.
- Consider `NetworkPolicy` by default for new workloads.
- Never commit plain-text Kubernetes `Secret` values as the final form; use SOPS-encrypted manifests or provide explicit instructions to encrypt with SOPS.

## Ingress conventions
- Before creating an `Ingress`, determine whether the app is LAN-only or externally exposed.
- Use `ingressClassName: internal` by default for internal apps.
- Use `ingressClassName: external` only for intentionally public apps.
- For public ingress, include TLS/cert-manager and external-dns configuration as appropriate.
- For public apps that should not be anonymous, consider protecting them with oauth2-proxy.

## Repo layout
- `README.md` is the high-level entrypoint for the repo.
- `cluster/base/` contains Flux bootstrap and core cluster wiring, including `apps.yaml`, `crds.yaml`, `cluster-secrets.yaml`, `flux-system/`, and `flux-system-extras/`.
- `cluster/apps/` contains the main Flux-managed workloads grouped by namespace or platform area.
- `cluster/crds/` contains CRD/bootstrap resources for platform components.
- `ansible/` contains node and host automation, including inventory, roles, and playbooks.
- `ansible/playbooks/setup-os.yaml` contains OS/bootstrap setup for machines.
- `docs/` contains repository and homelab documentation.
- `docs/cluster_setup/` contains cluster bring-up and operations docs such as k3s, Flux, and SOPS setup.
- `docs/apps/` contains app-specific documentation.
- `.github/workflows/` contains automation such as Flux-related jobs and docs publishing.
- `.sops.yaml` defines SOPS encryption rules for secrets.
- `mkdocs.yml` defines the docs site configuration.

## Homelab context
- This homelab runs **k3s**.
- If a task involves the live cluster, treat Flux reconciliation as the final path for durable changes.
- For k3s upgrade work, load the `k3s-upgrade-homelab` skill.

### SSH access
- Node access is available when node-level diagnostics are needed:
  - `k8-w1`: `ssh master@192.168.1.201`
  - `k8-w2`: `ssh worker@192.168.1.200`
  - `k8-w3`: `ssh worker@192.168.1.202`
  - `k8-w4`: `ssh worker@192.168.1.203`
- Use SSH narrowly for diagnostics, logs, service inspection, and carefully scoped maintenance.
- Do not use SSH to bypass Flux/GitOps for permanent Kubernetes changes.

## Expected behavior
- When proposing a fix, prefer the manifest or config path in this repo.
- If inspecting live state, use it to inform repo changes rather than bypass them.
- For Kubernetes resource changes, start by looking under `cluster/base/`, `cluster/apps/`, and `cluster/crds/`.
- For node/bootstrap changes, check `ansible/` before suggesting manual host edits.
- For secret-related changes, keep `.sops.yaml` and the repo's SOPS workflow in mind.
- For homelab node issues, use the SSH map above, but keep permanent fixes in-repo whenever possible.
- For app changes, include or update a `README.md` in the app folder when needed to explain purpose and configuration.
