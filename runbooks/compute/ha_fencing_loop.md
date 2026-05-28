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

# Runbook: Remediate HA Fencing Loop on PVE Cluster
* **Severity:** P1 / P2
* **SRE Owner:** Infrastructure Pod
* **Context:** A cluster node is being repeatedly fenced by the Proxmox HA Manager within a short window, preventing VMs from achieving quorum and causing continuous failover churn.

> **⚠️ WARNING:** Do NOT disable HA fencing globally to stop a loop. Fencing exists to protect data integrity during split-brain. Follow each step in order and validate quorum state before any intervention.

---

### Step 1: Initialize API Environment
```python
import sys
import os
import time

sys.path.insert(0, os.path.abspath("../../"))

from library.pve_auth import get_proxmox_client
from library.pve_ha import detect_ha_fencing_loop, FENCING_LOOP_THRESHOLD

proxmox = get_proxmox_client()

# Observation window: look back 1 hour
SINCE_EPOCH = int(time.time()) - 3600
print(f"Observation window: last 3600 seconds (since epoch {SINCE_EPOCH})")
```

---

### Step 2: Identify the Affected Node
Query the cluster for current HA resource states and find any node that is
being continuously fenced.

```python
# Pick any reachable node to query cluster-wide task history
query_node = proxmox.nodes.get()[0]["node"]
print(f"Querying task history via node: {query_node}")

report = detect_ha_fencing_loop(proxmox, node=query_node, since_epoch=SINCE_EPOCH)

if report.is_safe:
    print("✅ No fencing loop detected. Cluster appears healthy.")
else:
    print(f"🔴 Fencing loop detected on: {report.looping_nodes}")
    for node, events in report.events_by_node.items():
        if node in report.looping_nodes:
            print(f"\n  Node '{node}' — {len(events)} fence event(s):")
            for ev in events:
                print(f"    UPID: {ev.upid} | epoch: {ev.start_time}")
```

---

### Step 3: Check Cluster Quorum
Before taking any action, confirm the remaining nodes still hold quorum.
Intervening without quorum risks a split-brain scenario.

```python
cluster_status = proxmox.cluster.status.get()

quorum_ok = False
for item in cluster_status:
    if item.get("type") == "cluster":
        quorum_ok = item.get("quorate", 0) == 1
        nodes_total = item.get("nodes", "?")
        print(f"Cluster quorum: {'✅ OK' if quorum_ok else '🔴 LOST'} | Nodes visible: {nodes_total}")
        break

if not quorum_ok:
    raise RuntimeError(
        "🚨 Cluster has lost quorum. Do NOT proceed with automated remediation. "
        "Escalate to a senior SRE and refer to the split-brain runbook."
    )
```

---

### Step 4: Inspect the Fenced Node's Hardware / IPMI Status
A node caught in a fencing loop usually has a hardware-level problem
(IPMI unreachable, NIC flap, storage I/O hang). Use the Proxmox API to
read the node's current reachability and HA state.

```python
if not report.is_safe:
    for bad_node in report.looping_nodes:
        print(f"\n--- Inspecting node: {bad_node} ---")
        try:
            node_status = proxmox.nodes(bad_node).status.get()
            print(f"  Kernel version : {node_status.get('kversion', 'N/A')}")
            print(f"  CPU usage      : {node_status.get('cpu', 'N/A'):.2%}")
            print(f"  Memory used    : {node_status.get('memory', {}).get('used', 0) // 1024**3} GB")
        except Exception as exc:
            print(f"  ⚠️  Cannot reach node {bad_node} via API: {exc}")
            print("  → This is consistent with a fencing loop — node is likely offline.")

        # Check HA manager opinion of this node
        try:
            ha_status = proxmox.cluster.ha.status.manager_status.get()
            print(f"\n  HA Manager status (excerpt): {ha_status}")
        except Exception as exc:
            print(f"  ⚠️  Could not retrieve HA manager status: {exc}")
```

---
### Step 5: Temporarily Migrate or Freeze HA Resources
If the loop is confirmed and quorum is healthy, prevent further churn by
moving HA-managed VMs away from the problematic node and freezing their
HA group membership until the hardware issue is resolved.

```python
if not report.is_safe and quorum_ok:
    ha_resources = proxmox.cluster.ha.resources.get()

    for resource in ha_resources:
        resource_id = resource.get("sid", "")
        current_state = resource.get("state", "")
        print(f"HA resource: {resource_id} | state: {current_state}")

    # To freeze a resource (prevents HA from relocating it again):
    # proxmox.cluster.ha.resources(resource_id).put(state="stopped")
    # Uncomment the line above after verifying resource_id values above.
    print("\n⚠️  Review the resource list above, then uncomment the freeze command.")
```

---

### Step 6: Isolate the Node (Maintenance Mode)
Once resources are safe, place the fencing-loop node into maintenance mode
so HA stops attempting to fence it.

```python
if not report.is_safe and quorum_ok:
    for bad_node in report.looping_nodes:
        print(f"Placing {bad_node} into maintenance mode...")
        # proxmox.nodes(bad_node).config.put(maintenance=1)
        # Uncomment after confirming node identity above.
        print(f"  (Command commented out — verify node identity first.)")
```

---

### Step 7: Validate Cluster Stability
After isolation, re-run the loop detector and confirm the cluster has settled.

```python
import time

print("Waiting 60 seconds for HA manager to stabilise...")
# time.sleep(60)  # Uncomment in live execution

new_report = detect_ha_fencing_loop(proxmox, node=query_node, since_epoch=int(time.time()) - 300)

if new_report.is_safe:
    print("✅ Fencing loop resolved. Cluster is stable.")
else:
    print(f"🔴 Loop persists on: {new_report.looping_nodes}")
    print("Escalate to hardware team. Do not re-enable HA on affected node until root cause is confirmed.")
```
