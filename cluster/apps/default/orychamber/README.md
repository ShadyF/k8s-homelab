# Orychamber

Orychamber is an additive OpenChamber deployment for the `default` namespace.
It keeps the OpenCode and OpenChamber workflow from `opencode` while giving it
its own names, storage, services, and public host:

- UI: `https://orychamber.${SECRET_DOMAIN}`
- Preview service: `http://orychamber-preview.default.svc.cluster.local:4173`
- Browserless CDP: `ws://browserless-chrome-svc.default.svc.cluster.local:3000/chrome`

## Architecture

The Deployment runs a bootstrap init container, an `openchamber` application
container, and an `opencode-logs` log follower, with `Recreate` strategy on the
amd64 GPU node `k8-w5`.
OpenChamber manages OpenCode as a child process in the same container.
Bootstrap installs the pinned OpenCode,
OpenChamber, and agent-browser packages declared in the Deployment into
persistent workspace storage.

OpenCode listens on `127.0.0.1:4096`. OpenChamber and its managed OpenCode child
use the server password supplied through environment variables from the
encrypted Secret. Startup, readiness, and
liveness probes require OpenChamber to report a running, ready OpenCode
connection. A sustained integration failure restarts the combined container.
Restarting OpenChamber also interrupts active OpenCode work.

Compared with `cluster/apps/default/opencode/`, this deployment intentionally
has no nested container engine, cluster credentials, or Kubernetes API access.
It has:

- a 20 GiB `orychamber-data` workspace PVC;
- a 5 GiB writable `orychamber-homebrew` PVC;
- a public UI Service on port 3000 and an internal preview Service on port 4173;
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

## GPU access

The Pod uses the `nvidia` runtime class. The `openchamber` container requests
one `nvidia.com/gpu` time-sharing slot and enables the `compute,utility,graphics`
driver capabilities for compute and headless graphics. Blender jobs launched by
OpenCode run in this container; the bootstrap and log containers have no GPU
allocation.

The node has one NVIDIA GeForce GTX 1660 SUPER with 6 GiB VRAM, shared with
WhisperX. Time-sliced scheduling provides no VRAM or performance isolation, so
concurrent workloads can exhaust GPU memory or slow each other down.

This configuration provides GPU devices and driver libraries. It does not install
Blender or the CUDA toolkit. After Flux deploys the manifest, use an account with
Pod exec permission to check device access and the installed Blender version:

```sh
# Check GPU visibility in the container that runs tool jobs.
kubectl -n default exec deployment/orychamber -c openchamber -- nvidia-smi -L

# Check the Blender version if Blender is installed.
kubectl -n default exec deployment/orychamber -c openchamber -- blender --version
```

Then enumerate Cycles GPU devices in that Blender version and run a small GPU
render. Confirm that it uses the allocated GPU without falling back to CPU
rendering before relying on GPU acceleration.

## Secret provisioning

Flux expects an encrypted Secret named `orychamber-openchamber-secrets` with
these three keys:

- `OPENCHAMBER_UI_PASSWORD`
- `OPENCODE_JWT_SECRET`
- `OPENCODE_SERVER_PASSWORD`

Provide strong random values for all three keys,
using a strong random JWT secret such as the output of
`openssl rand -base64 48`, then encrypt the file from the repository root:

```sh
sops --encrypt --in-place cluster/apps/default/orychamber/secrets.enc.yaml
```

Before staging or committing, verify that SOPS can decrypt the file without
printing plaintext and that all three values are encrypted:

```sh
sops --decrypt secrets.enc.yaml > /dev/null
grep -qE '^[[:space:]]+OPENCHAMBER_UI_PASSWORD: ENC\[' secrets.enc.yaml
grep -qE '^[[:space:]]+OPENCODE_JWT_SECRET: ENC\[' secrets.enc.yaml
grep -qE '^[[:space:]]+OPENCODE_SERVER_PASSWORD: ENC\[' secrets.enc.yaml
test "$(grep -Ec '^[[:space:]]+(OPENCHAMBER_UI_PASSWORD|OPENCODE_JWT_SECRET|OPENCODE_SERVER_PASSWORD): ' secrets.enc.yaml)" -eq 3
```

Do not stage, commit, or apply this file while any value is empty or
plaintext.

## Deployment and verification

Flux discovers this directory through the recursive `cluster/apps` source. It
decrypts `secrets.enc.yaml` when present, substitutes `${SECRET_DOMAIN}`, and
reconciles the manifests. Deployment changes trigger a rollout when Flux applies
them. ConfigMap changes alone do not restart an existing Pod; for future
bootstrap changes, update the
`orychamber.home.arpa/binary-settings-revision` Pod-template annotation or
intentionally restart the Deployment.

After the encrypted Secret is available and Flux has reconciled, verify with:

```sh
kubectl -n default get deployment,pod,svc,ingress,pvc -l app.kubernetes.io/name=orychamber
kubectl -n default rollout status deployment/orychamber
kubectl -n default logs deployment/orychamber -c bootstrap
kubectl -n default logs deployment/orychamber -c openchamber
kubectl -n default logs deployment/orychamber -c opencode-logs
kubectl -n default describe pod -l app.kubernetes.io/name=orychamber
```

After rollout, verify existing sessions, a new tool call, GPU access, and recovery
after a restart. Back up persistent state before rollout. To roll back, restore
the Deployment and bootstrap ConfigMap together; retain both PVCs.

All three application probes check the reported OpenCode integration state.
Preview access is internal to the cluster;
Browserless should reach it through
`orychamber-preview.default.svc.cluster.local:4173`.

## OpenCode logging

OpenCode writes runtime logs to
`$HOME/.local/share/opencode/log/opencode.log` on the workspace PVC. The
`opencode-logs` container mounts only that directory, read-only, and follows
the file into container stdout for Kubernetes and Loki collection.
It waits for the file to appear, follows rotation, and streams only new lines;
existing contents are not replayed when the follower starts.

```sh
kubectl -n default logs deployment/orychamber -c opencode-logs -f
```

Logs can contain prompts, model responses, tool output, and credentials. Restrict
access and apply retention controls to both persisted files and centralized logs.
OpenChamber startup and lifecycle diagnostics remain in the `openchamber`
container's logs.
