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
`k3sup install --ip 192.168.1.184 --user master --local-path ~/.kube/config --merge --context homelab --ssh-key ~/.ssh/id_ed25519`

Look into this guy for inspiration https://github.com/billimek/k8s-gitops