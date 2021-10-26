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
k3sup install --ip <master_ip> --user master --local-path ~/.kube/config --merge --context homelab --ssh-key <ssh_key> --k3s-channel latest --no-extras
```

This will command will attempt to create a k3s master node on the machine you pointed to (via the `--ip` flag). After
that's done, the newly created cluster will be added to your `KUBECONFIG`, which would could then switch on over to
using `kubectl config use-context homelab`

If you just want to get the kubeconfig without creating the cluster again, simply add the `--skip-install` flag at the
end of the command above.

## Adding nodes to your cluster

Once you've created your master node, it's time to add some workers!

Run the following from your local machine

!!! warning Not 100% sure whether `ssh-key` in below command should be the ssh key of the master node or the worker
node.

```sh
k3sup join --ip <worker_ip> --server-ip <master_ip> --user master --ssh-key <master_ssh_key> --k3s-channel latest
```