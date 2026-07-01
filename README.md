# cheatsheets

Offensive security cheat sheets, organized by pentest phase.
Each topic has a **PDF** (one-page diagram + step-by-step commands) and a **Markdown** source.

---

## 02 — Scanning & Enumeration
- [nmap](02-enumeration/nmap/) — host discovery, scan types, version/OS detection, NSE scripts, output
- [web-enumeration](02-enumeration/web-enumeration/) — dirs/vhosts/subdomains/params (feroxbuster, ffuf, gobuster, subfinder)
- [smb-enumeration](02-enumeration/smb-enumeration/) — SMB recon with nxc: shares, users (RID brute), pass policy, signing, GPP/loot
- [linux-enumeration](02-enumeration/linux-enum/) — Linux local enumeration workflow
- [windows-local](02-enumeration/windows-local/) — Windows local enumeration workflow

## 03 — Exploitation

### Initial Access
- [aitm-phishing](03-initial-access/aitm-phishing/) — Adversary-in-the-Middle reverse-proxy phishing to steal MFA-backed session tokens
- [evilginx](03-initial-access/evilginx/) — Evilginx 2: phishlets, lures, session capture, cookie replay

### Web Application
- [sqli](03-web-app/sqli/) — SQL injection: auth bypass, UNION + blind extraction, sqlmap
- [xss](03-web-app/xss/) — Cross-Site Scripting: reflected/stored/DOM, context payloads, WAF bypasses, session theft
- [command-injection](03-web-app/command-injection/) — OS shell command injection → RCE + reverse shell (in-band, blind, filter bypasses)
- [lfi-rfi](03-web-app/lfi-rfi/) — file inclusion: path traversal, PHP wrappers, log/session poisoning → RCE
- [file-upload-bypass](03-web-app/file-upload-bypass/) — defeat extension/content-type/magic-byte filters to plant a webshell
- [ssrf](03-web-app/ssrf/) — Server-Side Request Forgery: internal reach, cloud metadata (IMDS), gopher/file schemes, filter bypasses
- [burp-suite](03-web-app/burp-suite/) — Burp Suite, split per tool:
  - [burp-overview](03-web-app/burp-suite/burp-overview/) — proxy / CA / scope setup and the Send-to-tool workflow
  - [burp-repeater](03-web-app/burp-suite/burp-repeater/) — manual request tampering (auth bypass, IDOR, injection probes)
  - [burp-intruder](03-web-app/burp-suite/burp-intruder/) — automated fuzzing + the 4 attack types
  - [burp-extensions](03-web-app/burp-suite/burp-extensions/) — key BApp Store extensions (Autorize, Param Miner, JWT Editor, Logger++, Turbo Intruder)

### Active Directory

#### Enumeration
- [windows-ad](03-active-directory/enumeration/windows-ad/) — unauthenticated + authenticated AD enumeration, impacket, BloodHound collection
- [ldap-enumeration](03-active-directory/enumeration/ldap-enumeration/) — query AD over LDAP (nxc/ldapsearch/windapsearch): SPNs, AS-REP, delegation, description-field passwords
- [bloodhound](03-active-directory/enumeration/bloodhound/) — BloodHound CE setup, data collection, pathfinding, DCSync, Cypher queries

#### Credential Attacks
- [pass-the-hash](03-active-directory/credential-abuse/pass-the-hash/) — authenticate with a captured NT hash — SMB, WinRM, network spray
- [lsass-dumping](03-active-directory/credential-abuse/lsass-dumping/) — dump LSASS / local secrets (nxc, secretsdump, comsvcs, mimikatz, pypykatz)
- [shadow-credentials](03-active-directory/credential-abuse/shadow-credentials/) — abuse msDS-KeyCredentialLink via certipy/pywhisker → PKINIT → NT hash
- [password-spraying](03-active-directory/credential-abuse/password-spraying/) — one password vs many users, on-prem (nxc/kerbrute) + cloud (M365/Entra)
- [pass-the-ticket](03-active-directory/credential-abuse/pass-the-ticket/) — overpass-the-hash + pass-the-ticket (Rubeus/impacket)

