---
apply: always
---

# Flux Deployment Guidelines

- **Helm Releases:** When deploying third-party applications via Helm, use the Flux `HelmRelease` and `HelmRepository` custom resources. Do not use standard Helm CLI commands.
- **Version Pinning:** Always pin the `HelmRelease` chart version. Do not use `>=` or `*` unless specifically requested, to allow Renovate to manage the exact version bumps.
- **Values Configuration:** Place all Helm chart overrides in the `values:` section of the `HelmRelease`. If values are too large, suggest placing them in a `ConfigMap` and using the `valuesFrom` feature.
- **Namespace Declarations:** Ensure that any newly generated `Kustomization` or `HelmRelease` specifies the `targetNamespace` correctly.