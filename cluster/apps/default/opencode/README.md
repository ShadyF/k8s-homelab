# OpenCode logging

OpenChamber manages the OpenCode server as a child process of the `openchamber`
container. The `opencode-log-wrapper` ConfigMap mounts a small executable wrapper
at `/opt/opencode-wrapper/opencode-wrapper` and `OPENCODE_BINARY` points to it.

- `serve` invocations add `--print-logs --log-level INFO`.
- OpenCode server stderr is redirected to the parent container's stderr stream.
- OpenCode server stdout remains a pipe so OpenChamber can detect the listening
  line during startup.
- Version, help, and other non-server invocations pass through unchanged.

View the managed OpenCode logs with:

```sh
kubectl logs deployment/opencode -n default -c openchamber
```

## Activation

Flux applies the ConfigMap but does not restart Pods when referenced ConfigMap
data changes. The OpenCode-specific
`opencode.home.arpa/binary-settings-revision` pod-template annotation triggers
the rollout for this bootstrap change. After Flux applies the manifests, wait
for that rollout before checking logs.

The bootstrap owns migration of the persisted OpenChamber setting. On every
successful bootstrap it atomically preserves all settings and writes
`opencodeBinary: ""`, the documented clear sentinel. OpenChamber then leaves
the manifest-provided `OPENCODE_BINARY` value unchanged, so the manifest owns
selection of the log wrapper and the wrapper owns selection of the installed
OpenCode CLI. Malformed settings are rejected without replacement. For future
bootstrap or wrapper changes, use an OpenCode-specific pod-template change or
an intentional rollout restart; do not rely on ConfigMap reconciliation alone.

OpenChamber still keeps only its normal captured stderr tail for diagnostics;
after this redirect, managed OpenCode stderr is available through Kubernetes
container logs instead of that OpenChamber tail.
