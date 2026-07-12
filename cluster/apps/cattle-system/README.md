# Rancher Manager

Flux installs Rancher from the vendored stable chart in `cluster/charts/rancher`. Rancher is available only through the internal ingress at `https://rancher.${SECRET_DOMAIN}`.

## Unsupported Kubernetes override

The cluster runs Kubernetes 1.36. Rancher 2.14.3 supports Kubernetes only through 1.35 and declares `kubeVersion: < 1.36.0-0`. The vendored chart changes only that field to `< 1.37.0-0`; this bypasses Helm's guard but does not make the combination supported.

## Access and TLS

The SOPS-encrypted bootstrap password is in `bootstrap-values.enc.yaml`. Retrieve it locally, log in as `admin`, and change it immediately. Rancher uses external TLS termination through internal ingress-nginx and its wildcard default certificate. A Flux post-render patch forces HTTPS redirection.

## Topology and upgrades

This is one replica on the same mixed-architecture cluster it manages. The pod may schedule on amd64 or arm64. Before upgrading, review release notes and the support matrix, vendor the complete new chart, compare it to upstream, and apply a metadata override only when still explicitly required.

## Rollback

Capture HelmRelease status, logs, events, and metrics before reverting. Revert through Git and let Flux uninstall Rancher; do not leave imperative fixes or cluster drift.
