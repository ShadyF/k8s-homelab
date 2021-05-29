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
flux bootstrap github \                                                                                                                                                                                  Thu 13 May 2021 05:29:10 PM UTC
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
command: ['sleep']
args: ['infinity']
```