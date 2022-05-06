# Getting MetalLB to work on Raspberry Pi 4's Wifi

## Problem
MetalLB in ARP mode doesn't work on Raspberry Pi if the Wifi interface is used.

The exact details of the issue can be found [here](https://github.com/raspberrypi/linux/issues/2677)
## Solution
We'll need to change the Wifi adapter to use promiscuous mode. This can be done by running the following command:

```bash
ip link set wlan0 promisc on
```

However, you'll have to run this command after each reboot. To have this run automatically on startup, we can use `crontab`.

```bash
crontab -e

# Add the following line to crontab
@reboot ip link set wlan0 promisc on
```