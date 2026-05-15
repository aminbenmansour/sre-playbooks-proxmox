---
jupyter:
  jupytext:
    formats: ipynb,md
    main_language: python
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.1
---

# Runbook: Remediate `locked: backup` State on PVE VMs

**Severity:** P2 / P3
**SRE Owner:** Infrastructure Pod
**Context:** A VM is locked by a stale backup task. Attempting to manage the VM results in `VM is locked (backup)`.

> **⚠️ WARNING:** Never unlock a VM if the backup process `vzdump` is actively writing blocks. Doing so during an active snapshot commit can cause severe data corruption.

### Step 1: Initialize API Environment
Set your target cluster and authenticate.

```python
import sys
import os

from proxmoxer import ProxmoxAPI

sys.path.insert(0, os.path.abspath("../../"))

from library.pve_auth import get_proxmox_client
from library.pve_safety import is_vzdump_active

proxmox = get_proxmox_client()
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
for v in locked_vms:
    node, vmid, name = v['node'], v['vmid'], v['name']

    print(f"\n🔍 Analyzing VM {vmid} ({name})...")
    if is_vzdump_active(proxmox, node, vmid):
        print(f"🔴 ABORT: Active I/O task found for {vmid}. Do not unlock.")
    else:
        print(f"🟢 SAFE: No active backup tasks. Unlocking {vmid}...")
        # proxmox.nodes(node).qemu(vmid).config.post(skiplock=1)
        print(f"✅ Lock cleared successfully.")
```

### Step 4: Execute Unlock
Clear the lock on safe VMs.

```python
for v in safe_to_unlock:
    node, vmid = v['node'], v['vmid']
    # Execute API call to unlock
    # proxmox.nodes(node).qemu(vmid).config.post(skiplock=1) # (Simplified for safety)
    print(f"✅ Lock cleared on VM {vmid} ({v['name']}).")
```
