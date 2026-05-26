---
name: pr-upgrade-review
description: Use when reviewing open pull requests, Renovate PRs, dependency upgrades, app upgrades, Helm chart updates, container image updates, release-note impact, or regression risk for this k8s-homelab repository. This skill should trigger whenever the user asks what open PRs can be merged, whether upgrades are safe, or what release notes imply for the repo's Kubernetes/Flux manifests.
compatibility: opencode
---

# PR Upgrade Review

Use this skill to review all open upgrade pull requests for `ShadyF/k8s-homelab`, especially Renovate PRs. The goal is not just to summarize versions; it is to decide whether each upgrade is safe and useful for this repo's actual Flux/Kubernetes configuration.

## Core behavior

- Analyze **all open PRs** by default.
- Do **not** require or use the `gh` CLI.
- Prefer GitHub MCP/API tools when available for PR metadata, files, commits, diffs, issues, and releases.
- Use `scripts/fetch_pr_upgrade_inventory.py` as a deterministic fallback or starting inventory when direct GitHub tooling is unavailable.
- Prefer repo/static validation before live-cluster inspection. Most upgrade PRs can be decided from PR patches, manifests, rendered/kustomized output, release notes, and issue research.
- Do repo-checkable validation before giving the final recommendation. Do not leave a vague `merge after checks` recommendation when those checks can be run locally from the repo.
- Inspect the live cluster only when the remaining risk is runtime-only and cannot be answered from repo/static evidence, or when the user explicitly asks for live validation.
- Produce a report first. Do not edit manifests, Helm values, docs, or other config unless the user explicitly approves a proposed change.
- Do not create commits or push changes. The user handles commits and pushes for this repository.

## Inventory workflow

1. Fetch open PRs for `ShadyF/k8s-homelab`.
2. For each PR, inspect title, body, branch names, author, commits, changed files, and patches/diffs.
3. Identify the app, Helm chart, container image, dependency, or controller being upgraded.
4. Identify the current version and target version. If not obvious from the PR title/body, infer from changed-file patches.
5. Extract release-note, changelog, compare, and tag links from the PR body.
6. Use changed file paths to locate related repo configuration.

If using the bundled helper, run from the repository root:

```bash
python .opencode/skills/pr-upgrade-review/scripts/fetch_pr_upgrade_inventory.py --output /tmp/opencode/pr-upgrade-inventory.json
```

The helper uses public GitHub REST API endpoints and supports `GITHUB_TOKEN` to avoid rate limits. It gathers facts only; it does not make recommendations. Treat version detection as heuristic inventory data: check `version_detection.source`, `version_detection.confidence`, and `version_detection.candidates` before relying on the range for release-note research. The helper includes PR body text, file patches, file change counts, and commit metadata so it can be used as a fallback when direct GitHub tooling is unavailable.

## Repository inspection

Inspect the changed files first, then nearby or related configuration:

- `cluster/apps/<namespace>/<app>/` for Flux-managed apps, HelmReleases, values, ConfigMaps, and app README files.
- `cluster/crds/` when an upgrade mentions CRDs, controllers, operators, or API changes.
- `cluster/base/` when the PR affects Flux wiring, substitutions, bootstrap resources, or shared cluster configuration.
- `ansible/` only when the upgrade affects host/bootstrap automation.
- `docs/` only when release notes imply user-facing or runbook changes.

Keep findings specific to the files actually used in this repo. Avoid generic upstream summaries that do not connect to local manifests or values.

## Repo-first validation

Before recommending a PR, run the checks that can be answered from the repository:

- Inspect the PR patch and confirm whether it is image-only, chart-only, CRD-only, or includes value/config changes.
- Parse affected YAML after applying or simulating the target version.
- For Flux/Kustomize paths, render the affected kustomization when practical.
- For CRD URL bumps, confirm the new URLs exist and the expected CRD resources still render.
- Check whether upstream breaking changes touch providers, sources, features, environment variables, CRDs, or Helm values actually used in this repo.
- If a reported regression only affects unused providers, disabled components, absent config, or a workflow this repo cannot plausibly exercise, mark it not applicable and allow `merge`.
- If a check cannot be performed from the repo, name the exact missing evidence and decide whether it justifies `manual review` or live-cluster inspection.

Do not inspect the live cluster as a default smoke test. Live checks are for runtime-only questions such as whether an already-deployed workload is healthy, whether an ingress actually serves traffic, or whether controller logs show an issue that repo/static evidence cannot answer.

## Release-note research

For each upgrade, read release information for the exact current-to-target version range:

1. Start with Renovate-provided release notes, changelog, compare, and source links in the PR body.
2. If Renovate did not include release notes, or says it failed to fetch them, find upstream notes directly from the app/chart/dependency GitHub releases, tags, changelog, documentation site, or artifact registry links.
3. Look for breaking changes, migration steps, deprecations, new defaults, changed Helm values, CRD changes, security fixes, and bug fixes.
4. Note new features only when this repo's current configuration could use them.

## Regression research

Check for negative upgrade signals before recommending a merge:

- Search upstream GitHub issues, discussions, and release comments for the target version and nearby patch versions.
- Search the web for regressions, upgrade failures, Kubernetes compatibility problems, Helm chart issues, image bugs, and architecture-specific problems.
- Prefer sources that name the target version, chart version, image tag, or dependency version.
- Treat unresolved regressions that match this repo's configuration as `hold` or `manual review`, not `merge`.
- If evidence is weak or generic, say so and avoid overstating risk.

## Recommendation categories

Use one of these categories for each PR:

- `merge`: repo/static checks are complete, any upstream breaking changes or regressions are irrelevant to this repo's actual config, and no required repo changes remain.
- `manual review`: a specific relevant risk remains that cannot be resolved from repo/static checks, or the repo contains encrypted/unknown config needed to assess impact.
- `hold`: known relevant regression, breaking change, missing migration, or unsafe version for this repo.

Avoid `merge after checks` as a final recommendation. If checks are needed and can be done from the repo, do them first. If a live/runtime check is truly required, say exactly which runtime check remains and use `manual review` unless the user asks you to perform that live check.

## Report structure

Use this structure for the final response.

### Executive summary

| PR | App/dependency | Version change | Recommendation | Reason |
| --- | --- | --- | --- | --- |

### Per-PR detail

For each PR include:

- PR URL
- changed files checked
- detected app/dependency and version change
- release-note highlights relevant to this repo
- breaking changes relevant to this repo
- useful new features or configuration opportunities
- regression and known-issue findings, with links when available
- repo-specific impact based on manifests, Helm values, CRDs, or related config checked
- repo/static checks performed, and any precise runtime-only check that remains
- final recommendation

### Manifest update candidates

If release notes or regression research suggest repo changes, list them separately:

| File | Proposed change | Evidence | Required before merge? |
| --- | --- | --- | --- |

After listing candidates, stop and ask whether the user wants you to make any of those changes. Do not edit files before approval.

## Safety rules

- Keep durable fixes in the repo; do not use live cluster mutations for PR review.
- Do not commit plaintext secrets.
- Keep image tags and chart versions explicit and Renovate-friendly.
- Avoid manual churn in Flux-generated bootstrap files unless the PR is specifically about Flux bootstrap.
- Do not make speculative manifest updates. Tie every proposed change to release notes, regression research, or a repo-specific compatibility concern.
