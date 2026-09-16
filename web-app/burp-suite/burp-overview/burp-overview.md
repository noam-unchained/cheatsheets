Burp Suite - Overview Cheat Sheet

Burp Suite is the core web-app testing proxy: it sits between your browser and
the target, letting you intercept, inspect, modify, and replay HTTP(S) traffic.
This is the setup + workflow hub - see burp-repeater and burp-intruder for the
attack tools.
Replace the placeholders (<...>) with your own values.


Step 1 - Start Burp and the pre-configured browser

Easiest path: use Burp's built-in Chromium - proxy + cert already trusted.

    Proxy tab -> Intercept -> "Open Browser"

Everything you browse there flows through Burp automatically.


Step 2 - (Manual) Point your own browser at Burp

If you prefer your own browser:
  - Proxy listener default: 127.0.0.1:8080 (Proxy -> Proxy settings).
  - Set the browser/system HTTP+HTTPS proxy to 127.0.0.1:8080
    (FoxyProxy extension makes toggling easy).


Step 3 - Install Burp's CA certificate (to see HTTPS)

Without the CA, HTTPS sites throw cert errors. With Burp running + proxied:

    Browse to:  http://burp
    Download "CA Certificate" (cacert.der) -> import into the browser/OS as a
    trusted Root CA.

Firefox: Settings -> Certificates -> Import -> trust for websites.


Step 4 - Set your scope (do this early)

Scope keeps noise out and stops you hitting out-of-scope hosts:

    Target -> Site map -> right-click the host -> "Add to scope"
    Target -> Scope settings -> enable "Use advanced scope control" if needed
    Proxy/HTTP history -> filter -> "Show only in-scope items"

Also enable: Settings -> "Drop out-of-scope requests" to stay safe.


Step 5 - The core loop (intercept <-> history)

  - Proxy -> Intercept ON  -> requests pause so you can edit before forwarding
        Forward / Drop each held request.
  - Proxy -> Intercept OFF -> traffic flows; review it in HTTP history.
  - HTTP history is your log of everything - search/filter it heavily.


Step 6 - Send requests to the right tool (the hub move)

Right-click any request (in history, Repeater, etc.) -> "Send to ...":

    Send to Repeater   (Ctrl+R)   -> manual tampering / iterate one request
    Send to Intruder   (Ctrl+I)   -> automated fuzzing / many payloads
    Send to Comparer              -> diff two requests or responses
    Send to Decoder               -> encode/decode/hash a value
    Send to Organizer             -> save interesting requests for later

See burp-repeater and burp-intruder for those workflows.


Step 7 - Quick tour of the other tools

  - Decoder    : URL/Base64/HTML/hex encode-decode, hashing. Fast field work.
  - Comparer   : word/byte diff - great for blind-injection true/false pages.
  - Sequencer  : analyze randomness of session tokens / CSRF tokens.
  - Extensions : BApp Store -> Autorize (authz testing), Logger++, JSON Web
                 Tokens, Param Miner, Active Scan++ (Pro).


Handy shortcuts
    Ctrl+R  send to Repeater       Ctrl+I  send to Intruder
    Ctrl+Shift+B  Base64 selection Ctrl+Shift+U  URL-decode selection
    Ctrl+F  forward intercept


Cautions
  - Community Edition: Intruder is heavily throttled; no active scanner.
  - Only test targets you are authorized to test.


Key idea: Burp is a man-in-the-middle for your own browser. You proxy traffic,
trust its CA so HTTPS is readable, scope to the target, then capture requests
and fan them out to the specialised tools - Repeater to hand-craft, Intruder to
automate. Almost every web attack starts by grabbing the right request here and
pressing Ctrl+R or Ctrl+I.
