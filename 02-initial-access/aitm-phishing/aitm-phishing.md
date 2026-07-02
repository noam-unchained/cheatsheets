AiTM Phishing (MFA Bypass) - Cheat Sheet

Adversary-in-the-Middle phishing: stand a reverse proxy between the victim and
the real login page (e.g. Microsoft 365). The victim authenticates - including
MFA - against the genuine site through your proxy, and you capture the
resulting SESSION COOKIE / token. Replaying the cookie skips MFA entirely.

>>> AUTHORIZED ENGAGEMENTS ONLY. Use only with written permission for a
    sanctioned phishing/red-team assessment. <<<
Replace the placeholders (<...>) with your own values.


Why AiTM beats classic phishing
Classic credential phishing fails the moment MFA is on - you get the password
but not the second factor. AiTM proxies the entire real login flow, so the
victim completes MFA on the legitimate server. You don't steal the factor;
you steal the authenticated session that MFA produced.


Step 1 - Infrastructure (lab/authorized)

  - A VPS you control + a look-alike domain (typosquat of the client's).
  - Valid TLS cert (Let's Encrypt) so the page looks legitimate.
  - Reverse-proxy phishing framework: Evilginx (most common) or Modlishka.


Step 2 - Configure Evilginx

    # set the domain + external IP
    config domain <phish-domain>
    config ipv4 external <vps-ip>

    # load a phishlet (proxy template) for the target service
    phishlets hostname o365 <phish-domain>
    phishlets enable o365

    # create the capture/redirect link
    lures create o365
    lures get-url <id>          # this is the link you send (authorized test)


Step 3 - Deliver (within scope of the assessment)
Send the lure URL through the agreed channel (email pretext approved by the
client). The victim clicks, sees the real M365 login proxied through your
domain, logs in, and completes MFA.


Step 4 - Harvest the session
Evilginx captures, per victim:
    - username + password (plaintext, as typed)
    - the authenticated SESSION COOKIES / tokens (the prize)

    sessions                 # list captured sessions
    sessions <id>            # view tokens/cookies for one victim


Step 5 - Replay the session (skip MFA)
Import the captured cookies into a browser to ride the authenticated session:

  - Use a cookie-editor extension (e.g. "Cookie-Editor") and paste the
    ESTSAUTH / session cookies, then browse to https://office.com - you are
    logged in as the victim WITHOUT re-doing MFA.
  - From there, pivot into the tenant (see entra-id-attacks): read mail,
    enumerate with ROADrecon, register persistence.


Step 6 - Turn the session into durable access
Cookies expire - convert to something longer-lived fast:
    - Enroll your own MFA method / register a device on the victim.
    - Add an app secret or OAuth consent for offline_access (refresh token).
    - Harvest a refresh token from the session for re-auth.


Defender notes (so you can report fixes)
  - Phishing-resistant MFA (FIDO2 / passkeys, certificate-based) defeats AiTM -
    the cookie is bound to the origin/device and won't replay.
  - Conditional Access: require compliant/managed device + token protection.
  - Detections: impossible-travel, new-device sign-ins, sign-ins from hosting
    ASNs, anomalous user-agents.


Key idea: AiTM phishing doesn't beat MFA by cracking it - it lets the victim
pass MFA on the real server and steals the session token that results. The
token, not the password, is the asset, and a replayed session inherits the
MFA the victim just completed. The only real fix is phishing-resistant MFA
that binds the credential to the device/origin. Authorized testing only.
