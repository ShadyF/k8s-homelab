# Speakr pilot

This is a single-user Speakr pilot. The `speakr-secrets` Secret is intentionally
not tracked in Git; it must exist in `default` before Flux reconciles the
HelmRelease. It is manual recovery state, so keep the values somewhere safe.

Create it manually with user-supplied values and a shell-generated `SECRET_KEY`:

```sh
export SPEAKR_ADMIN_PASSWORD='<admin-password>'
export OPENROUTER_API_KEY='<openrouter-api-key>'

kubectl -n default create secret generic speakr-secrets \
  --from-literal=ADMIN_PASSWORD="${SPEAKR_ADMIN_PASSWORD}" \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
```

The pilot has no diarization, Syncthing watcher, or ASR sidecar. Its 1Gi PVC
is disposable pilot data, not a backup. Speakr's default SQLite instance
directory is `/data/instance`. To replace the OpenRouter key without changing
the admin credentials or `SECRET_KEY`, set `OPENROUTER_API_KEY` to the new value
and patch the existing Secret:

```sh
kubectl -n default patch secret speakr-secrets --type merge \
  -p "{\"stringData\":{\"OPENROUTER_API_KEY\":\"${OPENROUTER_API_KEY}\"}}"
```

Restart the Speakr pod after replacing the key so the updated environment value
is loaded.
