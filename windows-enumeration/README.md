# Windows Enumeration

Full Windows / Active Directory enumeration cheat sheet, organized by goal.
Covers the complete workflow from zero knowledge to full domain mapping.

## Files

- `windows-enumeration.md` — full cheat sheet (plain text, readable in any editor)
- `windows-enumeration.pdf` — styled PDF with orange theme (English)
- `windows-enumeration-he.pdf` — same content in Hebrew
- `quickref.txt` — one-liner command card, all sections at a glance

## Structure

### Part 1 — Unauthenticated
- **Host & Service Discovery** — nmap ping sweep, top-port scan, full service scan, OS fingerprinting
- **DC Discovery** — nslookup SRV record, DNS zone transfer
- **SMB Fingerprinting** — NetExec banner grab (domain, signing status, OS, guest access)
- **Null Session / General Enumeration** — enum4linux-ng, rpcclient
- **User Enumeration** — Kerbrute (silent), nmap krb5 script, rpcclient
- **Share Enumeration** — anonymous and guest access, smbclient

### Part 2 — Authenticated
- **Credential Verification & Spraying** — nxc SMB spray, Kerbrute Kerberos spray (event 4771 vs 4625)
- **Password Policy** — lockout threshold, observation window, duration
- **User Enumeration** — NetExec, RID brute, Impacket GetADUsers, ldapdomaindump
- **Group Enumeration** — NetExec, high-value group targets
- **Share Enumeration & Spidering** — NetExec --spider-shares, smbclient
- **LDAP Enumeration** — nxc ldap, get-desc-users, ldapsearch
- **Kerberos Attack Surface** — ASREPRoastable accounts (GetNPUsers), Kerberoastable accounts (GetUserSPNs)
- **AD Attack Path Mapping** — BloodHound / bloodhound-python, key queries
- **Code Execution & Credential Dumping** — nxc -x/-X, --sam, --lsa

## Key tools covered
`nmap` `nxc / crackmapexec` `enum4linux-ng` `rpcclient` `kerbrute` `smbclient`
`GetADUsers.py` `GetNPUsers.py` `GetUserSPNs.py` `ldapdomaindump` `bloodhound-python` `SharpHound`
