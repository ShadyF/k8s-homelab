---
title: Installing k3s
---

# Installing k3s

[k3s](https://rancher.com/docs/k3s/latest/en/) is a lightweight version of Kubernetes, meant to be used on edge devices,
in CI, ARM boards and so on.

It's basically a single binary that contains everything to get kubernetes up and running.

To help us with installing `k3s`, we're going to be using a utility package
called [k3sup](https://github.com/alexellis/k3sup)

## Creating your cluster

Getting your cluster up and running is as simple as running this command from your local machine

```sh
k3sup install --ip <master_ip> --user master --local-path ~/.kube/config --merge --context homelab --ssh-key <ssh_key> --k3s-channel stable --no-extras
```

This will command will attempt to create a k3s master node on the machine you pointed to (via the `--ip` flag). After
that's done, the newly created cluster will be added to your `KUBECONFIG`, which would could then switch on over to
using `kubectl config use-context homelab`

If you just want to get the kubeconfig without creating the cluster again, simply add the `--skip-install` flag at the
end of the command above.

## Adding nodes to your cluster

Once you have created the initial control-plane node, add more machines based on their role.

### Add an additional control-plane node

Run the following from your local machine:

```sh
k3sup join --server --ip <control_plane_ip> --server-ip <healthy_control_plane_ip> --user <ssh_user> --server-user <server_ssh_user> --ssh-key <ssh_key> --k3s-channel stable --no-extras
```

Additional control-plane nodes run `k3s.service`. Do not use plain agent-mode `k3sup join ...` for a control-plane node.

Using agent-mode join on a control-plane node is incorrect and can create a stray `k3s-agent.service`.

### Add a worker node

Run the following from your local machine:

```sh
k3sup join --ip <worker_ip> --server-ip <healthy_control_plane_ip> --user <ssh_user> --server-user <server_ssh_user> --ssh-key <ssh_key> --k3s-channel stable
```

Worker nodes run `k3s-agent.service`.
