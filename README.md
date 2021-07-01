#### Kubectl cheatsheet commands

```bash
# To change context
kubectl config use-context homelab2 
```

#### Which templating tool to use?

https://learnk8s.io/templating-yaml-with-code

#### Settings up raspberry pi

https://levelup.gitconnected.com/step-by-step-slow-guide-kubernetes-cluster-on-raspberry-pi-4b-part-1-6e4179c89cbc

We need to setup Linux Control Groups that are used for resource monitoring and isolation that are needed by Kubernetes.

`sudo nano /boot/firmware/cmdline.txt`

Add the following at the end of the line

`cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory`

configure user to execute commands without sudo password

```bash
sudo visudo
master ALL=(ALL) NOPASSWD:ALL
```

install k3sup from https://github.com/alexellis/k3sup

k3sup needs that the user on the node to be able to execture sudo command without password

```bash
sudo visudo
master ALL=(ALL) NOPASSWD:ALL
```

run k3sup from local machine
`k3sup install --ip 192.168.1.184 --user master --local-path ~/.kube/config --merge --context homelab --ssh-key ~/.ssh/id_ed25519 --k3s-channel latest --no-extras`

To get the kubeconfig, add `--skip-install` at the end

Look into this guy for inspiration https://github.com/billimek/k8s-gitops

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
`sops --encrypt --in-place flux-system/cluster-secrets.yaml `

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

### To make pod not crash

```yaml
command: [ 'sleep' ]
args: [ 'infinity' ]
```

### Doing SD backups

https://www.raspberrypi.org/documentation/linux/filesystem/backup.md

### Add wifi to raspi

https://itsfoss.com/connect-wifi-terminal-ubuntu/

TLDR:

```bash
sudo nano /etc/netplan/50-cloud-init.yaml
```

then paste in the following under `networks`

```yaml
wifis:
  wlan0:
    dhcp4: true
    optional: true
    access-points:
      "SSID_name":
        password: "WiFi_password"
```

then type in the following command

`sudo netplan apply`

### Changing default shell

```bash
chsh --shell /usr/bin/fish
```

### Get RPI cpu temp in ubuntu

`cat /sys/class/thermal/thermal_zone0/temp`

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

### Reconciling using flux

```bash
# Reconcile gitcontroller (given that flux-system is the name of the gitcontroller)
flux reconcile source git flux-system

# Reconcile kustomization (given that apps is the name of the kustomization controller)
flux reconcile kustomization apps

# Reconcile a helm release
flux reconcile helmrelease oauth2-proxy -n networking
```

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

#### Settings up nfs mounting in windows

https://graspingtech.com/mount-nfs-share-windows-10/

### To see the data created in a longhorn volume

1. use `lsblk -f` or `df -H` to find your desired PVC path
2. `cd` into it

### VPN with kube

https://github.com/bjw-s/k8s-gitops/blob/10dd2f3bd358bd694b0aaed8b34618806e64842a/cluster/apps/vpn/vpn-gateway/helmrelease.yaml

https://github.com/seanrclayton/kub_yaml/blob/master/pia-deluge-vpncheckkillswitch.yaml

### Settings up log2ram to reduce sd card / ssd writes

https://github.com/azlux/log2ram

### Fixing oauth2 proxy slowing down everything

https://stackoverflow.com/questions/58997958/oauth2-proxy-authentication-calls-slow-on-kubernetes-cluster-with-auth-annotatio

TLDR:
When auth-url is set to auth.domain.com, this means that the request goes outside of the cluster (so called hairpin
mode), and goes back via External IP of Ingress that routes to internal ClusterIP Service (which adds extra hops),
instead going directly with ClusterIP/Service DNS name (you stay within Kubernetes cluster)

To solve this, set the `auth-url `to the internal `oauth2` service.

**_Note:_** This doesn't happen with other repos (ones in references) because they use a split-horizon DNS, meaning they
have a DNS internal to their network that resolves queries to internal IPs and another one externaly that resolves
queries to external IPs.

If a request is made to `auth.domain.com` from **inside** the internal network, the **internal** DNS resolves this to an
internal IP.

If a request is made to `auth.domain.com` from **outside** the network, the **external** DNS (cloudflare, google,
etc...) resolves this to the external IP set in the DNS records.

### Probes explained

https://developers.redhat.com/blog/2020/11/10/you-probably-need-liveness-and-readiness-probes#