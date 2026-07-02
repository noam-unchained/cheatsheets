Windows AD Attack Chain - Cheat Sheet

A high-level roadmap for attacking a Windows Active Directory environment.
This is NOT a commands reference — it maps the flow from initial foothold to
domain dominance and tells you WHAT to do next based on WHAT you have.
For actual commands, follow the cross-references to the dedicated cheatsheets.


========================================================================
 PHASE 0 — BEFORE YOU TOUCH ANYTHING
========================================================================

Prep checklist:
  - C2 ready?            → see: sliver cheatsheet
  - File-transfer method? → see: file-transfers cheatsheet
  - Note-taking started?  → log every cred, host, and path as you go


========================================================================
 PHASE 1 — INITIAL ACCESS  (you have: nothing → you want: a foothold)
========================================================================

Pick your entry based on the engagement scope:

  ┌─────────────────────────────────────────────────────────────────┐
  │  On the network (internal pentest)?                            │
  │    YES → go straight to Phase 2 (you ARE the foothold)         │
  │    NO  → you need remote initial access:                       │
  │          • Phishing / AitM   → see: aitm-phishing, evilginx   │
  │          • Web app vuln      → see: web-app cheatsheets        │
  │          • VPN / exposed svc → exploit and get a shell         │
  └─────────────────────────────────────────────────────────────────┘

Once you have a shell or agent callback → move to Phase 2.


========================================================================
 PHASE 2 — SITUATIONAL AWARENESS  (you have: foothold → you want: context)
========================================================================

First thing on any new host — understand where you are:

  1. Am I a local admin?
       whoami /priv  — look for SeDebugPrivilege, SeImpersonatePrivilege
       whoami /groups — member of Administrators / BUILTIN\Administrators?
         YES → you can dump creds (Phase 4), skip local privesc
         NO  → you need local privesc (Phase 3)

  2. Is Defender / EDR running?
       tasklist — look for MsMpEng.exe, Sysmon, CrowdStrike, Carbon Black…
         YES → you likely need AMSI bypass before running any PS tooling
               → see: av-amsi-bypass cheatsheet
         NO  → proceed freely

  3. What domain am I in?
       whoami          → DOMAIN\user
       systeminfo      → Domain field
       nltest /dsgetdc:  → find the DC

  4. What network am I on?
       ipconfig /all, arp -a, netstat -ano
       Can I reach the DC? Other subnets?
         NO  → you may need to pivot → see: pivoting-tunneling cheatsheet

  → see: windows-local cheatsheet for full local enum commands


========================================================================
 PHASE 3 — LOCAL PRIVILEGE ESCALATION  (you have: low-priv shell →
                                         you want: local admin)
========================================================================

  Only needed if Phase 2 showed you are NOT local admin.

  Decision tree:
  ┌─────────────────────────────────────────────────────────────────┐
  │  Do you have SeImpersonatePrivilege? (service accounts often   │
  │  do — IIS, MSSQL, etc.)                                       │
  │    YES → Potato attacks (GodPotato, PrintSpoofer, etc.)        │
  │                                                                │
  │  Any unquoted service paths / weak service permissions?        │
  │    YES → service-based privesc                                 │
  │                                                                │
  │  Stored credentials? (cmdkey /list, Credential Manager)        │
  │    YES → runas /savecred                                      │
  │                                                                │
  │  AlwaysInstallElevated enabled?                                │
  │    YES → MSI-based privesc                                    │
  │                                                                │
  │  Nothing local?                                                │
  │    → try credential abuse from Phase 5 to move to a host      │
  │      where you ARE admin                                       │
  └─────────────────────────────────────────────────────────────────┘

  → see: windows-privesc cheatsheet for commands


========================================================================
 PHASE 4 — CREDENTIAL HARVESTING  (you have: local admin →
                                    you want: domain creds)
========================================================================

  *** AMSI / AV CHECK ***
  Before running Mimikatz, Rubeus, or any PS module:
    Is AMSI / Defender active?
      YES → bypass AMSI first → see: av-amsi-bypass cheatsheet
      NO  → proceed

  Dump everything you can:
  ┌─────────────────────────────────────────────────────────────────┐
  │  LSASS memory                                                  │
  │    → plaintext passwords, NTLM hashes, Kerberos tickets       │
  │    → see: lsass-dumping cheatsheet                             │
  │                                                                │
  │  SAM database (local accounts)                                 │
  │    → secretsdump or reg save + offline extraction              │
  │                                                                │
  │  Credential Manager / DPAPI / browser creds / vaults           │
  │    → see: credential-hunting cheatsheet                        │
  │                                                                │
  │  Cached domain creds (DCC2)                                    │
  │    → crackable offline → see: hashcat, john cheatsheets        │
  └─────────────────────────────────────────────────────────────────┘

  What did you get?
    • NTLM hash       → Phase 5a (pass-the-hash)
    • Kerberos TGT    → Phase 5b (pass-the-ticket)
    • Cleartext pass  → Phase 5c (direct auth, password spraying)
    • Nothing useful  → go to Phase 6 (AD enum) and find another path


