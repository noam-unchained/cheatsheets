Nmap - General Cheat Sheet

A general network scanning workflow with nmap.
Replace the placeholders (<...>) with your own values.


Step 1 - Host Discovery

Discover live hosts before deep-scanning:

    nmap -sn <target-range>

    Common target formats:
      192.168.1.1          single host
      192.168.1.0/24       entire subnet
      192.168.1.1-50       IP range

    -sn   ping scan only (no port scan) — just find who's alive
    -Pn   skip host discovery, assume all hosts are up (useful when ICMP is blocked)


Step 2 - Port Scan

Choose a scan type based on your situation:

    nmap -sS <target>      (recommended — stealth SYN scan, requires root)
    nmap -sT <target>      (TCP connect — no root needed, but easily logged)
    nmap -sU <target>      (UDP scan — slow, use with --top-ports to limit)

    Useful port flags:
      -p <ports>           e.g. -p 80, -p 1-1000, -p 22,445,3389
      -p-                  scan all 65,535 ports
      -F                   fast scan — top 100 ports only
      --top-ports <n>      scan the n most common ports

    Timing (speed vs. stealth trade-off):
      -T0 / -T1            paranoid / sneaky  (very slow, very stealthy)
      -T3                  normal (default)
      -T4 / -T5            aggressive / insane (fast, noisy)


Step 3 - Version and OS Detection

Identify what is running on open ports:

    nmap -sV <target>      service version detection
    nmap -O  <target>      OS fingerprinting (requires root)
    nmap -A  <target>      aggressive: enables -sV, -O, default scripts, and traceroute

    Useful extras:
      -n     disable reverse DNS (speeds things up)
      -v     verbose output
      -vv    even more verbose


Step 4 - NSE Scripts

Run the Nmap Scripting Engine for deeper checks:

    nmap --script=default <target>          same as -sC
    nmap --script=vuln    <target>          check for known CVEs
    nmap --script=auth    <target>          test default/weak credentials

    Common individual scripts:
      --script smb-vuln-ms17-010            EternalBlue check (port 445)
      --script smb-enum-shares              list accessible SMB shares
      --script smb-enum-users               enumerate users via SMB
      --script ldap-search                  query AD over LDAP (port 389)
      --script ftp-anon                     check for anonymous FTP login
      --script http-title                   grab HTTP page titles
      --script ssh-brute --script-args userdb=<users>,passdb=<wordlist-path>


Step 5 - Save Output

Always save results — you'll want them later:

    nmap -oN <output.txt>   human-readable
    nmap -oX <output.xml>   XML (importable into Metasploit, etc.)
    nmap -oA <basename>     save all three formats at once


Putting it all together (common scan combos):

    Quick sweep of a subnet:
        nmap -sn 192.168.1.0/24

    Stealth scan with version detection, save output:
        nmap -sS -sV -T4 -oN <output.txt> <target>

    Full aggressive scan (all ports):
        nmap -A -p- -T4 <target>

    EternalBlue check:
        nmap -p 445 --script smb-vuln-ms17-010 <target>

    Full vulnerability scan:
        nmap -sV --script vuln -p- <target>

    UDP top-20 ports:
        nmap -sU --top-ports 20 <target>


Key idea: always start broad (host discovery, top ports) and then narrow down.
-A is great for CTFs and labs; use -sS with careful timing for stealthier engagements.
