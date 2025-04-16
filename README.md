<div align="center">
<br/>
<img src="https://user-images.githubusercontent.com/6564442/167219151-928edaa8-fd73-45bb-9219-0a3da19e73f5.png" width="144px" height="144px"/>

### My K8s Homelab :computer:

#### Synced Using Flux <img src="https://avatars.githubusercontent.com/u/52158677?s=200&v=4" width="18px"> Updated using Renovate <img src="https://docs.renovatebot.com/assets/images/logo.png" width="18px">

[![k3s](https://img.shields.io/badge/k3s-v1.24.3+k3s1-brightgreen?style=for-the-badge&logo=kubernetes&logoColor=white)](https://k3s.io/)
[![Website](https://img.shields.io/website?down_message=offline&label=homelab.shadyf.com&logo=readthedocs&logoColor=white&style=for-the-badge&up_message=online&url=https%3A%2F%2Fhomelab.shadyf.com)](https://homelab.shadyf.com)
![GitHub last commit](https://img.shields.io/github/last-commit/shadyf/k8s-homelab?logo=github&style=for-the-badge)
![Lines of code](https://img.shields.io/tokei/lines/github/ShadyF/k8s-homelab?label=lines&logo=codefactor&logoColor=white&style=for-the-badge)
</div>

## :book: Overview

This repository contains the kubernetes manifests of my homelab, synced using [Flux](https://github.com/fluxcd/flux2).

[Renovate](https://docs.renovatebot.com/) also scans this repo and create PRs whenever it finds a dependency update.

## :floppy_disk: Software

My homelab uses [k3s](https://k3s.io/) on top of bare-metal hardware running Ubuntu Server 21.04. Hardware specs can be
found below.

### Folder Structure

K8s manifests that are actually synced with the homelab can be found under the `cluster` directory. Documentation and
website files are found in the `docs` directory

Inside the cluster directory, here's how everything is structured:

- **base**: Flux's entrypoint. Mainly stuff created by bootstrapping flux + some additional functionalities
- **crds**: Contains any CRDs that need to exist before anything else gets applied.
- **apps**: Contains both essential cluster components and common applications. Grouped by namespace. Depends on crds.

_Note: Flux always syncs these directories in the above order. (base -> crds -> apps)_

### Essential Cluster Components

- [MetalLB](https://metallb.universe.tf/): Bare metal implementation of a network load balancer.
- [Ingress NGINX](https://kubernetes.github.io/ingress-nginx/): Ingress controller to expose HTTP traffic to pods over
  DNS.
- [cert-manager](https://cert-manager.io/docs/): Creating SSL certificates via Letsencrypt for
  externally exposed services.
- [OAuth2 Proxy](https://github.com/oauth2-proxy/oauth2-proxy): Handles authentication of externally exposed services.
- [ExternalDNS](https://github.com/kubernetes-sigs/external-dns): Managing DNS records using my DNS provider. Needed so
  that I don't have to create DNS records whenever I create / remove a new service.
- [SOPS](https://github.com/mozilla/sops): Needed for secret management. Sensitive data is encrypted in the git repo and
  is decrypted by Flux when they're synced with the cluster.
- [Longhorn](https://github.com/longhorn/longhorn): Distributed block storage.
- [CrowdSec](https://www.crowdsec.net/): Security automation tool that detects and responds to attacks.
- [Kured](https://github.com/weaveworks/kured): Kubernetes Reboot Daemon that performs safe automatic node reboots.
- [Descheduler](https://github.com/kubernetes-sigs/descheduler): Pod descheduler for Kubernetes to improve scheduling.
- [Node Feature Discovery](https://github.com/kubernetes-sigs/node-feature-discovery): Detects hardware features in nodes.
- [Intel Device Plugins](https://github.com/intel/intel-device-plugins-for-kubernetes): Plugins for Intel hardware.
- [Reloader](https://github.com/stakater/Reloader): Auto-reload ConfigMaps and Secrets when they change.

#### Monitoring Stack
- [Prometheus](https://prometheus.io/) (via kube-prometheus-stack): Monitoring and alerting toolkit.
- [Grafana](https://grafana.com/): Analytics and monitoring dashboards.
- [Loki](https://grafana.com/oss/loki/): Log aggregation system.
- [Promtail](https://grafana.com/docs/loki/latest/clients/promtail/): Agent that ships logs to Loki.
- [ntfy](https://ntfy.sh/): Push notification service for alerts.


### Apps

List of applications running on the cluster:

#### Media Management
- [Plex](https://www.plex.tv/): Home media solution. Like a selfhosted version of Netflix.
- [qBittorrent](https://www.qbittorrent.org/): Torrent Client.
- [Flood](https://github.com/jesec/flood): Modern UI for qBittorrent.
- [Sonarr](https://sonarr.tv/): TV show management and automation.
- [Radarr](https://radarr.video/): Movie management and automation.
- [Readarr](https://readarr.com/): Book management and automation.
- [Prowlarr](https://github.com/Prowlarr/Prowlarr): Indexer manager/proxy for the *arr stack.
- [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr): Proxy server to bypass Cloudflare protection.

#### Productivity & Personal Tools
- [Syncthing](https://syncthing.net/): File synchronization program. Like a selfhosted Dropbox.
- [Hyperion](https://github.com/hyperion-project/hyperion.ng): Opensource ambient light software. Used to control smart
  LEDs I have around the house.
- [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx): Document management system.
- [Mealie](https://hay-kot.github.io/mealie/): Recipe management and meal planning.
- [n8n](https://n8n.io/): Workflow automation tool.
- [Actual Budget](https://actualbudget.com/): Personal finance and budgeting tool.
- [YOURLS](https://yourls.org/): URL shortener.
- [V-Rising](https://playvrising.com/): Game server.

#### VPN & Network Tools
- [WireGuard](https://www.wireguard.com/): Modern VPN server.
- [Shadowsocks](https://shadowsocks.org/): Secure SOCKS5 proxy.
- [WSTunnel](https://github.com/erebe/wstunnel): Tunnel over websocket protocol.

## :computer: Infrastructure

My k3s cluster currently has the following hardware

- 1x Old Computer I had laying around with the following specs

  | Component    | Details |
  |--------|---------------------------------------------|
  | CPU    | Intel Core i5-2500K (Overclocked to **4.5GHz**) |
  | Cooler | Cooler Master Hyper 212 EVO                 |
  | RAM    | 8GB DDR3                                    |
  | GPU    | AMD Radeon HD 6950                          |
  | PSU    | Antec 650W                                  |

- 1x Raspberry Pi 4 (8GB RAM)
- 1x Asus Zenbook UX305UA

## Uptime Monitoring
Uptime monitoring is done via [UptimeRobot](https://stats.uptimerobot.com/DAmr6ToN03).

UptimeRobot essentially ping / send requests to each externally exposed service I have configured and
sends out a push notification to my mobile whenever a service goes down.

Quite useful!

Link to the status page is [here](https://stats.uptimerobot.com/DAmr6ToN03).

![Status Page](https://user-images.githubusercontent.com/6564442/190654435-718f1a03-8134-4ec8-86f1-38817228e73e.png)

## :book: Documentation

Documentation for this repo is done using [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) and is
located in the `docs` directory.

The docs are automatically published via a CI job to https://homelab.shadyf.com.

## :hand: Acknowledgments

I'd love to give a huge shoutout to the awesome [k8s-at-home](https://github.com/k8s-at-home/) community. A lot of
inspiration came from the repos shared
at [awesome-home-kubernetes](https://github.com/k8s-at-home/awesome-home-kubernetes) repo.
