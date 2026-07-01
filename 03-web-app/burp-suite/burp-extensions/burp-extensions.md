Burp Extensions - Cheat Sheet

Extensions (from the BApp Store) bolt extra capabilities onto Burp. A few are
near-essential for real web testing - especially Autorize for authorization
bugs and Param Miner for hidden parameters. All below work in Community Edition.
See burp-overview (hub) for proxy setup.
Replace the placeholders (<...>) with your own values.


Step 1 - Install extensions

    Extensions tab -> BApp Store -> search -> Install.

Some need Jython (Python extensions) or a JDK. If an extension is greyed out,
set the environment: Extensions -> Extensions settings -> Python environment
(point to jython-standalone.jar).


Step 2 - Autorize (authorization / IDOR testing) ★ must-have

Tests every request as a LOW-priv user automatically while you browse as HIGH.

    1. Log in as the HIGH-priv user in Burp's browser.
    2. Autorize tab -> "Configure" -> paste the LOW-priv user's Cookie /
       Authorization header into the box.
    3. Click "Autorize is off" -> turn it ON.
    4. Browse the app as the high-priv user normally.

Autorize replays each request with the low-priv session and flags:
    - "Bypassed!"      -> low-priv user got the same data = broken authz (IDOR)
    - "Enforced!"      -> properly blocked
    - "Is enforced???" -> check manually
Catches horizontal/vertical privilege bugs across the whole app at once.


Step 3 - Param Miner (find hidden parameters / headers) ★ useful

Brute-forces unlinked params and headers the app secretly honours.

    Right-click request -> Extensions -> Param Miner -> "Guess parameters"
    (also: "Guess headers", "Guess cookies")

Great for finding hidden debug params, and for web-cache-poisoning research
(unkeyed inputs). Results show in the Issues/Extensions output.


Step 4 - JWT Editor (attack JSON Web Tokens)

Adds a "JSON Web Token" tab to Repeater for tampering JWTs:
    - alg:none attack (strip the signature)
    - weak HMAC secret -> crack offline, re-sign
    - key confusion (RS256 -> HS256 using the public key as HMAC secret)
    - embedded JWK / kid header injection
Decode + edit claims (e.g. "role":"admin") and re-sign, then resend.


Step 5 - Logger++ (advanced logging / search)

A powerful, filterable log across ALL Burp tools (not just Proxy history).
    - Regex/grep across every request+response.
    - Custom columns, export to CSV for the report.
Use when HTTP history filtering isn't enough.


Other handy extensions
    - Active Scan++      : extra passive/active checks (boosts the scanner; Pro).
    - Turbo Intruder     : super-fast, scriptable request sending (beats CE
                           Intruder throttling for big fuzzes).
    - Hackvertor        : tag-based inline encoding/encryption in requests.
    - Collaborator Everywhere / interactsh : out-of-band (OOB) hit detection.
    - Content Type Converter : flip JSON<->XML<->form to find parser bugs.


Tips
  - Turbo Intruder is the CE answer to throttled Intruder - load a template,
    set requests-per-second, run thousands fast.
  - Keep only the extensions you need loaded - each adds memory + passive
    checks that slow Burp.


Key idea: stock Burp covers the core loop; extensions cover the specialised
work. The two that change your testing the most are Autorize (it finds broken
access control across the entire app automatically while you just browse) and
Param Miner (it reveals inputs the app never advertised). JWT Editor, Logger++,
and Turbo Intruder round out tokens, logging, and fast fuzzing.