#### Relay Attacks
- [llmnr-poisoning-responder](03-active-directory/relay-attacks/llmnr-poisoning-responder/) — LLMNR/NBT-NS poisoning with Responder to capture NTLMv2 hashes
- [ntlm-relay](03-active-directory/relay-attacks/ntlm-relay/) — relay NTLM auth in real time — Responder + ntlmrelayx + SOCKS
- [smb-relay](03-active-directory/relay-attacks/smb-relay/) — SMB relay attack
- [mitm6](03-active-directory/relay-attacks/mitm6/) — IPv6-based MITM — exploit default-enabled IPv6 + WPAD to relay NTLM to LDAP
- [authentication-coercion](03-active-directory/relay-attacks/authentication-coercion/) — force machine auth (PetitPotam/PrinterBug/DFSCoerce/Coercer) — trigger for relay + ADCS ESC8
- [adcs-relay](03-active-directory/relay-attacks/adcs-relay/) — ESC8: coerce a DC → relay to AD CS HTTP enrollment → cert → PKINIT → DCSync

#### Kerberos
- [kerberoasting](03-active-directory/kerberos/kerberoasting/) — request TGS tickets for SPN accounts and crack offline (hashcat + John)
- [asrep-roasting](03-active-directory/kerberos/asrep-roasting/) — capture AS-REP hashes for accounts with pre-auth disabled and crack offline
- [delegation-abuse](03-active-directory/kerberos/delegation-abuse/) — unconstrained / constrained (S4U) / RBCD delegation abuse → Domain Admin
- [adcs-esc-attacks](03-active-directory/kerberos/adcs-esc-attacks/) — AD CS ESC1–ESC8 with certipy → certificate → PKINIT
- [golden-silver-tickets](03-active-directory/kerberos/golden-silver-tickets/) — forge TGTs (golden) and TGSs (silver) — persistence/impersonation

#### GPO Abuse
- [gpo-abuse](03-active-directory/gpo-abuse/) — abuse writable GPOs (SharpGPOAbuse/pyGPOAbuse) to push scheduled tasks domain-wide + GPP password extraction

#### Site Systems
- [sccm-mecm-attacks](03-active-directory/sccm-mecm-attacks/) — SCCM/MECM: recover NAA creds + relay the site server (SCCMHunter) → SYSTEM on every client

### Cloud
- [entra-id-attacks](03-cloud/entra-id-attacks/) — Entra ID / Azure AD: tenant recon, token theft (device code, consent, PRT), hybrid pivot
- [azure-enumeration](03-cloud/azure-enumeration/) — directory + resource enumeration (ROADrecon, AzureHound, az CLI, IMDS)

### Network
- [ettercap-mitm](03-network/ettercap-mitm/) — Ettercap ARP-poisoning MITM
- [pivoting-tunneling](03-network/pivoting-tunneling/) — pivot through a foothold into internal subnets (ligolo-ng / chisel / SSH / proxychains)

### Wireless
- [wifi-wpa-cracking](03-wireless/wifi-wpa-cracking/) — capture WPA/WPA2 handshake or PMKID with an ALFA adapter → crack offline (aircrack / hashcat -m 22000)

### Evasion
- [av-amsi-bypass](03-av-amsi-bypass/) — bypass AMSI (reflection/memory patch) + evade Defender on disk (in-memory cradles, ScareCrow, custom loaders, DLL side-loading)

### C2 Frameworks
- [sliver](03-c2-frameworks/sliver/) — Sliver C2: implant generation (session/beacon), listeners, execute-assembly, SOCKS5 pivoting, armory extensions

## 04 — Post-Exploitation
- [privilege-escalation / linux](04-privilege-escalation/linux-privesc/) — Linux local privilege escalation
- [privilege-escalation / windows](04-privilege-escalation/windows-privesc/) — local Windows privesc (SeImpersonate/Potato, service exploits, AlwaysInstallElevated, stored creds) + AD escalation (ACL abuse, DCSync)
- [credential-hunting](04-post-exploitation/credential-hunting/) — mine stored creds (Windows DPAPI/browser/Cred Manager, Linux history/keys/configs) → reuse to escalate + pivot
- [persistence-windows](04-post-exploitation/persistence-windows/) — survive reboots: registry run keys, scheduled tasks, services, WMI subscriptions, DLL hijacking
- [persistence-linux](04-post-exploitation/persistence-linux/) — survive reboots: cron, systemd, SSH keys, SUID backdoor, shell profiles, rc.local

## 00 — Cross-Cutting
- [hashcat](00-password-cracking/hashcat/) — offline hash cracking: mode selection, wordlist + rules, masks, hybrid, run control
- [john](00-password-cracking/john/) — John the Ripper: *2john file extractors (zip/PDF/SSH/KeePass/shadow), auto-detect, rules/incremental/mask
- [file-transfers](00-file-transfers/) — get tools on target + loot off it: certutil, PowerShell, wget/curl, SMB, scp, nc, /dev/tcp, base64
