# OpenChamber and OpenCode

## Runtime

The `openchamber` container runs OpenChamber and its managed OpenCode child
process. Bootstrap installs the package versions pinned in the Deployment.
OpenCode listens on `127.0.0.1:4096`; the UI listens on port 3000.
OpenChamber and its managed OpenCode child use the server password supplied
through environment variables from the encrypted Secret.

Startup, readiness, and liveness checks require OpenChamber to report a running,
ready OpenCode connection. A sustained integration failure restarts the combined
container. Restarting OpenChamber also interrupts active OpenCode work.

The Docker sidecar, TLS client certificates, Kubernetes credentials, workspace
storage, and native worktree mounts remain available to tool jobs in this
container. The `opencode` Kubernetes Service exposes preview port 4173.

The workspace, Homebrew, and Docker PVCs retain data across Pod recreation.
Back up persistent state before rollout. After Flux reconciles, check existing
sessions, a new tool call, Docker access, and recovery after a restart. Reverting
the Deployment and bootstrap ConfigMap together restores the previous runtime
layout; do not delete PVCs during rollback.

## OpenCode logging

OpenCode writes runtime logs to
`$HOME/.local/share/opencode/log/opencode.log` on the workspace PVC. The
`opencode-logs` container mounts only that directory, read-only, and follows
the file into container stdout for Kubernetes and Loki collection:

```sh
kubectl logs -n default deployment/opencode -c opencode-logs -f
```

The follower waits for the file to appear, follows rotation, and streams only
new lines. Existing file contents are not replayed when the follower starts.
View OpenChamber startup and lifecycle diagnostics separately:

```sh
kubectl logs -n default deployment/opencode -c openchamber -f
```

Logs can contain sensitive prompts, model responses, tool output, or other
private data. Restrict access to Kubernetes logs and apply appropriate
retention controls to persisted logs and the cluster's log backend.

## Activation

Deployment template changes trigger a rollout when Flux applies them. Changes
to the bootstrap ConfigMap alone do not restart Pods, so use an intentional
rollout when a bootstrap change must take effect.
