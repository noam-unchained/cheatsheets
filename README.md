# cheatsheets

Personal security / lab cheat sheets, organized by attack phase.

## Enumeration
- [nmap](enumeration/nmap/) — nmap scanning workflow: host discovery, scan types, version/OS detection, NSE scripts, output (diagram + step-by-step)
- [linux-enumeration](enumeration/linux-enumeration/) — Linux local enumeration workflow
- [windows-ad](enumeration/windows-ad/) — full Windows / Active Directory enumeration workflow, organized by goal — unauthenticated recon through authenticated domain mapping
- [windows-local](enumeration/windows-local/) — Windows local enumeration workflow

## Attacks

### Credential Attacks
- [llmnr-poisoning-responder](attacks/credential-attacks/llmnr-poisoning-responder/) — LLMNR/NBT-NS poisoning with Responder to capture NTLMv2 hashes (diagram + step-by-step)
- [ntlm-relay](attacks/credential-attacks/ntlm-relay/) — relay captured NTLM auth in real time to a target without cracking — Responder + ntlmrelayx + SOCKS post-exploitation (secretsdump, lsassy, smbexec, token impersonation)
- [pass-the-hash](attacks/credential-attacks/pass-the-hash/) — authenticate with a captured NT hash directly, no plaintext needed — SMB, WinRM, and network spray (diagram + step-by-step)
- [smb-relay](attacks/credential-attacks/smb-relay/) — SMB relay attack

### MITM
- [ettercap-mitm](attacks/mitm/ettercap-mitm/) — Ettercap ARP-poisoning MITM (diagram + step-by-step)
- [mitm6](attacks/mitm/mitm6/) — IPv6-based MITM attack — exploit default-enabled IPv6 + WPAD to relay NTLM auth to LDAP and dump the entire domain (users, groups, computers, policies)

### Kerberos
- [kerberoasting](attacks/kerberos/kerberoasting/) — request service tickets for SPNs and crack them offline to recover service account passwords
- [asrep-roasting](attacks/kerberos/asrep-roasting/) — capture AS-REP hashes for accounts with pre-auth disabled and crack them offline

## Privilege Escalation
- [linux-privesc](privilege-escalation/linux-privesc/) — Linux local privilege escalation
- [windows-privesc](privilege-escalation/windows-privesc/) — local Windows privilege escalation (SeImpersonatePrivilege/Potato, service exploits, AlwaysInstallElevated, stored credentials) + AD escalation (ACL abuse, DCSync)
