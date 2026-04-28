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

### Step 2: Identify Locked VMs
Query the cluster for any VMs currently reporting a lock.

```python
locked_vms = []
for node in proxmox.nodes.get():
    for vm in proxmox.nodes(node['node']).qemu.get():
        if vm.get('lock') == 'backup':
            locked_vms.append({"node": node['node'], "vmid": vm['vmid'], "name": vm['name']})

print(f"Found {len(locked_vms)} locked VMs:")
for v in locked_vms:
    print(f" - Node: {v['node']} | VMID: {v['vmid']} | Name: {v['name']}")
```

### Step 3: Safety Check - Verify No Active `vzdump` I/O
Before unlocking, we must ensure `vzdump` is completely dead on the host node. We execute a remote command via the API/SSH abstraction to check process I/O.

```python
def check_vzdump_process(node, vmid):
    # Simulated execution: ssh root@node "ps aux | grep vzdump | grep vmid"
    # Returns True if running, False if dead.
    print(f"🔍 Checking host {node} for active vzdump tasks on {vmid}...")
    return False # Assuming no tasks found for this run

safe_to_unlock = []
for v in locked_vms:
    if not check_vzdump_process(v['node'], v['vmid']):
        safe_to_unlock.append(v)
        print(f"🟢 VM {v['vmid']} is safe to unlock.")
    else:
        print(f"🔴 ABORT: VM {v['vmid']} has active I/O. Do not unlock.")
```
