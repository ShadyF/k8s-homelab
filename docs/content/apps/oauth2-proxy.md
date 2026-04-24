---
title: OAuth2 Proxy
---

# OAuth2 Proxy slows down k8s cluster

## The Problem

When `ingress-nginx` and `oauth2-proxy` are used together in a k8s cluster, as described in
this [tutorial](https://kubernetes.github.io/ingress-nginx/examples/auth/oauth-external-auth/), the cluster immediately
starts slowing down when accessing any application using HTTP / HTTPS that go through the ingress.

The issue is described further
in [this stackoverflow post](https://stackoverflow.com/questions/58997958/oauth2-proxy-authentication-calls-slow-on-kubernetes-cluster-with-auth-annotatio)

## The Cause

Setting the following in an application's annotation causes this issue

```yaml
annotations:
  nginx.ingress.kubernetes.io/auth-url: "http://auth.domain.com/oauth2/auth"
  nginx.ingress.kubernetes.io/auth-signin: "https://auth.domain.com/oauth2/sign_in"
```

### Why does adding these annotations cause the issue?

When `auth-url` is set to `auth.domain.com`, this means that the request goes outside the cluster (so-called hairpin
mode), and goes back via External IP of Ingress that routes to internal ClusterIP Service (which adds extra network
hops), instead going directly with ClusterIP/Service DNS name (you stay within Kubernetes cluster)[^1]

If a request is made to `auth.domain.com` from **inside** the internal network, the **internal** DNS resolves this to an
internal IP.

If a request is made to `auth.domain.com` from **outside** the network, the **external** DNS (cloudflare, google,
etc...) resolves this to the external IP set in the DNS records.

!!! note 
    This doesn't happen with other repos (the ones
    at [awesome-home-kubernetes](https://github.com/k8s-at-home/awesome-home-kubernetes)) because they use
    a [split-horizon DNS](https://en.wikipedia.org/wiki/Split-horizon_DNS), meaning they have a DNS internal to their
    network that resolves queries to internal IPs and another one externaly that resolves queries to external IPs.

## The Solution

Set the `auth-url` to the internal `oauth2` service so that the application doesn't resolve the `auth-url` to an
external IP.

```yaml
annotations:
  nginx.ingress.kubernetes.io/auth-url: "http://oauth2-proxy.networking.svc.cluster.local/oauth2/auth"
  nginx.ingress.kubernetes.io/auth-signin: "https://auth.domain.com/oauth2/sign_in"
```

[^1]: [https://stackoverflow.com/a/60280114](https://stackoverflow.com/a/60280114)
