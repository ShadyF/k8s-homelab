# Hermes personal event skills

This directory installs repo-managed event skills into the personal `hermes` Deployment. The skill instructions themselves are agent-neutral and are not written as personal-Hermes-only skills.

The feature is repo-managed/GitOps:
- Egypt skill source: `cluster/apps/default/hermes/personal/skills/events/egypt-events/SKILL.md`
- UAE skill source: `cluster/apps/default/hermes/personal/skills/events/uae-events/SKILL.md`
- source helper: `cluster/apps/default/hermes/personal/scripts/events_seen.py`
- runtime ConfigMap projection: generated from base name `hermes-customizations` by `kustomization.yaml`

Installed into the Hermes PVC at pod startup:
- `/opt/data/skills/events/egypt-events/SKILL.md`
- `/opt/data/skills/events/uae-events/SKILL.md`
- `/opt/data/scripts/events_seen.py`

Seen-state lives on the existing `hermes-data` PVC:
- Egypt: `/opt/data/events/egypt-seen-events.jsonl`
- UAE: `/opt/data/events/uae-seen-events.jsonl`

Scope summary:
- `egypt-events`: Egypt events only, across all Egypt with Cairo/Giza priority.
- `uae-events`: UAE events only, currently through Live Nation UAE/Middle East sources.
- Egypt sources include Cairo360, CairoScene, TicketsMarche, Live Nation Middle East Egypt listings, Cairo Opera House, El Sawy, Room Art Space, D-CAF, AUC sources, Zawya, Startup Grind New Cairo, Founders Live Cairo, and approved Instagram accounts.
- Egypt skill excludes techno/electronic club nights and generic nightlife.

Delivery behavior:
- Scheduling is handled by the consuming agent/runtime.
- Do not add a Kubernetes CronJob.
- Emit a digest only when new events remain after dedupe.
- Return `[SILENT]` when no credible new events are found or source quality is too weak.

Validation:
- `python3 -m unittest cluster/apps/default/hermes/personal/scripts/test_events_seen.py -v`
- Smoke test example:
  ```bash
  printf '%s' '[{"title":"Example","date":"2026-01-01","url":"https://example.com/e1","venue":"Venue","city":"Cairo","category":"Culture","source":"Example"}]' | python3 cluster/apps/default/hermes/personal/scripts/events_seen.py check --state-file /tmp/events-seen.jsonl
  ```
- `kubectl kustomize cluster/apps/default/hermes/personal | kubectl apply --dry-run=client --validate=false -f -`

Operational notes:
- Source files under `skills/` and `scripts/` are kept readable/testable in git. Kustomize generates the ConfigMap from those files, so the skills and helper are not duplicated in a hand-written manifest.
- Kustomize keeps the generated ConfigMap name hash enabled. Content changes update the generated ConfigMap name and the Deployment volume reference, which rolls the pod so the init container recopies the latest files.
- The generic `prepare-hermes-customizations` init container copies the generated ConfigMap projection into Hermes home. ConfigMap keys use `__` as a path separator because Kubernetes ConfigMap keys cannot contain `/`.
- To add another repo-managed skill or script, add only a `configMapGenerator.files` entry in `kustomization.yaml` using one of these key forms:
  - `skills__<category>__<skill>__<filename>=skills/<category>/<skill>/<filename>`
  - `scripts__<filename>=scripts/<filename>`
- Do not use literal double underscores (`__`) in custom skill or script directory/file names; the init container decodes `__` back to `/` when installing generated ConfigMap keys.
- Do not edit the Deployment when adding another generated skill or script; the init container installs every generated key that starts with `skills__` or `scripts__`.
- Updating skill/script content only requires changing the source files; Flux/Kustomize regenerates the ConfigMap during reconciliation.
- Do not put secrets in these files.
