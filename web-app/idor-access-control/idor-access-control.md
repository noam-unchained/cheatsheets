# IDOR / Broken Access Control

The app checks *authentication* (who you are) but not *authorisation* (whether you're allowed to
touch **this** object or action). Change an identifier — or just visit a privileged endpoint — and
you reach another user's data (**horizontal**) or admin functionality (**vertical**). OWASP #1.

Replace placeholders (`<...>`) with your own values.

---
---

# PART 1 — OVERVIEW (at a glance)

## The variants

| Variant | You change… | You get |
|---------|-------------|---------|
| **IDOR (horizontal)** | an object id (`?id=124`→`123`) | another user's data/actions |
| **Vertical (privilege)** | the endpoint/role you hit | admin functionality as a normal user |
| **Forced browsing** | the URL you visit | hidden/unlinked admin pages |
| **Parameter/method** | a param (`role=user`→`admin`) or method | more than the UI allows |
| **Mass assignment** | extra fields in the body | set fields you shouldn't (`isAdmin:true`) |

## The workflow

1. **Map** objects and roles — capture requests as a low-priv user and note every id/reference.
2. **Tamper** the reference — increment/swap ids, change a role param, change the HTTP method.
3. **Test both axes** — horizontal (other users) and vertical (admin actions).
4. **Confirm with two accounts** — do user-B's requests work with user-A's session?

## Go-to tests

```
GET /api/user/123        → try 122, 124, other users' ids
GET /admin/...           → hit it directly as a low-priv user (forced browsing)
role=user                → role=admin        method=GET → POST/PUT/DELETE
{"id":1,"role":"user"}   → add "isAdmin":true (mass assignment)
```

## Defender notes (for the report)

- **Enforce authorisation server-side on every request**, per object — "does *this* user own/
  may access *this* id?" — not just "is the user logged in."
- **Deny by default**; don't rely on hidden URLs; use unpredictable references + ownership checks.

---
---

# PART 2 — DETAILED WALKTHROUGH

## Step 1 — Map objects & roles

Browse the whole app as a **low-privilege** user through Burp. Note every request that references
an object: `?id=`, `/user/5`, `/order/1001`, `uuid`, `filename`, `account`, `doc`. Note which
features are admin-only. Ideally get **two accounts** (user-A, user-B) to test cross-access.

## Step 2 — Horizontal IDOR (other users' data)

Change the identifier and see if you get someone else's object:

```
GET /api/user/123           → 122, 124, 1, 9999
GET /invoice?id=1001        → 1000, 1002
GET /files/download?f=me.pdf → ../otheruser/secret.pdf
```

```
what confirms it: user-A's session returns user-B's data / a 200 with someone else's record
```

UUIDs/hashes aren't safe if they leak elsewhere (in listings, emails, `Location` headers).

## Step 3 — Vertical (privilege escalation)

Access higher-privilege functionality as a normal user:

```
GET  /admin                       # forced browsing to admin UI
POST /api/admin/users             # call the admin API directly
GET  /api/user/123/promote        # privileged action endpoint
```

Copy an admin request (from docs/JS) and replay it with **your** low-priv session/cookie.

## Step 4 — Parameter & method tampering

```
role=user            → role=admin
userId=me            → userId=<victim>
GET /order/1         → change method to DELETE /order/1  (method not authz'd)
add a header the app trusts:  X-User-Id: 1 / X-Forwarded-For / X-Original-URL: /admin
```

## Step 5 — Mass assignment

Send fields the UI never exposes; frameworks that bind the whole body may accept them:

```json
POST /api/register {"user":"x","pass":"y","isAdmin":true,"role":"admin","verified":true}
PATCH /api/user/me {"balance":999999}
```

## Step 6 — Find hidden IDs

```
- Enumerate via listing endpoints (/api/users) that leak all ids
- Predict sequential ids; decode base64/hex ids; unwrap hashed ids seen elsewhere
- Wrap in an array/JSON:  id=123 → id[]=123&id[]=124  or  {"id":[123,124]}
```

---
---

# PART 3 — PAYLOAD ARSENAL

## Where references live (change these)

```
URL:      /user/123  /order/1001  ?id=  ?account=  ?doc=  ?file=
Body:     "userId":123  "role":"user"  "owner":"me"
Headers:  Cookie userid · X-User-Id · X-Original-URL · Referer-based checks
```

## ID transformation tricks

```
sequential:  123 → 122/124/1/9999
encoded:     base64/hex/rot — decode, change, re-encode
hashed id:   reuse a hash leaked in a listing/email/Location header
array wrap:  id=123 → id[]=123&id[]=124   |   {"id":[123,124]}
type juggle: id=123 → id=123.0 / "123" / id[$ne]= (also see nosql-injection)
path:        /me → /../otheruser   filename traversal
```

## Vertical / forced-browsing checklist

```
□ Hit /admin, /api/admin/*, /manage, /internal directly as a low-priv user
□ Replay an admin request with your low-priv session
□ Change method (GET↔POST↔PUT↔DELETE) on the same endpoint
□ Trust headers: X-User-Id, X-Original-URL: /admin, X-Forwarded-For
□ Mass assignment: add isAdmin/role/verified to the body
```

## Tools

```
Burp Autorize (extension)  → replay every request with a low-priv session, flags authz gaps
Burp Repeater/Intruder     → fuzz the id parameter across a range
```

---

**Key idea:** broken access control is a **missing check**, not a payload — the server authenticates
you but forgets to verify you're allowed to touch *this* object or run *this* action. Map every
reference and role, then tamper: change ids for horizontal access, hit privileged endpoints for
vertical, and add fields for mass assignment. Always confirm with a second account. Fix: enforce
per-object authorisation server-side, deny by default.
