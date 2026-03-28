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

## Upgrade command
Use this command to update a machine, replacing `<ip>` with the target node IP:

```bash
k3sup join --ip <ip> --server-ip 192.168.1.203 --user worker --server-user worker --ssh-key ~/.ssh/id_ed25519 --k3s-channel stable
```

## Required process for each machine
1. Confirm which machine is being updated and ensure no other node is mid-upgrade.
2. Confirm the correct SSH user for that specific node.
3. Before running `k3sup`, inspect `/etc/systemd/system/k3s.service` on that machine.
4. Record any arguments already present in the `ExecStart` field.
5. Run the `k3sup join ...` command for that machine.
6. Re-check `/etc/systemd/system/k3s.service` because `k3sup` will overwrite it.
7. Restore any previously present `ExecStart` arguments that were lost.
8. Run `systemctl daemon-reload` after editing the unit file.
9. Ensure the k3s service is running correctly after the unit file is restored.
10. Verify the node is updated, back to `Ready`, and workloads are healthy before continuing.

## Verified service path
- The verified service path is `/etc/systemd/system/k3s.service`.

## Preserve ExecStart arguments
When `k3sup` rewrites the service unit, restore any custom arguments that existed before the update.

## Verification before moving on
Before touching the next machine, verify at least:
- `systemctl cat k3s` still contains the expected custom arguments
- the updated node is `Ready`
- `kubectl get nodes` shows the cluster healthy
- control-plane workloads and critical apps recover cleanly

## Workflow expectations
- Keep the upgrade sequence serialized: one node only.
- Be explicit about which node is in progress and which nodes are still pending.
- If anything is unclear about service restart timing after `daemon-reload`, prefer verifying the unit, reloading systemd, and then confirming k3s service health before proceeding.
