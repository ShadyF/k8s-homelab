# Restrict Port Forwarding to only allow Cloudflare IPs using OpenWRT

Default firewall rules only allow for one source IP to be defined when created a rule. Hence, there's two options when
you want to create a rule that uses multiple Source IPs:

1. Repeat the firewall multiple times
2. Use `ipset` (https://openwrt.org/docs/guide-user/firewall/fw3_configurations/fw3_config_ipset)

We're going with the second option as it's much easier.

In `/etc/config/firewall` add the following

```
config  ipset
        option  name            'cloudflareips'
        option  match           'src_net'
        option  storage         'hash' 
        option  enabled         '1'
        list    entry           '103.21.244.0/22'
        list    entry           '103.22.200.0/22'
        list    entry           '103.31.4.0/22'
        list    entry           '104.16.0.0/13'  
        list    entry           '104.24.0.0/14'
        list    entry           '108.162.192.0/18'
        list    entry           '131.0.72.0/22'
        list    entry           '141.101.64.0/18'
        list    entry           '162.158.0.0/15'
        list    entry           '172.64.0.0/13'
        list    entry           '173.245.48.0/20'
        list    entry           '188.114.96.0/20'
        list    entry           '190.93.240.0/20'
        list    entry           '197.234.240.0/22'
        list    entry           '198.41.128.0/17'
```

Now edit your port forwardings (called `redirect` in `/etc/config/firewall`) to utilize the newly created `ipset`

Again, in `/etc/config/firewall`

```
config redirect
        option target 'DNAT'
        option name 'KubeHTTP'
        option src 'wan'
        option ipset 'cloudflareips' # <- This like here
        option src_dport '80'
        option dest 'lan'
        option dest_ip '<internal_ip>'
        option dest_port '80'
        list proto 'tcp'

config redirect
        option target 'DNAT'
        option name 'KubeHTTPS'
        list proto 'tcp'
        option src 'wan'
        option ipset 'cloudflareips' # <- This like here
        option src_dport '443'
        option dest 'lan'
        option dest_ip '<internal_ip>'
        option dest_port '443'
```

Finally, reload the firewall by running `/etc/init.d/firewall reload`

[^1]: [https://openwrt.org/docs/guide-user/firewall/firewall_configuration](https://openwrt.org/docs/guide-user/firewall/firewall_configuration)