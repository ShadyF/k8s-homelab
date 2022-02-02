#### Which templating tool to use?

https://learnk8s.io/templating-yaml-with-code

#### Flux installation

1. Make a personal token on github with repo privelages
2. Install flux locally (flux-bin in AUR)
3. Export GITHUB_TOKEN to env
4. Run the following command

```bash
flux bootstrap github \                                                                                                                                                                                  
--owner=ShadyF \
--repository=homelab \
--branch=master \
--path=cluster/base \
--personal
```

#### Enable sops for secret managment

https://blog.sldk.de/2021/03/handling-secrets-in-flux-v2-repositories-with-sops/

To encrypt data
`sops --encrypt --in-place flux-system/cluster-secrets.yaml`

#### Exporting gpg key from one machine to another
https://makandracards.com/makandra-orga/37763-gpg-extract-private-key-and-import-on-different-machine

#### Get Kubelet config

```bash
kubectl proxy --port=8001
NODE_NAME="k8-m1"; curl -sSL "http://localhost:8001/api/v1/nodes/${NODE_NAME}/proxy/configz" | jq '.kubeletconfig|.kind="KubeletConfiguration"|.apiVersion="kubelet.config.k8s.io/v1beta1"' > kubelet_configz_${NODE_NAME}
```

#### Install VPA

https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler

### Tunneling wireguard via websockets

https://kirill888.github.io/notes/wireguard-via-websocket/

### Buildx

https://www.docker.com/blog/multi-arch-images/

### Create a docker registry secret

`kubectl create secret docker-registry regcred --docker-server="https://index.docker.io/v1/" --docker-username=<username> --docker-password=<password> --docker-email=<email> --dry-run=client -oyaml > regcred.yaml`

### Doing SD backups

https://www.raspberrypi.org/documentation/linux/filesystem/backup.md

### Settings up SSD

https://jamesachambers.com/raspberry-pi-4-usb-boot-config-guide-for-ssd-flash-drives/

### Getting Metallb to work on raspberry pi 4's wifi

See https://github.com/raspberrypi/linux/issues/2677

Add the following to crontab to enable promiscuous mode on startup

```bash
sudo crontab -e

# Add the following line to crontab (no need for sudo since we invoked crontab with sudo)
ip link set wlan0 promisc on
```

### Enable TRIM while using ssd

See https://wiki.archlinux.org/title/Solid_state_drive

```bash
sudo systemctl enable fstrim.timer
sudo systemctl start fstrim.timer
```

### Using cloudflare DNS challenge instead of basic acme challenge

First things first, you'll need to change your domain's DNS to cloudflare.

1. Use cloudflare nameservers instead of
   namecheap https://www.namecheap.com/support/knowledgebase/article.aspx/9607/2210/how-to-set-up-dns-records-for-your-domain-in-cloudflare-account/

See https://cert-manager.io/docs/configuration/acme/dns01/cloudflare/

##### Generating cloudflare API token

https://github.com/k8s-at-home/template-cluster-k3s#cloud-cloudflare-api-token

See https://www.reddit.com/r/selfhosted/comments/ga02px/you_should_probably_know_about_letsencrypt_dns/

### Issues regarding raspberry pi 4 freezing after certain amount of time

Added usb-quirks as an initial solution

https://github.com/ubuntu/microk8s/issues/2280

https://github.com/k3s-io/k3s/issues/1297

### Remove useless ubuntu stuff

```bash
# Remove snapd, takes up CPU and not needed on a kube node
sudo apt autoremove --purge snapd
```

### Making cloudflare DDNS work with gargoyle / openwrt based routers

https://community.cloudflare.com/t/ddns-api-not-working/22409
TLDR - Should be `ip@domain.com` rather than `ip.domain.com`
However, using gargoyle v1.12.0, you'll encounter another issue, the DDNS record won't be proxied. This is because the
cloudflare-dns script doesn't send the `proxied` parameter which defaults to `false`

To fix this, we're going to have to edit the cloudflare ddns script

```bash
# ssh into gargoyle router
ssh root@192.168.1.1 -i gargoyle

# edit cloudflare ddns script with vim
vim /plugin_root/usr/lib/ddns-gargoyle/cloudflare-ddns-helper.sh

# Go down to the end of the file and you should find this line
{"id":"$ZONEID","type":"A","name":"$HOST","content":"$LOCAL_IP"}

# Add to it the proxied parameter so that it would be like this 
{"id":"$ZONEID","type":"A","name":"$HOST","content":"$LOCAL_IP","proxied":true}
```

### Creating an NFS server

https://www.tecmint.com/install-nfs-server-on-ubuntu/

https://www.rancher.co.jp/docs/rancher/v2.x/en/cluster-admin/volumes-and-storage/examples/nfs/

https://linuxize.com/post/how-to-mount-an-nfs-share-in-linux/

#### Mounting nfs volume in linux on startup

TLDR, add the following to /etc/fstab
`192.168.1.xxx:/srv/nfs /home/<user>/nfs  nfs      defaults    0       0`

#### Settings up nfs mounting in windows

https://docs.datafabric.hpe.com/62/AdministratorGuide/MountingNFSonWindowsClient.html
**NOTE:** Use `AnonymousUID` and `AnonymousGID` instead of `AnonymousUid` and `AnonymousGid` when setting UID and GID
values in windows registry editor

### To see the data created in a longhorn volume

1. use `lsblk -f` or `df -H` to find your desired PVC path
2. `cd` into it

### VPN with kube

https://github.com/bjw-s/k8s-gitops/blob/10dd2f3bd358bd694b0aaed8b34618806e64842a/cluster/apps/vpn/vpn-gateway/helmrelease.yaml

https://github.com/seanrclayton/kub_yaml/blob/master/pia-deluge-vpncheckkillswitch.yaml

### Settings up log2ram to reduce sd card / ssd writes

https://github.com/azlux/log2ram

### Probes explained

https://developers.redhat.com/blog/2020/11/10/you-probably-need-liveness-and-readiness-probes#

https://blog.devgenius.io/understanding-kubernetes-probes-5daaff67599a (Great article)

TL/DR: there is no default readiness probe ("should I send this pod traffic?") and the default liveness probe ("should I
kill this pod?") is just whether the container is still running.

### Issues with PPPoE using OpenWRT

https://www.onetransistor.eu/2017/04/wan-port-openwrt-lede-vlan.html?m=1

### Setting up wireguard over wstunnel

https://kirill888.github.io/notes/wireguard-via-websocket/

_NOTE: The script in the above page doesn't use ip route, which won't work on modern linux machine.
A modified version of wstunnel.sh can be found here https://github.com/jnsgruk/wireguard-over-wss_

Don't forget to download `wstunnel` as a binary and copy it to `/usr/local/bin/wstunnel` and running `sudo chmod +x /usr/local/bin/wstunnel`