========================================================================
 PHASE 5 — LATERAL MOVEMENT  (you have: creds → you want: more hosts)
========================================================================

  Pick your method based on what cred type you hold:

  5a. NTLM hash (no cleartext):
      → pass-the-hash with nxc, wmiexec, psexec
      → see: pass-the-hash cheatsheet

  5b. Kerberos ticket (TGT/TGS):
      → pass-the-ticket, overpass-the-hash
      → see: pass-the-ticket cheatsheet

  5c. Cleartext password:
      → nxc smb/winrm/rdp, runas, Enter-PSSession
      → password spraying across the domain
      → see: password-spraying cheatsheet

  Target selection — where to move:
  ┌─────────────────────────────────────────────────────────────────┐
  │  Which hosts should you hit next?                              │
  │    • Hosts where your creds have local admin (nxc --shares)    │
  │    • High-value targets: DC, file servers, SCCM, ADCS, DB     │
  │    • Hosts with logged-in privileged users (BloodHound)        │
  │                                                                │
  │  Need to reach a different subnet?                             │
  │    → set up a pivot → see: pivoting-tunneling cheatsheet       │
  └─────────────────────────────────────────────────────────────────┘

  Every new host you land on → repeat Phase 2 + Phase 4 (enum + dump).
  This is the loop: land → dump → move → land → dump → move.


========================================================================
 PHASE 6 — AD ENUMERATION  (you have: domain user →
                              you want: escalation paths)
========================================================================

  *** AMSI / AV CHECK ***
  SharpHound and PowerView will get caught by AMSI if it's active.
    → bypass AMSI first if needed → see: av-amsi-bypass cheatsheet

  Run BloodHound collection:
    → see: bloodhound cheatsheet

  Also enumerate:
    • LDAP queries (users, groups, GPOs, ACLs, trusts)
      → see: ldap-enumeration, windows-ad cheatsheets
    • Kerberos: SPNs (Kerberoastable), no-preauth (AS-REP Roastable)
    • ADCS: misconfigured certificate templates (ESC1-ESC8)
    • SCCM/MECM: NAA creds, PXE abuse
    • GPO permissions: who can modify which GPO?

  What escalation paths did you find?
  ┌─────────────────────────────────────────────────────────────────┐
  │  Kerberoastable SPN on a high-priv account?                    │
  │    → Kerberoast it → see: kerberoasting cheatsheet             │
  │                                                                │
  │  AS-REP Roastable account?                                     │
  │    → AS-REP Roast → see: asrep-roasting cheatsheet             │
  │                                                                │
  │  ADCS misconfiguration (ESC1-ESC8)?                            │
  │    → abuse the template → see: adcs-esc-attacks cheatsheet     │
  │                                                                │
  │  Delegation abuse (unconstrained/constrained/RBCD)?            │
  │    → see: delegation-abuse cheatsheet                          │
  │                                                                │
  │  Writable GPO linked to high-priv OUs?                         │
  │    → see: gpo-abuse cheatsheet                                 │
  │                                                                │
  │  Shadow Credentials (write to msDS-KeyCredentialLink)?         │
  │    → see: shadow-credentials cheatsheet                        │
  │                                                                │
  │  SCCM/MECM misconfigurations?                                  │
  │    → see: sccm-mecm-attacks cheatsheet                         │
  │                                                                │
  │  ACL abuse paths (GenericAll, WriteDACL, ForceChangePassword)? │
  │    → BloodHound will show these → act accordingly              │
  │                                                                │
  │  Nothing yet?                                                   │
  │    → password spray with known patterns                        │
  │    → relay attacks (see Phase 7)                               │
  │    → hunt for creds in shares / scripts / GPP                  │
  └─────────────────────────────────────────────────────────────────┘


========================================================================
 PHASE 7 — RELAY & COERCION ATTACKS  (you have: network position →
                                       you want: auth to relay)
