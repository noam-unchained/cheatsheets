Windows AD Attack Chain - Cheat Sheet

A decision-tree walkthrough of a full AD engagement.
Click any [tool link] to jump to its cheatsheet, then come back here
and continue down the chain.


========================================================================
 PHASE 0 — PREP
========================================================================

Before touching the network:

  □ Set up your C2               → [Sliver](../../../09-c2-frameworks/sliver/sliver.md)
  □ Prep file-transfer methods   → [File Transfers](../../../00-general/file-transfers/file-transfers.md)
  □ Start your notes — log every cred, host, and path


========================================================================
 PHASE 1 — INITIAL ACCESS
========================================================================

  Are you already on the internal network?
  │
  ├─ YES → skip to Phase 2
  │
  └─ NO  → get in:
           ├─ Phishing?    → [AitM Phishing](../../../02-initial-access/aitm-phishing/aitm-phishing.md)
           │                  [Evilginx](../../../02-initial-access/evilginx/evilginx.md)
           ├─ Web app?     → [SQLi](../../../02-initial-access/web-app/sqli/sqli.md)
           │                  [Command Injection](../../../02-initial-access/web-app/command-injection/command-injection.md)
           │                  [File Upload](../../../02-initial-access/web-app/file-upload-bypass/file-upload-bypass.md)
           │                  [LFI/RFI](../../../02-initial-access/web-app/lfi-rfi/lfi-rfi.md)
           └─ Exposed svc? → exploit it, get a shell

  Got a shell or callback? → Phase 2.


========================================================================
 PHASE 2 — WHERE AM I?
========================================================================

  Run on every new host you land on.
  Full local enum commands → [Windows Local Enum](../../../01-recon-enumeration/windows-local/windows-local.md)

  Q1: Am I local admin?
  │   whoami /priv, whoami /groups
  │
  ├─ YES → skip to Phase 4 (dump creds)
  └─ NO  → Phase 3 (privesc)

  Q2: Is Defender / EDR running?
  │   tasklist → MsMpEng.exe, Sysmon, CrowdStrike…
  │
  ├─ YES → bypass AMSI before any PowerShell tooling
  │        → [AV / AMSI Bypass](../../../08-evasion/av-amsi-bypass/av-amsi-bypass.md)
  └─ NO  → proceed freely

  Q3: Can I reach the DC and other subnets?
  │
  ├─ YES → continue
  └─ NO  → set up a tunnel
           → [Pivoting & Tunneling](../../../06-network/pivoting-tunneling/pivoting-tunneling.md)


========================================================================
 PHASE 3 — LOCAL PRIVESC
========================================================================

  Only if you are NOT local admin. Pick your path:
  Full commands → [Windows Privesc](../../../03-post-exploitation/windows-privesc/windows-privesc.md)

  Have SeImpersonatePrivilege?
  ├─ YES → Potato attacks (GodPotato, PrintSpoofer)
  │
  Weak service permissions / unquoted paths?
  ├─ YES → service-based privesc
  │
  Stored creds? (cmdkey /list)
  ├─ YES → runas /savecred
  │
  AlwaysInstallElevated?
  ├─ YES → MSI privesc
  │
  Nothing works locally?
  └─ try lateral movement (Phase 5) to a box where you ARE admin

  Got local admin? → Phase 4.


========================================================================
 PHASE 4 — DUMP CREDENTIALS
========================================================================

  *** Is Defender / AMSI active? ***
  ├─ YES → bypass first → [AV / AMSI Bypass](../../../08-evasion/av-amsi-bypass/av-amsi-bypass.md)
  └─ NO  → proceed

  Dump LSASS (hashes, tickets, plaintext):
    → [LSASS Dumping](../../credential-abuse/lsass-dumping/lsass-dumping.md)

  Dump SAM (local account hashes):
    → secretsdump / reg save

  Hunt for saved creds, DPAPI, browser passwords, vaults:
    → [Credential Hunting](../../../03-post-exploitation/credential-hunting/credential-hunting.md)

  Cached domain creds (DCC2)? Crack them offline:
    → [Hashcat](../../../00-general/password-cracking/hashcat/hashcat.md)
    → [John](../../../00-general/password-cracking/john/john.md)

  What did you get?
  │
  ├─ NTLM hash      → Phase 5 (pass-the-hash)
  ├─ Kerberos TGT   → Phase 5 (pass-the-ticket)
  ├─ Cleartext pass  → Phase 5 (direct auth / spraying)
  └─ Nothing useful  → Phase 6 (AD enum for other paths)


========================================================================
 PHASE 5 — LATERAL MOVEMENT
========================================================================

  Based on what you hold:

  Have an NTLM hash?
    → [Pass-the-Hash](../../credential-abuse/pass-the-hash/pass-the-hash.md)

  Have a Kerberos ticket?
    → [Pass-the-Ticket](../../credential-abuse/pass-the-ticket/pass-the-ticket.md)

  Have a cleartext password?
    → nxc smb/winrm/rdp directly
    → [Password Spraying](../../credential-abuse/password-spraying/password-spraying.md) across the domain

  Where to move next?
  │
  ├─ Hosts where your creds are local admin (nxc --shares to check)
  ├─ High-value targets: DC, file servers, SCCM, ADCS, DB servers
  ├─ Hosts with logged-in privileged users (check BloodHound)
  │
  Need to reach another subnet?
    → [Pivoting & Tunneling](../../../06-network/pivoting-tunneling/pivoting-tunneling.md)

  ┌────────────────────────────────────────────┐
  │  Every new host → go back to Phase 2.      │
  │  Land → Enum → Dump → Move → Repeat.       │
  └────────────────────────────────────────────┘


