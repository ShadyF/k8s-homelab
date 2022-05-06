---
title: Tips and Tricks
---

Here are some tips and tricks that might be of use.

## Change kubectl context

```shell
kubectl config use-context homelab
```

## Change default shell

```shell
chsh --shell /usr/bin/fish
```

## Retrieve Raspberry pi's CPU temp in Ubuntu

```shell
cat /sys/class/thermal/thermal_zone0/temp
```

## Debug pod stuck in crashloop

Force the pod to run the sleep command rather than what it has as an entrypoint, allowing you to SSH into it and debug
what's going on

Add the following to your pod's definition

```yaml
command: [ 'sleep' ]
args: [ 'infinity' ]
```

## Exporting GPG key from one machine to another

Follow the steps provided
in [this guide](https://makandracards.com/makandra-orga/37763-gpg-extract-private-key-and-import-on-different-machine)

## Creating a docker registry secret yaml file

```bash
kubectl create secret docker-registry regcred --docker-server="https://index.docker.io/v1/" --docker-username=<username> --docker-password=<password> --docker-email=<email> --dry-run=client -oyaml > regcred.yaml
```

## Remove useless ubuntu stuff

```bash
# Remove snapd, takes up CPU and not needed on a kube node
sudo apt autoremove --purge snapd
```

## To see the data created in a longhorn volume

1. use `lsblk -f` or `df -H` to find your desired PVC path
2. `cd` into it

## Setting up log2ram to reduce SD card strain / SSD writes  
https://github.com/azlux/log2ram