# Setting up Raspberry Pi for k3s

!!!info 
    The following guide was heavily inspired / has snippets
    from [this medium tutorial](https://levelup.gitconnected.com/step-by-step-slow-guide-kubernetes-cluster-on-raspberry-pi-4b-part-1-6e4179c89cbc)

!!! info 
    This guide assumes that you have already installed Ubuntu Server 21.04 on your Raspberry Pi

## Logging into Raspberry Pi via SSH

First things first, we need to login to our Raspberry Pi before doing anything. If this is your first time connecting to
it, you'll need to connect your Raspberry Pi to your router via ethernet cable. We'll enable Wi-Fi later on in this
section.

From your router's dashboard, you'll need to figure out which IP was assigned to the Raspberry Pi. The rest of this
guide will assume the Raspberry Pi has an internal IP of `192.168.1.100` assigned to it via the router's DHCP.

Once you have your IP, time to SSH into this bad boy.

```shell
ssh ubuntu@192.168.1.100
```

!!! note 
    The default username and password for a fresh Ubuntu Server 21.04 install should be `ubuntu` / `ubuntu`. Don't
    worry, you'll be prompted to change this once you login for the first time.

## Creating a new user

Next up, let's create a new user that represents what this node will be doing. Assuming this Raspberry Pi will be our
master node, we're going to create a new user called `master`

```shell
sudo adduser master
```

Let's now take all the groups that belonged to the `ubuntu` and add them to our newly created `master` user

```shell
# Running the following command while logged in as ubuntu
# should give you a list of all the groups the ubuntu user belongs to
groups

# Assign the same groups to master
sudo usermod -a -G adm,dialout,cdrom,floppy,sudo,audio,dip,video,plugdev,netdev,lxd master
```

Before deleting the `ubuntu` user, let's first make sure we can login with `master`

```shell
ssh master@192.168.1.100
```

If all goes well, we should can now safely remove the default user

```shell
sudo deluser --remove-home ubuntu
```

## Change default hostname

Let's change the hostname from the default to something more meaningful. Since this node will be our master node, we're
going to change it to `k8-m1`

```shell
sudo hostnamectl set-hostname k8-m1
```

Also, since Ubuntu Server 21.04 uses `cloud-init`, we're going to have the following line in `/etc/cloud/cloud.cfg`

```shell
sudo nano /etc/cloud/cloud.cfg
```

```yaml
# Change preserve_hostname to true
preserve_hostname: true
```

## Securing SSH access

!!! note 
    This section assumes that you're familiar with Key-Based authentication and that you already have a public /
    private key pair.

    If not, you can generate one using the following instructions found
    in [this link](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#generating-a-new-ssh-key)

Currently, anyone can ssh into our Raspberry Pi if they have our username and password. We're going to change this from
password-based authentication to key-based authentication, for added security.

From your local machine, Let's copy our key to the master node

```shell
# This copies the public key (at ~/.ssh/id_k8-m1) to the master node
ssh-copy-id -i ~/.ssh/id_k8-m1 master@192.168.1.100
```

If successful, we should check if we can ssh into the master node with our key, without entering a password

```shell
ssh -i ~/.ssh/id_k8-m1 master@192.168.1.100
```

Next up, let's tighten up our ssh config so that we disable password login, enable key-based authentications and disable
the ability to login as `root`

```shell
sudo nano /etc/ssh/sshd_config
```

Change the following lines

```
From:
#PermitRootLogin prohibit-password
#PasswordAuthentication yes
#PubkeyAuthentication yes

To:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

Finally, restart the sshd daemon so that the changes take effect

```shell
sudo systemctl restart sshd.service
```

## Setup Linux Control Groups

We need to setup Linux Control Groups that are used for resource monitoring and isolation that are needed by Kubernetes.

```shell
sudo nano /boot/firmware/cmdline.txt
```

Add the following at the end of the line

```
cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory
```

## Adding password-less `sudo` to our user

!!! note
    We need our user to have password-less `sudo` so that `k3sup` would work correctly in the next step

```
# Run the following from your shell
sudo visudo

# Add the following at the end of the file
master ALL=(ALL) NOPASSWD:ALL
```

## (Optional) Enable Wi-Fi on your Raspberry Pi
!!! warning 
    It's recommended to connect the your cluster nodes via a wired connection for a general stability, and an
    overall better experience

This section will be about how to connect your Raspberry Pi to your network via WiFi[^1]

First off, edit the following file

```shell
sudo nano /etc/netplan/50-cloud-init.yaml
```

Paste in the following under `networks` (don't forget to replace the `SSID_name` and `WiFi_password` placeholders)

```yaml
wifis:
  wlan0:
    dhcp4: true
    optional: true
    access-points:
      "SSID_name":
        password: "WiFi_password"
```

Finally, apply the new netplan for it to take effect

```shell
sudo netplan apply
```

[^1]: [https://itsfoss.com/connect-wifi-terminal-ubuntu/](https://itsfoss.com/connect-wifi-terminal-ubuntu/)