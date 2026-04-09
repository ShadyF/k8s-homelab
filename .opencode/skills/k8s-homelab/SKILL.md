---
name: k8s-homelab
description: Use when working in this repository on Kubernetes manifests, Flux-managed apps, live-cluster inspection, or homelab node/bootstrap tasks.
compatibility: opencode
---

# k8s-homelab

Use this skill when working in this repository.

## Boundary with AGENTS.md
- `AGENTS.md` holds stable repo facts: Flux entrypoint, cluster directory order, command/environment split, secret handling, and automation that can overwrite files.
- This skill should add workflow guidance and conventions that help with Kubernetes changes, live-cluster inspection, and host/bootstrap work.
- Do not duplicate the repo-orientation bullets from `AGENTS.md` here unless the skill needs a short reminder for a workflow-specific rule.

## Core rules
- For durable changes, follow the repo-first rule in `AGENTS.md`; use live-cluster changes mainly for inspection or short-lived debugging.
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

## Homelab context
- If a task involves the live cluster, treat Flux reconciliation as the final path for durable changes.
- For k3s upgrade work, load the `k3s-upgrade-homelab` skill.

### SSH access
- For node-level diagnostics, the current SSH targets are:
  - `k8-w1`: `ssh master@192.168.1.201`
  - `k8-w2`: `ssh worker@192.168.1.200`
  - `k8-w3`: `ssh worker@192.168.1.202`
  - `k8-w4`: `ssh worker@192.168.1.203`
- Use SSH narrowly for diagnostics, logs, service inspection, and carefully scoped maintenance.
- Do not use SSH to bypass Flux/GitOps for permanent Kubernetes changes.

## Expected behavior
- When proposing a fix, prefer the manifest or config path in this repo.
- If inspecting live state, use it to inform repo changes rather than bypass them.
- For Kubernetes resource changes, start from the repo paths called out in `AGENTS.md`, then narrow to the specific app or platform area.
- For node/bootstrap changes, check `ansible/` before suggesting manual host edits.
- For secret-related changes, follow the repo SOPS workflow documented in `AGENTS.md`.
- For homelab node issues, use the SSH map above, but keep permanent fixes in-repo whenever possible.
- For app changes, include or update a `README.md` in the app folder when needed to explain purpose and configuration.
