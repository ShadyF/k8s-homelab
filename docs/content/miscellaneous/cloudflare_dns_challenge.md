# Using cloudflare DNS challenge instead of basic acme challenge

First things first, you'll need to change your domain's DNS to cloudflare.

1. Use cloudflare nameservers instead of
   namecheap https://www.namecheap.com/support/knowledgebase/article.aspx/9607/2210/how-to-set-up-dns-records-for-your-domain-in-cloudflare-account/

See https://cert-manager.io/docs/configuration/acme/dns01/cloudflare/

##### Generating cloudflare API token

https://github.com/k8s-at-home/template-cluster-k3s#cloud-cloudflare-api-token

See https://www.reddit.com/r/selfhosted/comments/ga02px/you_should_probably_know_about_letsencrypt_dns/
