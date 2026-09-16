# Web-App Attack Methodology

The map that ties every web cheatsheet together. Web-app testing is one loop: **map the app →
follow each piece of user input to where it lands → attack by that sink → escalate the win.**
Almost every vuln class comes down to *"my input reached a dangerous place unsanitised."*

Use this page to decide **which cheatsheet** to open. Links point to the sheets in this folder.

---
---

# PART 1 — THE WORKFLOW (at a glance)

## The four phases

1. **Map** — spider the app, fingerprint the stack, list every input (params, headers, cookies,
   JSON, file uploads, path segments). Tools: Burp, `web-enumeration` (recon).
2. **Probe each input** — send a marker/metacharacter and watch *where it lands and what breaks*.
3. **Attack by sink** — the place your input ends up decides the vuln (see the table below).
4. **Escalate** — turn the bug into RCE, account takeover, data theft, or a pivot into the cloud/network.

## Decision: "where does my input go?" → which attack

| Your input lands in… | Symptom | Attack → cheatsheet |
|----------------------|---------|---------------------|
| HTML / the page | reflected/stored, renders as markup | **XSS** |
| A SQL query | quote breaks it, DB errors | **SQLi** (+ **sqli-syntax**) |
| A NoSQL query | JSON/operator injection works | **NoSQL injection** |
| An OS shell command | metachars run commands | **Command injection** |
| A file path (include) | path traversal reads files | **LFI / RFI** |
| A server-side URL fetch | server requests your URL | **SSRF** |
| A template engine | `{{7*7}}` → `49` | **SSTI** |
| An XML parser | entities are resolved | **XXE** |
| An object ID / reference | changing it exposes others' data | **IDOR / access control** |
| A state-changing request | no anti-CSRF token | **CSRF** |
| An auth token | JWT `alg`/signature weak | **JWT attacks** |
| An uploaded file | server stores + executes it | **File upload bypass** |

## The tool that runs through all of it

**Burp Suite** — proxy every request, then **Repeater** (hand-test one endpoint) and **Intruder**
(fuzz/brute). See `burp-suite/`.

---
---

# PART 2 — PER-PHASE DETAIL

## Phase 1 — Map the application

```
□ Proxy the whole app through Burp; browse every feature (populate the site map)
□ Fingerprint: server, framework, language (Wappalyzer, headers, error pages, cookies)
□ Enumerate content: dirs, files, params, vhosts   → see 01-recon/web-enumeration (ffuf/feroxbuster)
□ List every input surface:
    - URL query params, path segments
    - POST bodies (form + JSON + multipart)
    - Headers (Cookie, User-Agent, Referer, X-Forwarded-For, Host)
    - File uploads, WebSockets, GraphQL/REST endpoints
□ Note auth boundaries: which pages need a session, which roles exist (user vs admin)
```

## Phase 2 — Probe each input

Send a **polyglot marker** and watch the response + DOM + timing:

```
test'"<x>{{7*7}}${7*7}|id;sleep0
```

Read the reaction:

```
'"  → SQL error / broken HTML         → SQLi / XSS
<x> renders as a tag                  → XSS
{{7*7}} or ${7*7} → 49                → SSTI
reflected in a server-side fetch      → SSRF
path/file behaviour changes           → LFI / RFI
timing/OOB on ; | `                   → command injection
```

## Phase 3 — Attack by sink

Open the matching cheatsheet from the Part 1 table. Each one follows the same shape:
**Overview → Detailed walkthrough → Payload arsenal.**

## Phase 4 — Escalate (turn the bug into impact)

```
XSS            → steal session / act as victim / account takeover
SQLi           → dump creds → crack (hashcat/john) → reuse; or --os-shell → RCE
Cmd injection  → reverse shell → local privesc (linux/windows-privesc)
LFI/RFI, upload, SSTI, XXE → RCE → foothold
SSRF           → cloud metadata → IAM creds → cloud account (azure/entra sheets)
IDOR / JWT / auth → horizontal/vertical access → admin → takeover
```

**Then pivot:** looted creds → other services (SMB/SSH/web admin); foothold → internal network
(`06-network/pivoting-tunneling`); cloud creds → `07-cloud`.

---
---

# PART 3 — QUICK REFERENCE

## Coverage map (this folder)

| Class | Sheet |
|-------|-------|
| Injection — SQL | `sqli`, `sqli-syntax` |
| Injection — NoSQL | `nosql-injection` |
| Injection — OS command | `command-injection` |
| Injection — template | `ssti` |
| Injection — XML | `xxe` |
| Client-side | `xss`, `csrf` |
| File / path | `lfi-rfi`, `file-upload-bypass` |
| Server-side request | `ssrf` |
| Access control | `idor-access-control`, `jwt-attacks` |
| Tooling | `burp-suite/` |

## OWASP Top 10 (2021) → sheets

```
A01 Broken Access Control   → idor-access-control, jwt-attacks, csrf
A03 Injection               → sqli, xss, command-injection, nosql-injection, ssti
A05 Security Misconfig      → file-upload-bypass, xxe
A06/A08 Vulnerable/Integrity→ file-upload-bypass, (deserialization — future)
A10 SSRF                    → ssrf
```

---

**Key idea:** every web bug is the same story — untrusted input reaches a place that trusts it
(a query, a shell, a parser, a file path, a URL, a token). Map the app, follow each input to its
sink, attack by that sink, then escalate. This page picks the door; the individual cheatsheets
kick it in.
