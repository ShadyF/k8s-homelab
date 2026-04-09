---
name: k3s-upgrade-homelab
description: Instructions for updating the k3s homelab cluster one machine at a time while preserving custom systemd ExecStart arguments.
compatibility: opencode
---

# k3s-upgrade-homelab

Use this skill when updating k3s in this homelab.

## Safety model
- Update **only one machine at a time**.
- Do not move to the next machine until the current machine is confirmed healthy and the cluster is stable.
- If a node fails to recover, stop and fix that node before touching any other machine.

## Node access
- Load the `k8s-homelab` skill for node access details and general homelab rules.
- Always verify the node-specific SSH user before running the upgrade command. Do not assume every node uses the same SSH user.

## Upgrade commands
Use the command that matches the node role you are upgrading.

### Control-plane / server node
Use this for an existing additional control-plane node:

```bash
k3sup join --server --ip <ip> --server-ip <healthy-server-ip> --user <ssh-user> --server-user <server-ssh-user> --ssh-key ~/.ssh/id_ed25519 --k3s-channel stable --no-extras
```

### Worker / agent node
Use this for a worker node:

```bash
k3sup join --ip <ip> --server-ip <healthy-server-ip> --user <ssh-user> --server-user <server-ssh-user> --ssh-key ~/.ssh/id_ed25519 --k3s-channel stable
```

## Required process for each machine
1. Confirm which machine is being updated and ensure no other node is mid-upgrade.
2. Confirm whether the node is a control-plane node or a worker node.
3. Confirm the correct SSH user for that specific node.
4. Confirm `--server-ip` points to another healthy control-plane node, never the node being upgraded.
5. Before running `k3sup`, inspect the active k3s unit on that machine.
6. For control-plane nodes, inspect `/etc/systemd/system/k3s.service` and record any arguments already present in `ExecStart`.
7. For worker nodes, verify the active unit is `k3s-agent.service`.
8. Run the role-correct `k3sup` command for that machine.
9. For control-plane nodes, re-check `/etc/systemd/system/k3s.service` because `k3sup` may overwrite it.
10. Restore any previously present `ExecStart` arguments that were lost.
11. Run `systemctl daemon-reload` after editing the unit file.
12. Ensure the correct service is running again after the unit is restored.
13. Verify the node is updated, back to `Ready`, and workloads are healthy before continuing.

## Verified service paths
- Control-plane nodes use `/etc/systemd/system/k3s.service`.
- Worker nodes may not have `/etc/systemd/system/k3s.service`; their active unit is `k3s-agent.service`.

## Preserve ExecStart arguments
When `k3sup` rewrites the control-plane `k3s.service` unit, restore any custom arguments that existed before the update.

## Recovery if agent mode was used on a control-plane node
- Stop and disable the stray `k3s-agent.service`.
- Optionally remove only `/etc/systemd/system/k3s-agent.service` and `/etc/systemd/system/k3s-agent.service.env`.
- Run `systemctl daemon-reload` if you removed agent unit files.
- Do not run `k3s-uninstall.sh` or stop the healthy `k3s.service`.
- Retry with `k3sup join --server ...`.

## Verification before moving on
Before touching the next machine, verify at least:
- the expected service is active again (`k3s` on control-plane nodes, `k3s-agent` on workers)
- control-plane `systemctl cat k3s` still contains the expected custom arguments
- the updated node is `Ready`
- `kubectl get nodes` shows the cluster healthy
- control-plane workloads and critical apps recover cleanly

## Workflow expectations
- Keep the upgrade sequence serialized: one node only.
- Be explicit about which node is in progress and which nodes are still pending.
- If anything is unclear about service restart timing after `daemon-reload`, prefer verifying the unit, reloading systemd, and then confirming k3s service health before proceeding.
