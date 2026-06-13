Ettercap MITM - General Cheat Sheet

A general ARP-poisoning man-in-the-middle workflow with ettercap (GUI).
Replace the placeholders (<...>) with your own values.


Step 1 - Prep Kali's network

Make sure Kali is on the same subnet as your targets, and ideally only that
subnet (extra IPs make ettercap scan the wrong network). With NetworkManager,
pin a single static lab IP:

    sudo nmcli con mod "<connection name>" ipv4.method manual ipv4.addresses <kali-ip>/24
    sudo nmcli con up "<connection name>"
    ip -4 addr show <interface>      # confirm only the lab IP is present


Step 2 - Launch the GUI

    sudo ettercap -G


Step 3 - In the GUI

1. Select your interface (e.g. eth0) and click the checkmark to start unified sniffing.
2. Menu -> Hosts -> Scan for hosts.
3. Menu -> Hosts -> Hosts list.
4. Click your first endpoint (e.g. server / gateway / DC) -> Add to Target 1.
5. Click your second endpoint (e.g. victim client) -> Add to Target 2.
6. MITM (globe) icon -> ARP poisoning -> tick "Sniff remote connections" -> OK.
7. Bottom log should show "ARP poisoning victims" with Group 1 and Group 2.


Step 4 - Verify it worked

On the victim machine:

    arp -a

The target's IP should now show Kali's MAC address instead of its real one.
That means traffic is flowing through Kali.


Step 5 - (optional) Capture traffic

Open Wireshark on the same interface and filter on the two target IPs:

    ip.addr == <target1> && ip.addr == <target2>


Step 6 - Stop cleanly

MITM (globe) icon -> Stop MITM attack(s). This restores the real ARP entries.


Step 7 - Restore Kali's normal networking

If you changed it in Step 1, switch back to DHCP:

    sudo nmcli con mod "<connection name>" ipv4.method auto
    sudo nmcli con up "<connection name>"


Key idea: it's just "two targets + ARP poisoning". Target 1 and Target 2 are
the two endpoints whose traffic you want to sit between - often a client and
the gateway/DC.
