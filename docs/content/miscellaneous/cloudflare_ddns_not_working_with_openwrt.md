# Cloudflare DDNS not working with OpenWRT based routers

Solution to the problem can be
found [in this forum post](https://community.cloudflare.com/t/ddns-api-not-working/22409 )

TLDR - Should be `ip@domain.com` rather than `ip.domain.com`

## `proxied` parameter not working when using [Gargoyle](https://www.gargoyle-router.com/)

Using [Gargoyle](https://www.gargoyle-router.com/) v1.12.0, you'll encounter another issue, the DDNS record won't be
proxied. This is because the cloudflare-dns script doesn't send the `proxied` parameter which defaults to `false`

To fix this, we're going to have to edit the Cloudflare DDNS script

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