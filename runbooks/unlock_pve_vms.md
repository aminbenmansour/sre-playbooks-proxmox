---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
---

# Runbook: Remediate `locked: backup` State on PVE VMs

**Severity:** P2 / P3
**SRE Owner:** Infrastructure Pod
**Context:** A VM is locked by a stale backup task. Attempting to manage the VM results in `VM is locked (backup)`.

> **⚠️ WARNING:** Never unlock a VM if the backup process `vzdump` is actively writing blocks. Doing so during an active snapshot commit can cause severe data corruption.

### Step 1: Initialize API Environment
Set your target cluster and authenticate.

```python
import os
from proxmoxer import ProxmoxAPI

# Read from Vault or local env vars
PVE_HOST = os.getenv("PVE_CLUSTER_ENDPOINT", "pve-api.internal.corp")
USER = os.getenv("PVE_USER", "sre-api@pam")
TOKEN_NAME = "runbook-token"
TOKEN_VALUE = os.getenv("PVE_TOKEN")

proxmox = ProxmoxAPI(
    PVE_HOST, user=USER, token_name=TOKEN_NAME, token_value=TOKEN_VALUE, verify_ssl=True
)
print(f"✅ Authenticated to {PVE_HOST}")
```

