SMB Enumeration - Cheat Sheet

Enumerate Windows/Samba SMB (TCP 445): identify hosts and OS, list shares,
read readable shares, pull users via RID brute, check the password policy, and
spot signing/null-session misconfigs. SMB is one of the richest recon surfaces
in a Windows network. Primary tool: nxc (NetExec).
Replace the placeholders (<...>) with your own values.


Step 1 - Find SMB hosts + fingerprint

    nxc smb <target-or-cidr>
    # e.g. nxc smb 192.168.1.0/24

Output shows hostname, domain, OS build, and "signing:True/False" +
"SMBv1:True/False". signing:False = relay-able (see ntlm-relay). Note the
domain name and DC.


Step 2 - Null / guest / anonymous session

Try unauthenticated access first (no creds):

    nxc smb <target> -u '' -p ''            # null session
    nxc smb <target> -u 'guest' -p ''       # guest
    smbclient -L //<target>/ -N             # list shares, no auth


Step 3 - Enumerate shares

    nxc smb <target> -u <user> -p <pass> --shares      # shows READ/WRITE perms
    smbmap -H <target> -u <user> -p <pass>             # perms + recursive view

Look for non-default shares and READ/WRITE on anything beyond IPC$. Juicy:
SYSVOL, NETLOGON, Backups, IT, Users, home shares.


Step 4 - Browse / loot readable shares

    smbclient //<target>/<share> -U '<user>%<pass>'
      # inside: ls, cd, get <file>, recurse ON, prompt OFF, mget *

    # spider all readable shares for interesting files:
    nxc smb <target> -u <user> -p <pass> -M spider_plus
    nxc smb <target> -u <user> -p <pass> --spider <share> --regex '(pass|cred|\.kdbx|\.config)'

Hunt for: passwords in scripts/configs, .kdbx, unattend.xml, Groups.xml
(GPP cpassword), web.config, backups.


Step 5 - Users, groups, policy (authenticated or null)

    nxc smb <target> -u <user> -p <pass> --users        # domain users
    nxc smb <target> -u '' -p '' --rid-brute            # users via RID (null)
    nxc smb <target> -u <user> -p <pass> --groups
    nxc smb <target> -u <user> -p <pass> --pass-pol     # lockout policy (spray-safe)
    nxc smb <target> -u <user> -p <pass> --loggedon-users

The user list feeds password spraying; --pass-pol tells you the lockout
threshold before you spray.


Step 6 - Deeper enumeration & quick wins

    enum4linux-ng -A <target>                           # all-in-one legacy enum
    nxc smb <target> -u <user> -p <pass> --sam          # local SAM (needs admin)
    nxc smb <target> -u <user> -p <pass> -M gpp_password # GPP cpassword decrypt

    # check for admin ("Pwn3d!"):
    nxc smb <target> -u <user> -p <pass>                # look for (Pwn3d!)


Common wins to watch for
  - Readable share with creds/config      -> new credentials
  - Groups.xml GPP cpassword               -> decryptable domain password
  - signing:False                          -> NTLM relay target
  - null session + --rid-brute             -> full user list with no creds
  - "(Pwn3d!)"                             -> local admin -> dump SAM / LSASS


Key idea: SMB leaks an enormous amount before you even authenticate - host and
OS details, whether signing protects it, and often (via null sessions) the
entire user list. Once you have any credential, shares are where secrets hide:
scripts, backups, and GPP files routinely hand over the next password. Always
check --pass-pol before spraying and note signing:False hosts for relay.
