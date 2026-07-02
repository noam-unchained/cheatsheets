# cheatsheets

Offensive security cheat sheets, organized by pentest phase.
Each topic has a **PDF** (one-page diagram + step-by-step commands) and a **Markdown** source.

---

## 00 — General
- [file-transfers](00-general/file-transfers/) — get tools on target + loot off it: certutil, PowerShell, wget/curl, SMB, scp, nc, /dev/tcp, base64
- [hashcat](00-general/password-cracking/hashcat/) — offline hash cracking: mode selection, wordlist + rules, masks, hybrid, run control
- [john](00-general/password-cracking/john/) — John the Ripper: *2john file extractors (zip/PDF/SSH/KeePass/shadow), auto-detect, rules/incremental/mask

## 01 — Recon & Enumeration
- [nmap](01-recon-enumeration/nmap/) — host discovery, scan types, version/OS detection, NSE scripts, output
- [web-enumeration](01-recon-enumeration/web-enumeration/) — dirs/vhosts/subdomains/params (feroxbuster, ffuf, gobuster, subfinder)
- [smb-enumeration](01-recon-enumeration/smb-enumeration/) — SMB recon with nxc: shares, users (RID brute), pass policy, signing, GPP/loot
- [linux-enumeration](01-recon-enumeration/linux-enum/) — Linux local enumeration workflow
- [windows-local](01-recon-enumeration/windows-local/) — Windows local enumeration workflow

## 02 — Initial Access

### Phishing
- [aitm-phishing](02-initial-access/aitm-phishing/) — Adversary-in-the-Middle reverse-proxy phishing to steal MFA-backed session tokens
- [evilginx](02-initial-access/evilginx/) — Evilginx 2: phishlets, lures, session capture, cookie replay

### Web Application
- [sqli](02-initial-access/web-app/sqli/) — SQL injection: auth bypass, UNION + blind extraction, sqlmap
- [xss](02-initial-access/web-app/xss/) — Cross-Site Scripting: reflected/stored/DOM, context payloads, WAF bypasses, session theft
- [command-injection](02-initial-access/web-app/command-injection/) — OS shell command injection → RCE + reverse shell (in-band, blind, filter bypasses)
- [lfi-rfi](02-initial-access/web-app/lfi-rfi/) — file inclusion: path traversal, PHP wrappers, log/session poisoning → RCE
- [file-upload-bypass](02-initial-access/web-app/file-upload-bypass/) — defeat extension/content-type/magic-byte filters to plant a webshell
- [ssrf](02-initial-access/web-app/ssrf/) — Server-Side Request Forgery: internal reach, cloud metadata (IMDS), gopher/file schemes, filter bypasses
- [burp-suite](02-initial-access/web-app/burp-suite/) — Burp Suite, split per tool:
  - [burp-overview](02-initial-access/web-app/burp-suite/burp-overview/) — proxy / CA / scope setup and the Send-to-tool workflow
  - [burp-repeater](02-initial-access/web-app/burp-suite/burp-repeater/) — manual request tampering (auth bypass, IDOR, injection probes)
  - [burp-intruder](02-initial-access/web-app/burp-suite/burp-intruder/) — automated fuzzing + the 4 attack types
  - [burp-extensions](02-initial-access/web-app/burp-suite/burp-extensions/) — key BApp Store extensions (Autorize, Param Miner, JWT Editor, Logger++, Turbo Intruder)

## 03 — Post-Exploitation
- [windows-privesc](03-post-exploitation/windows-privesc/) — local Windows privesc (SeImpersonate/Potato, service exploits, AlwaysInstallElevated, stored creds) + AD escalation (ACL abuse, DCSync)
- [linux-privesc](03-post-exploitation/linux-privesc/) — Linux local privilege escalation
- [credential-hunting](03-post-exploitation/credential-hunting/) — mine stored creds (Windows DPAPI/browser/Cred Manager, Linux history/keys/configs) → reuse to escalate + pivot
- [persistence-windows](03-post-exploitation/persistence-windows/) — survive reboots: registry run keys, scheduled tasks, services, WMI subscriptions, DLL hijacking
- [persistence-linux](03-post-exploitation/persistence-linux/) — survive reboots: cron, systemd, SSH keys, SUID backdoor, shell profiles, rc.local

## 04 — Active Directory

### Enumeration
- [windows-ad](04-active-directory/enumeration/windows-ad/) — unauthenticated + authenticated AD enumeration, impacket, BloodHound collection
- [ldap-enumeration](04-active-directory/enumeration/ldap-enumeration/) — query AD over LDAP (nxc/ldapsearch/windapsearch): SPNs, AS-REP, delegation, description-field passwords
- [bloodhound](04-active-directory/enumeration/bloodhound/) — BloodHound CE setup, data collection, pathfinding, DCSync, Cypher queries

