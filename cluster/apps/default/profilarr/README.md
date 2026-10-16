# Profilarr v2 pilot

Review and verify backups before publishing these manifests. Editing this repository does not stop live v1. The owner must review, commit, and push the changes before Flux applies them; no live rollout is performed by this preparation.

## Runtime and storage

The raw Deployment runs one replica with `Recreate`. During rollout Kubernetes terminates the old v1 pod before starting v2. The Service and internal Ingress remain on port 6868 at `https://profilarr.${SECRET_DOMAIN}`.

V2 uses `ghcr.io/dictionarry-hub/profilarr:2.2.0` with fresh `/config` storage on `profilarr-v2-pvc`. Do not copy v1 appdata into it: v1 databases and configuration cannot be migrated in place. The existing `profilarr-pvc` manifest is retained unchanged so Flux pruning does not delete the rollback claim. Keep both claims when rolling back.

The new Longhorn RWO claim requests 2Gi, matching the nearby Sonarr config claim as a local starting assumption. CPU 100m and memory 256Mi requests, with a 1Gi memory limit and no CPU limit, are initial local values. These are not upstream minimums. Watch storage growth and memory during database builds before expanding use.

The pinned image and entrypoint support UID/GID 1000 directly; `fsGroup: 1000` supplies volume access. Check actual write permissions after rollout. `AUTH=on` uses local account setup on first visit; create the account before connecting Arr. No credentials are stored here. `ORIGIN` sets the external URL and `TZ` remains `Africa/Cairo`.

The TCP startup probe allows up to 30 minutes for the server to listen. Readiness uses the upstream `/api/v1/health` endpoint. An unfinished PCD cache can report degraded with HTTP 200; readiness is not proof that the database build or sync is ready. There is intentionally no liveness probe: repository or database health failures must not cause repeated restarts during remote PCD builds. Inspect failures through logs and the UI. No parser is deployed; database sync works without it, while profile/custom-format testing needs the optional parser.

## Before publishing

1. Make verified, restorable backups of original Profilarr `/config`, its v1 Git repository and unpublished edits, and every Sonarr/Radarr instance that may be changed. Confirm the restore procedure and record the backup locations outside this repository. A retained PVC alone is not a backup.
2. Record existing Arr quality-profile names, assignments, custom-format definitions and scores, including local tweaks. V1 YAML repositories cannot be assumed compatible with v2 PCD repositories; retain them for comparison or manual recreation.
3. Review the scoped diff and validation results. The owner decides when to commit and push. Flux then replaces v1 with v2; expect a service interruption. Do not run another v1 sync controller against the pilot Arr instance.

## After owner-approved Flux rollout

These are read-only checks to run after publication, not instructions to apply manifests manually:

```sh
kubectl -n default rollout status deployment/profilarr --timeout=10m
kubectl -n default get pods -l app=profilarr -o wide
kubectl -n default get pvc profilarr-pvc profilarr-v2-pvc
kubectl -n default logs deployment/profilarr --tail=200
kubectl -n default get deployment profilarr -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}{.spec.template.spec.volumes[0].persistentVolumeClaim.claimName}{"\n"}'
```

Confirm the image is `2.2.0`, only the v2 claim is mounted, the old claim still exists, both claims are bound, and logs show no permission errors or restart loop. Use Prometheus for memory/restart trends and Loki for startup/build errors. Open the internal HTTPS URL, complete local account setup, and confirm authentication is required. Check the health response and database build status separately before any sync.

## One manual pilot

1. Let the fresh installation link and build the first-party Dictionarry database (`v2` branch). Its default automatic Git check/pull runs every 60 minutes. This alone does not write to Arr. Check and disable the global **apply default delay profiles** setting before adding any Arr connection: adding a connection can otherwise write delay settings immediately.
2. Add exactly one backed-up Arr instance. Confirm all sync selections are empty and triggers are `manual`. Keep `schedule` and `on_pull` off. Upgrade, rename, and cleanup schedules default to disabled; verify they remain disabled and do not invoke those actions manually.
3. Compare one candidate PCD quality profile against Arr before selecting it. Match exact names, custom-format definitions and scores, media assignments, and local tweaks. Same-name objects are updated in place; different names create new objects. Updating a profile can reset unselected custom-format scores to zero. Shared same-name custom formats change globally, including for profiles outside the pilot. Recreate required tweaks in a v2-compatible PCD before proceeding, or stop the pilot.
4. Only after verified backups and that comparison, select exactly one quality profile, retain the `manual` trigger, save, and run the explicit quality-profile sync exactly once. Do not run cleanup, upgrades, rename, a second pilot, or enable automation. Sync can partially succeed and has no transactional rollback.
5. Inspect Arr profile identity, assignments, scores and shared formats after the run. Review Profilarr logs and Arr state for errors or unexpected changes. Stop here for owner review before any further sync.

## Rollback

Stop further v2 writes and preserve logs and v2 data for diagnosis. Have the owner publish a Git revert of the Deployment to `santiagosayshey/profilarr:v1.1.5`, its original environment and original `profilarr-pvc` mount. Retain both PVC manifests; do not revert away the v2 claim and let Flux prune it. Verify v2 has stopped before v1 resumes.

If v2 changed Arr, restore the affected Arr backups before allowing v1 sync again. Reverting the Profilarr image or PVC does not undo profile, score, custom-format, or delay-setting changes in Arr. Restore original Profilarr data from its verified backup if needed. V1 is unmaintained; rollback is a recovery option, not a supported long-term upgrade path.

## Pinned upstream references

- [v2.2.0 Dockerfile](https://github.com/Dictionarry-Hub/profilarr/blob/v2.2.0/Dockerfile), [entrypoint](https://github.com/Dictionarry-Hub/profilarr/blob/v2.2.0/scripts/entrypoint.sh), and [health handler](https://github.com/Dictionarry-Hub/profilarr/blob/v2.2.0/src/routes/api/v1/health/+server.ts): image runtime, non-root mode and health endpoint.
- [Runtime and no-automation findings](../../../../docs/research/profilarr-v2-migration.md#fresh-v220-pilot-runtime-and-no-automation-setup): pinned sources for startup, defaults, and the delay-setting side effect.
- [Sync behavior](https://github.com/Dictionarry-Hub/profilarr/blob/v2.2.0/docs/backend/sync.md): recovery limits; compare the repository research note for exact-name matching and shared-format effects.
