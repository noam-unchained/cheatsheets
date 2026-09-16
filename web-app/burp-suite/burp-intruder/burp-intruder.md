Burp Intruder - Cheat Sheet

Intruder automates sending a request many times with varying values injected at
positions you choose. Use it to fuzz parameters, brute-force, enumerate IDs,
and test payload lists. Repeater is for ONE request by hand; Intruder is for
MANY automatically. See burp-suite (hub) for setup.
Replace the placeholders (<...>) with your own values.


Step 1 - Send a request to Intruder

    Right-click request -> "Send to Intruder"  (or Ctrl+I)
    Open the Intruder tab.


Step 2 - Set payload positions (the § markers)

Intruder marks where payloads get injected with § §:

    "Clear §"  -> removes all auto-marked positions
    select the value you want to fuzz -> "Add §"

Example - fuzz one parameter:
    GET /api/user?id=§1§ HTTP/1.1


Step 3 - Pick the attack type (this decides how payloads map to positions)

  - Sniper        : 1 payload set, ONE position at a time. Default for
                    single-parameter fuzzing (e.g. test passwords for one user).
  - Battering ram : 1 payload set, SAME value in ALL positions at once.
                    (e.g. put the same token in two places.)
  - Pitchfork     : multiple sets, run in PARALLEL (set1[i] with set2[i]).
                    (e.g. user[i] + matching password[i] - credential pairs.)
  - Cluster bomb  : multiple sets, ALL COMBINATIONS (set1 x set2).
                    (e.g. every user x every password - full spray/brute matrix.)


Step 4 - Load payloads

    Payloads tab -> Payload set (which position) -> Payload type:
      Simple list   : paste/import a wordlist
      Numbers       : ranges (e.g. 1000-2000 for ID enumeration)
      Runtime file  : stream a big wordlist from disk
      Brute forcer  : char sets + length
    Payload processing: add rules (prefix/suffix, hash, Base64-encode, etc.)
    URL-encode: keep "URL-encode these characters" on for safety.


Step 5 - Mark what "interesting" looks like (Grep)

    Settings -> Grep - Match: flag responses containing a string
        e.g. "Welcome", "Invalid", "admin", error signatures.
    A new result column shows hits -> sort by it to find the outlier.


Step 6 - Run and read results

    "Start attack"  -> results table opens.
    Sort by:
      Status   (e.g. 200 vs 302/401 - the odd one out)
      Length   (a different response size = different behaviour)
      Time     (spikes = time-based injection)
      Grep col (your match flag)
    The result that BREAKS the pattern is usually the finding.


Common use cases
  - Login brute / spray   : Cluster bomb (users x passwords) or Sniper (pwds).
  - ID / IDOR enumeration : Sniper + Numbers payload over id=§...§.
  - Hidden param / value  : Sniper + wordlist; watch Length/Status.
  - Token testing         : Pitchfork to pair CSRF token + request.


Caveats
  - Community Edition throttles Intruder to ~1 req/sec - painful for big
    lists. For heavy brute force use ffuf / wfuzz / hydra instead, then come
    back to Burp/Repeater to confirm the hit.
  - Set "Resource pool" throttle/delay to avoid lockouts and rate limits.
  - Only test authorized targets.


Key idea: Intruder = request template + payload positions (§) + an attack type
that decides how payloads fill those positions. Sniper for one knob, Cluster
bomb for the full matrix, Pitchfork for paired lists. You don't read every
response - you sort by status/length/time/grep and chase the one that breaks
the pattern. For large brute force, a dedicated fuzzer is faster than CE
Intruder.