========================================================================

  These attacks don't require domain creds — just network position.
  Good when you're stuck or want a parallel attack path.

  ┌─────────────────────────────────────────────────────────────────┐
  │  Is SMB signing disabled on targets? (nxc smb --gen-relay-list)│
  │    YES → LLMNR/NBT-NS poisoning + SMB relay                   │
  │          → see: llmnr-poisoning-responder cheatsheet           │
  │          → see: smb-relay, ntlm-relay cheatsheets              │
  │    NO  → relay to other services (LDAP, HTTP, ADCS)            │
  │                                                                │
  │  Can you coerce authentication from a DC / high-value server?  │
  │    → PetitPotam, PrinterBug, DFSCoerce                        │
  │    → see: authentication-coercion cheatsheet                   │
  │                                                                │
  │  Is ADCS web enrollment exposed?                               │
  │    → coerce + relay to ADCS (ESC8)                             │
  │    → see: adcs-relay cheatsheet                                │
  │                                                                │
  │  IPv6 unclaimed in the network?                                │
  │    → mitm6 + LDAP relay                                       │
  │    → see: mitm6 cheatsheet                                     │
  └─────────────────────────────────────────────────────────────────┘


========================================================================
 PHASE 8 — DOMAIN DOMINANCE  (you have: DA or equivalent →
                               you want: full domain control)
========================================================================

  You've reached Domain Admin (or equivalent). Now secure your access:

  ┌─────────────────────────────────────────────────────────────────┐
  │  Dump the domain — DCSync:                                     │
  │    → secretsdump.py with DA creds against the DC               │
  │    → gives you EVERY hash including krbtgt                     │
  │                                                                │
  │  Golden Ticket (krbtgt hash):                                  │
  │    → forge TGTs for any user, survives password resets          │
  │    → see: golden-silver-tickets cheatsheet                     │
  │                                                                │
  │  Silver Ticket (service account hash):                         │
  │    → forge TGS for specific services, stealthier               │
  │    → see: golden-silver-tickets cheatsheet                     │
  │                                                                │
  │  Persistence options:                                          │
  │    → see: persistence-windows cheatsheet                       │
  │                                                                │
  │  Forest trusts to abuse?                                       │
  │    → SID History, cross-forest Kerberoast, trust keys          │
  │                                                                │
  │  Cloud connected (Azure AD / Entra ID)?                        │
  │    → pivot to cloud → see: azure-enumeration,                  │
  │                             entra-id-attacks cheatsheets       │
  └─────────────────────────────────────────────────────────────────┘


========================================================================
 WHEN TO BYPASS AMSI — QUICK REFERENCE
========================================================================

  Bypass AMSI when you need to run ANY of these on a host with Defender:
    • Mimikatz / Invoke-Mimikatz
    • Rubeus
    • PowerView / SharpView
    • SharpHound (PowerShell collector)
    • Any custom PS script that touches security-sensitive APIs

  You do NOT need AMSI bypass for:
    • Python tools from your attack box (impacket, nxc, etc.)
    • Compiled C# loaded via execute-assembly in C2
    • Living-off-the-land binaries (LOLBins)
    • Tools running from Linux

  → see: av-amsi-bypass cheatsheet for bypass techniques


========================================================================
 THE LOOP — HOW THE CHAIN ACTUALLY FLOWS
========================================================================

  Most AD engagements follow this loop:

    ┌──────────────┐
    │ Land on host  │
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │ Situational   │◄──────────────────────────────┐
    │ awareness     │                               │
    └──────┬───────┘                               │
           ▼                                        │
    ┌──────────────┐     ┌────────────────┐         │
    │ Need local    │YES  │ Privesc        │         │
    │ admin?  ──────┼────►│ (Phase 3)      │         │
    │               │     └───────┬────────┘         │
    │       NO      │             │                   │
    └──────┬───────┘             │                   │
           ▼                     ▼                   │
    ┌──────────────┐                                 │
    │ Dump creds    │                                 │
    │ (Phase 4)     │                                 │
    └──────┬───────┘                                 │
           ▼                                         │
    ┌──────────────┐     ┌────────────────┐         │
    │ Got creds to  │YES  │ Move to next   │─────────┘
    │ move? ────────┼────►│ host (Phase 5) │  (repeat)
    │               │     └────────────────┘
    │       NO      │
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │ AD enum       │
    │ (Phase 6)     │
    │ Relay attacks │
    │ (Phase 7)     │
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │ Domain Admin? │
    │   YES → Phase 8 (dominance)                    │
    │   NO  → find more paths, keep looping          │
    └──────────────┘
