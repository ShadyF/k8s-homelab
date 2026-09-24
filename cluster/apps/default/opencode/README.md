# OpenCode logging

OpenCode v2 writes its logs to
`$HOME/.local/share/opencode/log/opencode.log` on the `opencode-data` PVC. The
`opencode-logs` sidecar in the `opencode` Deployment tails that file to its
container stdout. It mounts only the log directory, read-only, rather than the
rest of the OpenCode home directory.

View the streamed logs with:

```sh
kubectl logs -n default deployment/opencode -c opencode-logs -f
```

The sidecar starts at the end of the existing file and follows the filename
across rotation, retrying while the file is absent. It streams only new lines;
existing log content (including the current roughly 35 MB file) is not replayed.

Logs can contain sensitive prompts, model responses, tool output, or other
private data. Restrict access to Kubernetes logs and apply appropriate
retention controls to both the persistent PVC file and the cluster's log
backend. The sidecar's read-only subPath mount limits its access to the log
directory but does not remove sensitive content from the logs.

## Activation

The bootstrap init container creates the log directory before the application
containers start. Adding the sidecar changes the Deployment pod template and
triggers a rollout when Flux applies it; wait for that rollout before checking
the streamed logs. Later changes to the bootstrap ConfigMap alone do not restart
Pods, so use an intentional rollout when a bootstrap change must take effect.
