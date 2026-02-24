---
apply: always
---

# JetBrains AI Assistant Rules for Kubernetes Homelab

This repository contains GitOps-driven Kubernetes manifests for a homelab. The cluster is fully managed declaratively via Flux. When assisting with this project, you MUST strictly adhere to the following rules:

## 1. Cluster Interaction (Read-Only)
- **Query Only:** When suggesting or executing commands against the live cluster, ONLY use read-only `kubectl` commands (e.g., `kubectl get`, `kubectl describe`, `kubectl logs`).
- **No Manual Edits:** NEVER suggest or execute imperative commands that modify the cluster state (e.g., `kubectl edit`, `kubectl apply`, `kubectl delete`, `helm install`). All cluster changes must be made via repository manifests.

## 2. GitOps Workflow (Flux)
- **Manifests Over Direct Changes:** Any proposed changes to the cluster must be written as declarative Kubernetes manifests.
- **Flux Sync:** The repository is continuously synced to the cluster by Flux. Assume that pushing changes to the repository is the only way to deploy.
- **No Git Commits:** Do not execute `git commit` or `git push`. Only generate and provide the code/manifests; the user will review and commit the changes manually.

## 3. Renovate Compatibility
- **Image Tags:** This repository uses Renovate to automatically create merge/pull requests when container images are updated. 
- Ensure container images in manifests are clearly defined (e.g., `image: ghcr.io/namespace/image:v1.2.3`) so Renovate can easily parse and bump the tags.
- NEVER use `latest` tags. Always use explicit, immutable tags (SemVer preferred).

## 4. Security Defaults
Whenever creating or updating manifests, prioritize security best practices by default:
- **Security Contexts:** ALWAYS include a `securityContext` where possible. Drop all capabilities (`ALL`), run as non-root (`runAsNonRoot: true`), and set `readOnlyRootFilesystem: true` unless the specific application explicitly requires otherwise.
- **Resource Limits:** Define `resources.requests` and `resources.limits` for CPU and memory to prevent resource starvation.
- **Network Policies:** Suggest or generate `NetworkPolicy` manifests to restrict ingress/egress traffic if applicable.

## 5. Secret Management (SOPS)
- **Encryption Required:** NEVER generate or suggest storing plain-text secrets (e.g., `kind: Secret` with base64 encoded data) in this repository.
- **SOPS Integration:** All secrets must be encrypted using SOPS. When providing a secret manifest, provide the clear-text version in a markdown code block with explicit instructions for the user to encrypt it using SOPS (e.g., `sops --encrypt --in-place <file>`), or format it as a SOPS-compatible encrypted structure if specifically requested.

## 6. Repository Structure
- Respect the existing directory structure (e.g., `cluster/apps/<namespace>/<app>`, `cluster/base`, `cluster/crds`).
- When introducing a new application, place it in the appropriate namespace folder under `cluster/apps/`.
- Use the established Flux `HelmRelease` and `HelmRepository` patterns when dealing with Helm charts.

## 7. Application Configuration Guidelines

- **ConfigMaps vs. Secrets:** Separate non-sensitive configuration data from sensitive credentials. Use `ConfigMap` for general settings (e.g., `app-config.yaml`, environment variables like `TZ`) and `Secret` for API keys, passwords, and tokens.
- **SOPS Enforcement:** Reminder: Any `Secret` generated must be accompanied by instructions to encrypt it with SOPS.
- **Immutability:** Consider setting `immutable: true` on `ConfigMap` and `Secret` manifests if the application relies on rollouts (e.g., using a reloader controller) to restart pods upon config changes.