# Junie AI Agent Guidelines for Kubernetes Homelab

You are assisting with a GitOps-driven Kubernetes homelab repository. This cluster is fully managed declaratively via Flux. Please strictly adhere to the following rules when suggesting or modifying any manifests or executing commands.

## 1. Cluster Interaction (Read-Only)
- **Query Only:** When interacting with the live cluster, ONLY use read-only `kubectl` commands (e.g., `kubectl get`, `kubectl describe`, `kubectl logs`).
- **No Manual Edits:** Do not execute imperative commands that modify the cluster state (e.g., `kubectl edit`, `kubectl apply`, `kubectl delete`, `helm install`). All changes must be made in the repository manifests.

## 2. GitOps Workflow (Flux)
- **Manifests Over Direct Changes:** Any proposed changes to the cluster must be written as declarative Kubernetes manifests within this repository.
- **Flux Sync:** The repository is continuously synced to the cluster by Flux. Assume that pushing changes to the `main` branch is the only way to deploy.
- **No Git Commits:** Do not execute `git commit` or `git push`. Only generate and provide the code/manifests; the user will review and commit the changes manually.

## 3. Renovate Compatibility
- **Image Tags:** This repository uses Renovate to automatically create merge/pull requests when container images are updated. 
- Ensure container images in manifests are clearly defined (e.g., `image: ghcr.io/namespace/image:v1.2.3`) so Renovate can easily parse and bump the tags.
- Avoid using `latest` tags. Always use explicit, immutable tags (SemVer preferred).

## 4. Security Defaults
Whenever creating or updating manifests, prioritize security best practices by default:
- **Security Contexts:** Always include a `securityContext` where possible. Drop all capabilities (`ALL`), run as non-root (`runAsNonRoot: true`), and set `readOnlyRootFilesystem: true` unless the specific application explicitly requires otherwise.
- **Resource Limits:** Define `resources.requests` and `resources.limits` for CPU and memory to prevent resource starvation.
- **Network Policies:** Consider generating or suggesting `NetworkPolicy` manifests to restrict ingress/egress traffic if applicable.

## 5. Secret Management (SOPS)
- **Encryption Required:** Never store plain-text secrets (e.g., `kind: Secret` with base64 encoded data) in this repository.
- **SOPS Integration:** All secrets must be encrypted using SOPS before being added to the repository. When providing a secret manifest, either provide it as a `.sops.yaml` compatible encrypted structure, or provide the clear-text version in a markdown code block with explicit instructions for the user to encrypt it using SOPS (e.g., `sops --encrypt --in-place <file>`).

## 6. Repository Structure
- Respect the existing directory structure (e.g., `cluster/apps/<namespace>/<app>`, `cluster/base`, `cluster/crds`).
- When introducing a new application, place it in the appropriate namespace folder under `cluster/apps/`.
- If Helm releases are used, follow the established Flux `HelmRelease` and `HelmRepository` patterns used in this project.

## 7. Documentation
- **Documentation:** Ensure that all manifests include comments explaining their purpose and configuration. Use clear, concise language and follow the established documentation style guide.
- **Readme Files:** Include a `README.md` file in each application folder explaining the application, its purpose, and any specific configuration details.
- **Versioning:** Use semantic versioning (SemVer) for all applications and components. Update the version number in the manifest whenever there are significant changes or bug fixes.