### Credential Attacks
- [pass-the-hash](04-active-directory/credential-abuse/pass-the-hash/) — authenticate with a captured NT hash — SMB, WinRM, network spray
- [lsass-dumping](04-active-directory/credential-abuse/lsass-dumping/) — dump LSASS / local secrets (nxc, secretsdump, comsvcs, mimikatz, pypykatz)
- [shadow-credentials](04-active-directory/credential-abuse/shadow-credentials/) — abuse msDS-KeyCredentialLink via certipy/pywhisker → PKINIT → NT hash
- [password-spraying](04-active-directory/credential-abuse/password-spraying/) — one password vs many users, on-prem (nxc/kerbrute) + cloud (M365/Entra)
- [pass-the-ticket](04-active-directory/credential-abuse/pass-the-ticket/) — overpass-the-hash + pass-the-ticket (Rubeus/impacket)

### Relay & MITM Attacks
- [llmnr-poisoning-responder](04-active-directory/relay-attacks/llmnr-poisoning-responder/) — LLMNR/NBT-NS poisoning with Responder to capture NTLMv2 hashes
- [ntlm-relay](04-active-directory/relay-attacks/ntlm-relay/) — relay NTLM auth in real time — Responder + ntlmrelayx + SOCKS
- [smb-relay](04-active-directory/relay-attacks/smb-relay/) — SMB relay attack
- [mitm6](04-active-directory/relay-attacks/mitm6/) — IPv6-based MITM — exploit default-enabled IPv6 + WPAD to relay NTLM to LDAP
- [ettercap-mitm](04-active-directory/relay-attacks/ettercap-mitm/) — Ettercap ARP-poisoning MITM
- [authentication-coercion](04-active-directory/relay-attacks/authentication-coercion/) — force machine auth (PetitPotam/PrinterBug/DFSCoerce/Coercer) — trigger for relay + ADCS ESC8
- [adcs-relay](04-active-directory/relay-attacks/adcs-relay/) — ESC8: coerce a DC → relay to AD CS HTTP enrollment → cert → PKINIT → DCSync

### Kerberos
- [kerberoasting](04-active-directory/kerberos/kerberoasting/) — request TGS tickets for SPN accounts and crack offline (hashcat + John)
- [asrep-roasting](04-active-directory/kerberos/asrep-roasting/) — capture AS-REP hashes for accounts with pre-auth disabled and crack offline
- [delegation-abuse](04-active-directory/kerberos/delegation-abuse/) — unconstrained / constrained (S4U) / RBCD delegation abuse → Domain Admin
- [adcs-esc-attacks](04-active-directory/kerberos/adcs-esc-attacks/) — AD CS ESC1–ESC8 with certipy → certificate → PKINIT
- [golden-silver-tickets](04-active-directory/kerberos/golden-silver-tickets/) — forge TGTs (golden) and TGSs (silver) — persistence/impersonation

### GPO Abuse
- [gpo-abuse](04-active-directory/gpo-abuse/) — abuse writable GPOs (SharpGPOAbuse/pyGPOAbuse) to push scheduled tasks domain-wide + GPP password extraction

### Site Systems
- [sccm-mecm-attacks](04-active-directory/sccm-mecm-attacks/) — SCCM/MECM: recover NAA creds + relay the site server (SCCMHunter) → SYSTEM on every client

### Attack Chains
- [ad-attack-chain (v1)](04-active-directory/ad-attack-chain/v1-descriptive/) — high-level AD attack flowchart with phase descriptions
- [ad-attack-chain (v2)](04-active-directory/ad-attack-chain/v2-decision-tree/) — decision-tree walkthrough with clickable links to each cheatsheet

## 05 — Wireless
- [wifi-wpa-cracking](05-wireless/wifi-wpa-cracking/) — capture WPA/WPA2 handshake or PMKID with an ALFA adapter → crack offline (aircrack / hashcat -m 22000)
- [bluetooth-hacking](05-wireless/bluetooth-hacking/) — Classic + BLE recon, GATT enum, Ubertooth sniffing, BLE MITM, crackle, Bluesnarfing

## 06 — Network
- [pivoting-tunneling](06-network/pivoting-tunneling/) — pivot through a foothold into internal subnets (ligolo-ng / chisel / SSH / proxychains)

## 07 — Cloud
- [azure-enumeration](07-cloud/azure-enumeration/) — directory + resource enumeration (ROADrecon, AzureHound, az CLI, IMDS)
- [entra-id-attacks](07-cloud/entra-id-attacks/) — Entra ID / Azure AD: tenant recon, token theft (device code, consent, PRT), hybrid pivot

## 08 — Evasion
- [av-amsi-bypass](08-evasion/av-amsi-bypass/) — bypass AMSI (reflection/memory patch) + evade Defender on disk (in-memory cradles, ScareCrow, custom loaders, DLL side-loading)

## 09 — C2 Frameworks
- [sliver](09-c2-frameworks/sliver/) — Sliver C2: implant generation (session/beacon), listeners, execute-assembly, SOCKS5 pivoting, armory extensions
