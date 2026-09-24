# Orychamber

Orychamber is an additive OpenChamber deployment for the `default` namespace.
It keeps the OpenCode and OpenChamber workflow from `opencode` while giving it
its own names, storage, services, log sidecar, and public host:

- UI: `https://orychamber.${SECRET_DOMAIN}`
- Preview service: `http://orychamber-preview.default.svc.cluster.local:4173`
- Browserless CDP: `ws://browserless-chrome-svc.default.svc.cluster.local:3000/chrome`

## Architecture

The Deployment runs one `openchamber` application container, one bootstrap init
container, and one `opencode-logs` sidecar, with `Recreate` strategy on amd64
nodes. The application and bootstrap containers use the pinned
`mcr.microsoft.com/devcontainers/universal:6.1.7-noble` image. Bootstrap
installs the pinned `@opencode/cli` `2.0.15`, `@openchamber/web` `2.0.0`, and
`agent-browser` `0.38.1` packages into persistent workspace storage.

Compared with `cluster/apps/default/opencode/`, this deployment intentionally
has no nested container engine, cluster credentials, Kubernetes API access,
Plannotator, or Plannotator service. It has:

- a 20 GiB `orychamber-data` workspace PVC;
- a 5 GiB writable `orychamber-homebrew` PVC;
- a public UI Service on port 3000 and an internal preview Service on port 4173;
- a BusyBox `opencode-logs` sidecar that reads only the OpenCode log directory
  from `orychamber-data` through a read-only subPath mount;
- unrestricted egress, with ingress limited to the UI ingress controller and
  Browserless preview traffic.

The pinned universal image contains Docker, Compose, Buildx, and `kubectl`
clients. They remain inert: bootstrap does not install or configure them, and
the Pod has no Docker daemon or socket, Docker connection variables,
Kubernetes token, or RBAC binding.

The base image continues to provide the language and development tools used by
OpenCode. The agent-browser skill is updated during bootstrap for remote
Browserless CDP and the `orychamber-preview` service. Start preview servers on
`0.0.0.0:4173`, then browse them through that service rather than localhost.

Provider and model authentication are intentionally not preconfigured here.
Configure the required provider credentials and model settings after launch.

## OpenCode logs

OpenCode v2 writes logs to
`$HOME/.local/share/opencode/log/opencode.log` on the `orychamber-data` PVC.
Bootstrap creates the directory before the application containers start. The
`opencode-logs` sidecar tails the file to its container stdout and mounts only
that log directory, read-only; it does not have access to the rest of the home
directory.

Follow the streamed logs with:

```sh
kubectl logs -n default deployment/orychamber -c opencode-logs -f
```

The sidecar starts at the end of the current file, follows the filename across
rotation, and retries while the file is absent. Existing lines are not replayed.
Logs may contain sensitive prompts, model responses, tool output, or other
private data. Restrict access to Kubernetes logs and set suitable retention for
both the PVC file and the cluster log backend.

## Secret provisioning

Flux expects an encrypted Secret named `orychamber-openchamber-secrets` with
these two keys:

- `OPENCHAMBER_UI_PASSWORD`
- `OPENCODE_JWT_SECRET`

The `secrets.enc.yaml` skeleton contains empty values. Fill both quoted values,
using a strong random JWT secret such as the output of
`openssl rand -base64 48`, then encrypt the file from the repository root:

```sh
sops --encrypt --in-place cluster/apps/default/orychamber/secrets.enc.yaml
```

Before staging or committing, verify that SOPS can decrypt the file without
printing plaintext and that both values are encrypted:

```sh
sops --decrypt secrets.enc.yaml > /dev/null
grep -qE '^[[:space:]]+OPENCHAMBER_UI_PASSWORD: ENC\[' secrets.enc.yaml
grep -qE '^[[:space:]]+OPENCODE_JWT_SECRET: ENC\[' secrets.enc.yaml
test "$(grep -Ec '^[[:space:]]+(OPENCHAMBER_UI_PASSWORD|OPENCODE_JWT_SECRET): ' secrets.enc.yaml)" -eq 2
```

Do not stage, commit, or apply this file while either value is empty or
plaintext.

## Deployment and verification

Flux discovers this directory through the recursive `cluster/apps` source. It
decrypts `secrets.enc.yaml` when present, substitutes `${SECRET_DOMAIN}`, and
reconciles the manifests. Adding the sidecar changes the Deployment pod
template and triggers a rollout when Flux applies it. ConfigMap changes alone
do not restart an existing Pod; for future bootstrap changes, update the
`orychamber.home.arpa/binary-settings-revision` Pod-template annotation or
intentionally restart the Deployment.

After the encrypted Secret is available and Flux has reconciled, verify with:

```sh
kubectl -n default get deployment,pod,svc,ingress,pvc -l app.kubernetes.io/name=orychamber
kubectl -n default rollout status deployment/orychamber
kubectl -n default logs deployment/orychamber -c bootstrap
kubectl -n default logs deployment/orychamber -c openchamber
kubectl logs -n default deployment/orychamber -c opencode-logs -f
kubectl -n default describe pod -l app.kubernetes.io/name=orychamber
```

The OpenChamber readiness and liveness probes use `/health` on port 3000 and
also confirm that its managed OpenCode server is ready. Preview access is
internal to the cluster; Browserless should reach it through
`orychamber-preview.default.svc.cluster.local:4173`.
