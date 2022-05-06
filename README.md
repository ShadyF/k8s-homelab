<div align="center">
<br/>
<img src="https://user-images.githubusercontent.com/6564442/167219151-928edaa8-fd73-45bb-9219-0a3da19e73f5.png" width="144px" height="144px"/>

### My K8s Homelab :computer:

##### Synced Using Flux <img src="https://avatars.githubusercontent.com/u/52158677?s=200&v=4" width="18px"> Updated using Renovate <img src="https://docs.renovatebot.com/assets/images/logo.png" width="18px">

[![k3s](https://img.shields.io/badge/k3s-v1.22.7-brightgreen?style=for-the-badge&logo=kubernetes&logoColor=white)](https://k3s.io/)
[![Website](https://img.shields.io/website?down_message=offline&label=homelab.shadyf.com&logo=readthedocs&logoColor=white&style=for-the-badge&up_message=online&url=https%3A%2F%2Fhomelab.shadyf.com)](https://homelab.shadyf.com)
![GitHub last commit](https://img.shields.io/github/last-commit/shadyf/k8s-homelab?logo=github&style=for-the-badge)
![Lines of code](https://img.shields.io/tokei/lines/github/ShadyF/k8s-homelab?label=lines&logo=codefactor&logoColor=white&style=for-the-badge)
</div>

## :book: Overview

This repository contains the kubernetes manifests of my homelab, synced using [Flux](https://github.com/fluxcd/flux2).

[Renovate](https://docs.renovatebot.com/) also scans this repo and create PRs whenever it finds a dependency update.

## :floppy_disk:Software

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

### Apps

List of the apps that are currently running on the cluster

- [Plex](https://www.plex.tv/): Home media solution. Like a selfhosted version of Netflix.
- [qBittorrent](https://www.qbittorrent.org/): Torrent Client.
- [Flood](https://github.com/jesec/flood): Modern UI for qBittorrent.
- [Syncthing](https://syncthing.net/): File synchronization program. Like a selfhosted Dropbox.
- [Hyperion](https://github.com/hyperion-project/hyperion.ng): Opensource ambient light software. Used to control smart
  LEDs I have around the house.

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

## :book: Documentation

Documentation for this repo is done using [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) and is
located in the `docs` directory.

The docs are automatically published via a CI job to https://homelab.shadyf.com.

## :hand: Acknowledgments

I'd love to give a huge shoutout to the awesome [k8s-at-home](https://github.com/k8s-at-home/) community. A lot of
inspiration came from the repos shared
at [awesome-home-kubernetes](https://github.com/k8s-at-home/awesome-home-kubernetes) repo.



