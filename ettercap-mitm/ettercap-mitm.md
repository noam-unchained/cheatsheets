Ettercap MITM - General Cheat Sheet

A general ARP-poisoning man-in-the-middle workflow with ettercap (GUI).
Replace the placeholders (<...>) with your own values.


Step 1 - Launch the GUI

    sudo ettercap -G


Step 2 - In the GUI

1. Select your interface (e.g. eth0) and click the checkmark to start unified sniffing.
2. Menu -> Hosts -> Scan for hosts.
3. Menu -> Hosts -> Hosts list.
4. Click your first endpoint (e.g. server / gateway / DC) -> Add to Target 1.
5. Click your second endpoint (e.g. victim client) -> Add to Target 2.
6. MITM (globe) icon -> ARP poisoning -> tick "Sniff remote connections" -> OK.
7. Bottom log should show "ARP poisoning victims" with Group 1 and Group 2.


Step 3 - Verify it worked

On the victim machine:

    arp -a

The target's IP should now show Kali's MAC address instead of its real one.
That means traffic is flowing through Kali.


Step 4 - (optional) Capture traffic

Open Wireshark on the same interface and filter on the two target IPs:

    ip.addr == <target1> && ip.addr == <target2>


Step 5 - Stop cleanly

MITM (globe) icon -> Stop MITM attack(s). This restores the real ARP entries.


(optional) Restore Kali's networking

Only needed if you manually set a static IP before the attack:

    sudo nmcli con mod "<connection name>" ipv4.method auto
    sudo nmcli con up "<connection name>"


Key idea: it's just "two targets + ARP poisoning". Target 1 and Target 2 are
the two endpoints whose traffic you want to sit between - often a client and
the gateway/DC.
