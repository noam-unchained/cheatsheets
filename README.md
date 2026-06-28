# cheatsheets

Personal security / lab cheat sheets, organized by attack phase.

## Enumeration
- [nmap](enumeration/nmap/) — nmap scanning workflow: host discovery, scan types, version/OS detection, NSE scripts, output
- [linux-enumeration](enumeration/linux-enum/) — Linux local enumeration workflow
- [windows-local](enumeration/windows-local/) — Windows local enumeration workflow

## Active Directory

### Enumeration
- [windows-ad](active-directory/enumeration/windows-ad/) — unauthenticated + authenticated AD enumeration, impacket tools, BloodHound collection
- [bloodhound](active-directory/enumeration/bloodhound/) — BloodHound CE setup, data collection, pathfinding, DCSync, Cypher queries

### Credential Attacks
- [pass-the-hash](active-directory/credential-abuse/pass-the-hash/) — authenticate with a captured NT hash directly — SMB, WinRM, network spray

### Relay Attacks
- [llmnr-poisoning-responder](active-directory/relay-attacks/llmnr-poisoning-responder/) — LLMNR/NBT-NS poisoning with Responder to capture NTLMv2 hashes
- [ntlm-relay](active-directory/relay-attacks/ntlm-relay/) — relay captured NTLM auth in real time — Responder + ntlmrelayx + SOCKS post-exploitation
- [smb-relay](active-directory/relay-attacks/smb-relay/) — SMB relay attack
- [mitm6](active-directory/relay-attacks/mitm6/) — IPv6-based MITM — exploit default-enabled IPv6 + WPAD to relay NTLM auth to LDAP

### Kerberos
- [kerberoasting](active-directory/kerberos/kerberoasting/) — request TGS tickets for SPN accounts and crack them offline (hashcat + John)
- [asrep-roasting](active-directory/kerberos/asrep-roasting/) — capture AS-REP hashes for accounts with pre-auth disabled and crack them offline

## Network
- [ettercap-mitm](network/ettercap-mitm/) — Ettercap ARP-poisoning MITM

## Privilege Escalation
- [linux-privesc](privilege-escalation/linux-privesc/) — Linux local privilege escalation
- [windows-privesc](privilege-escalation/windows-privesc/) — local Windows privesc (SeImpersonatePrivilege/Potato, service exploits, AlwaysInstallElevated, stored creds) + AD escalation (ACL abuse, DCSync)
