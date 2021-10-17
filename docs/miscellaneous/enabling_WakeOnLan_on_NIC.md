# Enabling WakeOnLan on NIC

!!! info 
    Adapted from [https://www.techrepublic.com/article/how-to-enable-wake-on-lan-in-ubuntu-server-18-04/](https://www.techrepublic.com/article/how-to-enable-wake-on-lan-in-ubuntu-server-18-04/)

To enable WOL on a NIC in ubuntu, we're going to have to create a systemd service. Start by running the following command
```shell
sudo nano /etc/systemd/system/wol.service
```

In that file, paste the following
```
[Unit]
Description=Configure Wake On LAN

[Service]
Type=oneshot
ExecStart=/sbin/ethtool -s INTERFACE wol g

[Install]
WantedBy=basic.target
```

Afterwards, we need to start the systemd service to take effect immediately and enable it so that it runs on each startup
```shell
# start the service for the current session
sudo systemctl start wol.service

# enable the service to run on each startup
sudo systemctl enable wol.service
```