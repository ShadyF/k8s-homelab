---
title: Tips and Tricks
---

Here are some tips and tricks that might be of use.

### Change kubectl context

```shell
kubectl config use-context homelab
```

### Change default shell

```shell
chsh --shell /usr/bin/fish
```

### Retrieve Raspberry pi's CPU temp in Ubuntu

```shell
cat /sys/class/thermal/thermal_zone0/temp
```

### Debug pod stuck in crashloop

Force the pod to run the sleep command rather than what it has as an entrypoint, allowing you to SSH into it and debug
what's going on

Add the following to your pod's definition

```yaml
command: [ 'sleep' ]
args: [ 'infinity' ]
```
