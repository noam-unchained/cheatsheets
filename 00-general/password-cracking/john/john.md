John the Ripper - Cheat Sheet

Crack password hashes with John (jumbo). John's superpower is its huge library
of *2john tools that convert protected files (zip, PDF, SSH keys, KeePass,
shadow...) into crackable hashes, plus auto-format detection. Complements
hashcat - John for format wrangling + CPU, hashcat for raw GPU speed.
Replace the placeholders (<...>) with your own values.


Step 1 - Get the hash into John format

Many *2john extractors ship with jumbo John - convert a file to a hash:

    zip2john secret.zip > zip.hash
    rar2john secret.rar > rar.hash
    pdf2john.pl doc.pdf > pdf.hash
    ssh2john id_rsa > ssh.hash           # crack an encrypted SSH key passphrase
    keepass2john db.kdbx > kp.hash
    office2john report.docx > office.hash
    # Linux local accounts (root): combine passwd + shadow:
    unshadow /etc/passwd /etc/shadow > linux.hash

(There are 100+ *2john scripts: bitlocker2john, 7z2john, gpg2john, etc.)


Step 2 - Basic wordlist crack (auto-detect format)

    john --wordlist=/usr/share/wordlists/rockyou.txt <hashfile>
    john --show <hashfile>                 # print cracked results

John auto-detects the format for combined hashes. If it guesses wrong or you
need to force it:

    john --list=formats | grep -i <keyword>
    john --format=<name> --wordlist=rockyou.txt <hashfile>
      # e.g. --format=krb5tgs (kerberoast), --format=NT (NTLM), --format=sha512crypt


Step 3 - Wordlist + rules

    john --wordlist=rockyou.txt --rules <hashfile>            # default rules
    john --wordlist=rockyou.txt --rules=Jumbo <hashfile>      # bigger ruleset
    john --wordlist=rockyou.txt --rules=KoreLogic <hashfile>


Step 4 - Incremental (brute force) & mask

    john --incremental <hashfile>                  # smart brute (Markov)
    john --mask='?u?l?l?l?l?d?d' <hashfile>         # like hashcat masks
    john --incremental=Digits <hashfile>           # digits only


Step 5 - Manage cracking runs

    john --show <hashfile>                 # cracked so far (user:password)
    john --status                          # progress of the running session
    john --restore                         # resume the last interrupted session
    # cracked passwords are stored in ~/.john/john.pot (reused automatically)
    # crack only specific users:
    john --users=<user1,user2> <hashfile>


Step 6 - Common conversions -> crack (end to end)

    zip2john x.zip > h && john --wordlist=rockyou.txt h && john --show h
    ssh2john id_rsa > h && john --wordlist=rockyou.txt h        # then ssh -i id_rsa
    keepass2john db.kdbx > h && john --wordlist=rockyou.txt h   # then open .kdbx


John vs Hashcat (when to pick)
  - John: unmatched *2john file converters, auto-detect, great on CPU, easy for
    "I have this weird protected file" moments.
  - Hashcat: far faster on GPU for big/slow hashes (bcrypt, AES tickets, WPA).
  Workflow: use *2john to extract, then crack with whichever is faster - the
  hash format maps to a hashcat -m mode too.


Key idea: John's edge is breadth - it turns almost any password-protected
artifact into a hash with a *2john tool and figures out the format for you, so
you spend time cracking, not wrangling. Reach for John when you have an
encrypted zip/PDF/SSH key/KeePass to open; reach for hashcat when you need raw
GPU throughput on a slow hash.
