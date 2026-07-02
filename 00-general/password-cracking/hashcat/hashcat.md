Hashcat - Cheat Sheet

Crack captured hashes offline with GPU acceleration. The workflow is always:
identify the hash type -> pick the right mode (-m) -> choose an attack
(wordlist, rules, mask) -> run -> show cracked. This is the companion to every
cheatsheet that captures a hash (kerberoasting, asrep, NTLM, NetNTLMv2, JWT...).
Replace the placeholders (<...>) with your own values.


Step 1 - Identify the hash type -> get the mode number

    hashid '<hash>'                 # guesses the format
    nth --text '<hash>'             # name-that-hash (also suggests hashcat -m)
    hashcat --help | grep -i <keyword>

Common modes (-m):
    0      MD5                        1000   NTLM (NT hash)
    100    SHA1                       1800   sha512crypt ($6$ Linux shadow)
    3200   bcrypt ($2*$)              5600   NetNTLMv2 (Responder capture)
    13100  Kerberoast RC4 ($krb5tgs$23$)   19700  Kerberoast AES256 ($krb5tgs$18$)
    18200  AS-REP ($krb5asrep$23$)    22000  WPA-PBKDF2 (wifi)
    16500  JWT (HS256)                 500    md5crypt ($1$)


Step 2 - Basic wordlist attack (mode -a 0)

    hashcat -m <mode> <hashfile> /usr/share/wordlists/rockyou.txt

    # multiple hashes: one per line in <hashfile>. Add --username if the file
    # is user:hash format (e.g. secretsdump / NTDS output):
    hashcat -m 1000 ntlm.hashes /usr/share/wordlists/rockyou.txt --username


Step 3 - Wordlist + rules (best bang for buck)

Rules mutate each word (add digits, capitalise, leetspeak, etc.):

    hashcat -m <mode> <hashfile> rockyou.txt -r /usr/share/hashcat/rules/best64.rule
    hashcat -m <mode> <hashfile> rockyou.txt -r /usr/share/hashcat/rules/OneRuleToRuleThemAll.rule

best64 is fast; OneRuleToRuleThemAll is thorough. Rules multiply attempts by
the ruleset size - big coverage gain for weak-but-mutated passwords.


Step 4 - Mask / brute-force attack (mode -a 3)

For known patterns. Charsets: ?l lower ?u upper ?d digit ?s symbol ?a all.

    hashcat -m <mode> <hashfile> -a 3 '?u?l?l?l?l?l?d?d'      # Word12 style
    hashcat -m <mode> <hashfile> -a 3 '<Company>?d?d?d?s'     # policy-guess

    # increment length automatically:
    hashcat -m <mode> <hashfile> -a 3 ?a?a?a?a?a?a --increment


Step 5 - Combinator / hybrid

    # wordlist + mask appended (word2024!):
    hashcat -m <mode> <hashfile> -a 6 rockyou.txt '?d?d?d?d?s'
    # mask + wordlist prepended:
    hashcat -m <mode> <hashfile> -a 7 '?d?d?d?d' rockyou.txt


Step 6 - Run control & results

    hashcat -m <mode> <hashfile> <wordlist> -O -w 3        # -O optimized, -w workload
    hashcat -m <mode> <hashfile> --show                    # print cracked (user:pass)
    hashcat -m <mode> <hashfile> --left                    # show still-uncracked
    # session save/restore for long runs:
    hashcat ... --session myrun          # then: hashcat --session myrun --restore

Cracked results are stored in ~/.hashcat/hashcat.potfile (reused automatically).
Press 's' for status, 'p' pause, 'q' quit while running.


Tips
  - No GPU? add --force (CPU) - much slower. Cloud GPU for AES/bcrypt.
  - Kerberoast/asrep: prefer RC4 ($23$) targets - far faster than AES ($18$/$17$).
  - Estimate feasibility with --keyspace before committing to a big mask.
  - John the Ripper is the alternative (auto-detects format): john --wordlist=... <file>


Key idea: cracking is offline and parallel - the only real levers are the hash
type (some are deliberately slow: bcrypt, sha512crypt, AES tickets) and how
smartly you attack (a good wordlist + rules beats blind brute force almost
every time). Nail the mode number, throw rockyou + a rule at it first, then
escalate to masks and hybrids only for what survives.
