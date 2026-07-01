Web Enumeration - Cheat Sheet

Map a web target before attacking it: fingerprint the tech stack, brute-force
hidden directories and files, discover virtual hosts and subdomains, and pull
parameters. The goal is to expand the attack surface - find the pages, params,
and endpoints the app doesn't link to.
Replace the placeholders (<...>) with your own values.


Step 1 - Fingerprint the stack

    whatweb http://<target>
    nikto -h http://<target>          # quick vuln/misconfig sweep
    curl -sI http://<target>          # headers: Server, X-Powered-By, cookies

Check /robots.txt, /sitemap.xml, and page source / JS for hidden paths + API
routes. Note the server, framework, and any versions.


Step 2 - Directory & file brute force

feroxbuster (recursive, fast - recommended):

    feroxbuster -u http://<target> -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt \
        -x php,txt,html,bak -t 50

ffuf (FUZZ keyword marks the injection point):

    ffuf -u http://<target>/FUZZ -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt \
        -e .php,.txt,.html -mc 200,301,302,403

gobuster:

    gobuster dir -u http://<target> -w <wordlist> -x php,txt,html

Filter noise with ffuf: -fc 404 (filter code) / -fs <size> / -fw <words>.


Step 3 - Virtual host (vhost) discovery

Different sites can share one IP via the Host header. Fuzz it:

    ffuf -u http://<target> -H "Host: FUZZ.<domain>" \
        -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
        -fs <default-response-size>

Add discovered vhosts to /etc/hosts to browse them.


Step 4 - Subdomain enumeration (external / DNS)

    # passive
    subfinder -d <domain> -silent
    amass enum -passive -d <domain>

    # active brute
    ffuf -u http://FUZZ.<domain> -w <subdomain-wordlist> -mc 200,301,302

    # DNS zone transfer (if misconfigured)
    dig axfr <domain> @<ns-ip>

Resolve live hosts, then repeat Steps 1-2 on each interesting one.


Step 5 - Parameter & endpoint discovery

    # hidden GET/POST params
    ffuf -u "http://<target>/page?FUZZ=1" -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt -fs <size>
    # arjun (dedicated param finder)
    arjun -u http://<target>/page

    # pull URLs/params from wayback + crawling
    gau <domain> ; waybackurls <domain> ; katana -u http://<target>

Feed found params into your injection testing (see sqli / ssrf / xss).


Step 6 - Prioritise what you found

  - Login/admin panels        -> default creds / auth bypass / spraying
  - Upload forms              -> file-upload bypass
  - Params reflecting input   -> XSS / SSTI
  - Params hitting the backend-> SQLi / command injection
  - URLs/SSRF-looking params  -> SSRF (see ssrf cheatsheet)
  - .bak / .git / config files-> source + secrets (try /.git/ dumping)


Wordlists (SecLists) worth knowing
    Discovery/Web-Content/raft-*-directories.txt / -files.txt
    Discovery/Web-Content/directory-list-2.3-medium.txt
    Discovery/DNS/subdomains-top1million-*.txt
    Discovery/Web-Content/burp-parameter-names.txt


Key idea: web enumeration is attack-surface expansion. The app only links to a
fraction of what exists - brute forcing directories, vhosts, subdomains, and
parameters surfaces the forgotten admin panel, the dev endpoint, the backup
file, or the unlinked API that becomes your way in. Fingerprint first, then
fuzz broadly, then drill into whatever looks abnormal.