========================================================================
 PHASE 6 — AD ENUMERATION & ESCALATION PATHS
========================================================================

  *** Is AMSI active? SharpHound and PowerView will get caught. ***
  ├─ YES → bypass first → [AV / AMSI Bypass](../../../08-evasion/av-amsi-bypass/av-amsi-bypass.md)
  └─ NO  → proceed

  Map the domain:
    → [BloodHound](../../enumeration/bloodhound/bloodhound.md)
    → [LDAP Enumeration](../../enumeration/ldap-enumeration/ldap-enumeration.md)
    → [Windows AD Enum](../../enumeration/windows-ad/windows-enumeration.md)

  Look for these escalation paths:

  Kerberoastable SPN on a privileged account?
    → [Kerberoasting](../../kerberos/kerberoasting/kerberoasting.md)

  AS-REP Roastable account (no preauth)?
    → [AS-REP Roasting](../../kerberos/asrep-roasting/asrep-roasting.md)

  Misconfigured ADCS template (ESC1–ESC8)?
    → [ADCS ESC Attacks](../../kerberos/adcs-esc-attacks/adcs-esc-attacks.md)

  Delegation abuse (unconstrained / constrained / RBCD)?
    → [Delegation Abuse](../../kerberos/delegation-abuse/delegation-abuse.md)

  Writable GPO linked to high-priv OU?
    → [GPO Abuse](../../gpo-abuse/gpo-abuse.md)

  Can write msDS-KeyCredentialLink?
    → [Shadow Credentials](../../credential-abuse/shadow-credentials/shadow-credentials.md)

  SCCM/MECM misconfig (NAA creds, PXE)?
    → [SCCM/MECM Attacks](../../sccm-mecm-attacks/sccm-mecm-attacks.md)

  ACL abuse (GenericAll, WriteDACL, ForceChangePassword)?
    → BloodHound shows these — act on the path it gives you

  Nothing yet?
  └─ try relay attacks (Phase 7)
     hunt creds in shares, scripts, GPP, description fields


========================================================================
 PHASE 7 — RELAY & COERCION ATTACKS
========================================================================

  These don't need domain creds — just network position.
  Run these in parallel with other phases.

  Is SMB signing disabled? (nxc smb <subnet> --gen-relay-list)
  ├─ YES → poison + relay:
  │        [LLMNR Poisoning / Responder](../../relay-attacks/llmnr-poisoning-responder/llmnr-poisoning-responder.md)
  │        [SMB Relay](../../relay-attacks/smb-relay/smb-relay.md)
  │        [NTLM Relay](../../relay-attacks/ntlm-relay/ntlm-relay.md)
  └─ NO  → relay to LDAP / HTTP / ADCS instead

  Can you coerce auth from a DC or high-value server?
    → [Authentication Coercion](../../relay-attacks/authentication-coercion/authentication-coercion.md)
      (PetitPotam, PrinterBug, DFSCoerce)

  Is ADCS web enrollment exposed?
    → coerce + relay to it
    → [ADCS Relay](../../relay-attacks/adcs-relay/adcs-relay.md)

  IPv6 unclaimed on the network?
    → [mitm6](../../relay-attacks/mitm6/mitm6.md) + LDAP relay


========================================================================
 PHASE 8 — DOMAIN DOMINANCE
========================================================================

  You have Domain Admin (or equivalent). Finish the job:

  DCSync — dump every hash in the domain:
    → secretsdump.py with DA creds against the DC
    → this gives you the krbtgt hash

  Forge tickets with krbtgt:
    → [Golden / Silver Tickets](../../kerberos/golden-silver-tickets/golden-silver-tickets.md)

  Set up persistence:
    → [Windows Persistence](../../../03-post-exploitation/persistence-windows/persistence-windows.md)

  Domain is hybrid / cloud-connected?
    → pivot to cloud:
      [Azure Enumeration](../../../07-cloud/azure-enumeration/azure-enumeration.md)
      [Entra ID Attacks](../../../07-cloud/entra-id-attacks/entra-id-attacks.md)


========================================================================
 WHEN TO BYPASS AMSI — QUICK REFERENCE
========================================================================

  NEED bypass (Defender is on + you're running these on target):
    • Mimikatz / Invoke-Mimikatz
    • Rubeus
    • PowerView / SharpView
    • SharpHound (PowerShell collector)
    • Any offensive PS script

  DON'T need bypass:
    • Python tools from your attack box (impacket, nxc, etc.)
    • C# via execute-assembly in C2
    • LOLBins (certutil, rundll32, etc.)
    • Anything running from your Linux box

  → [AV / AMSI Bypass](../../../08-evasion/av-amsi-bypass/av-amsi-bypass.md)
