# cheatsheets

Personal security / lab cheat sheets, organized by attack phase.

## Initial Access
- [aitm-phishing](initial-access/aitm-phishing/) — Adversary-in-the-Middle reverse-proxy phishing to steal MFA-backed session tokens (concept + workflow)
- [evilginx](initial-access/evilginx/) — Evilginx 2: standalone AiTM framework — phishlets, lures, session capture, cookie replay

## Enumeration
- [nmap](enumeration/nmap/) — nmap scanning workflow: host discovery, scan types, version/OS detection, NSE scripts, output
- [linux-enumeration](enumeration/linux-enum/) — Linux local enumeration workflow
- [windows-local](enumeration/windows-local/) — Windows local enumeration workflow

## Web Application
- [sqli](web-app/sqli/) — SQL injection: auth bypass, UNION + blind extraction, and sqlmap automation
- [burp-suite](web-app/burp-suite/) — Burp Suite, split per tool:
  - [burp-overview](web-app/burp-suite/burp-overview/) — proxy / CA / scope setup and the Send-to-tool workflow
  - [burp-repeater](web-app/burp-suite/burp-repeater/) — manual request tampering (auth bypass, IDOR, injection probes)
  - [burp-intruder](web-app/burp-suite/burp-intruder/) — automated fuzzing + the 4 attack types
  - [burp-extensions](web-app/burp-suite/burp-extensions/) — key BApp Store extensions (Autorize, Param Miner, JWT Editor, Logger++, Turbo Intruder)

## Active Directory

### Enumeration
- [windows-ad](active-directory/enumeration/windows-ad/) — unauthenticated + authenticated AD enumeration, impacket tools, BloodHound collection
- [bloodhound](active-directory/enumeration/bloodhound/) — BloodHound CE setup, data collection, pathfinding, DCSync, Cypher queries

### Credential Attacks
- [pass-the-hash](active-directory/credential-abuse/pass-the-hash/) — authenticate with a captured NT hash directly — SMB, WinRM, network spray
- [lsass-dumping](active-directory/credential-abuse/lsass-dumping/) — dump LSASS / local secret stores (nxc, secretsdump, comsvcs, mimikatz, pypykatz)
- [shadow-credentials](active-directory/credential-abuse/shadow-credentials/) — abuse msDS-KeyCredentialLink via certipy/pywhisker → PKINIT → NT hash
- [password-spraying](active-directory/credential-abuse/password-spraying/) — one password vs many users, on-prem (nxc/kerbrute) + cloud (M365/Entra)
- [pass-the-ticket](active-directory/credential-abuse/pass-the-ticket/) — overpass-the-hash (hash → TGT) + pass-the-ticket (reuse stolen tickets), Rubeus/impacket

### Relay Attacks
- [llmnr-poisoning-responder](active-directory/relay-attacks/llmnr-poisoning-responder/) — LLMNR/NBT-NS poisoning with Responder to capture NTLMv2 hashes
- [ntlm-relay](active-directory/relay-attacks/ntlm-relay/) — relay captured NTLM auth in real time — Responder + ntlmrelayx + SOCKS post-exploitation
- [smb-relay](active-directory/relay-attacks/smb-relay/) — SMB relay attack
- [mitm6](active-directory/relay-attacks/mitm6/) — IPv6-based MITM — exploit default-enabled IPv6 + WPAD to relay NTLM auth to LDAP
- [authentication-coercion](active-directory/relay-attacks/authentication-coercion/) — force machine auth (PetitPotam/PrinterBug/DFSCoerce/Coercer) — the trigger for relay + ADCS ESC8
- [adcs-relay](active-directory/relay-attacks/adcs-relay/) — ESC8: coerce a DC, relay its auth to AD CS HTTP enrollment → cert for DC$ → PKINIT → DCSync

### Kerberos
- [kerberoasting](active-directory/kerberos/kerberoasting/) — request TGS tickets for SPN accounts and crack them offline (hashcat + John)
- [asrep-roasting](active-directory/kerberos/asrep-roasting/) — capture AS-REP hashes for accounts with pre-auth disabled and crack them offline
- [delegation-abuse](active-directory/kerberos/delegation-abuse/) — unconstrained / constrained (S4U) / RBCD delegation abuse → impersonate to Domain Admin
- [adcs-esc-attacks](active-directory/kerberos/adcs-esc-attacks/) — AD CS ESC1–ESC8 with certipy → certificate for a privileged user → PKINIT
- [golden-silver-tickets](active-directory/kerberos/golden-silver-tickets/) — forge TGTs (golden, krbtgt hash) and TGSs (silver, service hash) — persistence/impersonation

### Site Systems
- [sccm-mecm-attacks](active-directory/sccm-mecm-attacks/) — SCCM/MECM: recover NAA creds + relay the site server (SCCMHunter) → SYSTEM on every client

## Cloud
- [entra-id-attacks](cloud/entra-id-attacks/) — Entra ID / Azure AD: tenant recon, token theft (device code, consent, PRT), enumeration, hybrid pivot
- [azure-enumeration](cloud/azure-enumeration/) — deep-dive directory + resource enumeration (ROADrecon, AzureHound, az CLI, IMDS managed identities)

## Network
- [ettercap-mitm](network/ettercap-mitm/) — Ettercap ARP-poisoning MITM
- [pivoting-tunneling](network/pivoting-tunneling/) — pivot through a foothold into internal subnets (ligolo-ng / chisel / SSH / proxychains)

## Privilege Escalation
- [linux-privesc](privilege-escalation/linux-privesc/) — Linux local privilege escalation
- [windows-privesc](privilege-escalation/windows-privesc/) — local Windows privesc (SeImpersonatePrivilege/Potato, service exploits, AlwaysInstallElevated, stored creds) + AD escalation (ACL abuse, DCSync)
