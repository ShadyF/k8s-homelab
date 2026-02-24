---
apply: always
---

# Ingress and Networking Guidelines

- **Exposure Prompt:** Before generating an `Ingress` manifest, ALWAYS ask the user whether the application will be exposed outside the LAN.
- **Ingress Class Configuration:** 
  - If the app is NOT exposed outside the LAN (or if the user doesn't specify), use the default `ingressClassName: internal`.
  - If the app IS exposed outside the LAN, use `ingressClassName: external`.
- **Cert-Manager & External-DNS:** Always include the necessary annotations for `cert-manager` (e.g., `cert-manager.io/cluster-issuer`) to automate TLS certificates, and `external-dns` if a DNS record needs to be created.
- **HTTPS Only:** Ensure that TLS is configured for all exposed services. Do not expose services over plain HTTP.
- **Authentication:** If an application lacks built-in authentication and is exposed externally, suggest applying the necessary Nginx annotations to protect the route using the existing `oauth2-proxy` setup.