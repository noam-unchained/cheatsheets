Burp Repeater - Cheat Sheet

Repeater is Burp's manual request editor: send one HTTP request, edit any part
of it, resend, and read the response - over and over. It's where you hand-test
a single endpoint for auth bypass, IDOR, injection, and logic flaws.
See burp-suite (hub) for proxy setup and burp-intruder for automation.
Replace the placeholders (<...>) with your own values.


Step 1 - Get a request into Repeater

From Proxy HTTP history, Site map, or anywhere:

    Right-click the request -> "Send to Repeater"   (or Ctrl+R)
    Switch to the Repeater tab.

Each request opens in its own numbered tab - rename tabs (double-click) so you
don't lose track.


Step 2 - Send and read

    Click "Send"  (or Ctrl+Space)  -> response shows on the right.

Use the response view tabs: Pretty / Raw / Hex / Render. "Render" shows the
page roughly as a browser would - handy for spotting reflected output.


Step 3 - Edit the request and resend

Change anything, then Send again:
  - Parameters (GET query, POST body, JSON fields)
  - Headers (Cookie, Authorization, User-Agent, Host, X-Forwarded-For)
  - Method (right-click -> "Change request method" to flip GET<->POST)

This tight edit->send->observe loop is the whole point of Repeater.


Step 4 - Common manual tests

Auth / session:
  - Remove the Cookie / Authorization header -> still 200? broken auth.
  - Swap your session cookie for another user's -> see their data? broken authz.

IDOR (Insecure Direct Object Reference):
  - Change id=1001 -> id=1002 and resend -> do you get another user's record?

Injection probes (one char at a time, watch the response):
  - SQLi:  add '  to a param -> SQL error / changed response
  - SSTI:  {{7*7}} -> response shows 49
  - Command: ;id  / |id  / `id`  -> command output in response

Header tricks:
  - X-Forwarded-For: 127.0.0.1   (IP allow-list bypass)
  - Host: evil.tld               (host-header injection / routing)


Step 5 - Compare responses

To spot subtle true/false differences (great for blind bugs):

    Right-click response -> "Send to Comparer"  (send two; diff word/byte)

Repeater also shows response length + status + time - watch those columns;
a length or timing change often reveals the vuln before the body does.


Step 6 - Iterate efficiently

  - History arrows (< >) step through previous versions of THIS request.
  - "Send" repeatedly to confirm consistent behaviour.
  - Copy as curl: right-click -> "Copy as curl command" for your notes/report.


Tips
  - Update Content-Length: Burp auto-fixes it on Send by default - good.
  - Keep one Repeater tab per idea; rename them (login-bypass, idor-orders...).
  - URL-encode tricky payloads: select -> Ctrl+U (or Ctrl+Shift+U to decode).


Key idea: Repeater is the surgical tool - one request, infinite controlled
edits. When you have a hunch about a single endpoint (a parameter, a header, a
session check), Repeater lets you test it by hand, change exactly one thing,
resend, and read the answer. When you need to try MANY values automatically,
that's Intruder's job instead.
