---
title: Setting up Flux
---

# Setting up Flux

## Installing Flux

1. Make a personal token on github with repo privelages
2. Install flux locally (`flux-bin` in AUR if using arch)
3. Export `GITHUB_TOKEN` to shell environment
4. Run the following command

```bash
flux bootstrap github --owner=ShadyF --repository=homelab --branch=master --path=cluster/base --personal
```

## Reconciling using flux

```bash
# Reconcile gitcontroller (given that flux-system is the name of the gitcontroller)
flux reconcile source git flux-system

# Reconcile kustomization (given that apps is the name of the kustomization controller)
flux reconcile kustomization apps

# Reconcile a helm release
flux reconcile helmrelease oauth2-proxy -n networking
```