import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium", app_title="Unlock PVE VMs")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # Runbook: Remediate `locked: backup` State on PVE VMs

        **Severity:** P2 / P3 · **SRE Owner:** Infrastructure Pod

        > ⚠️ **WARNING:** Never unlock a VM if `vzdump` is actively writing blocks.
        > Doing so during an active snapshot commit can cause severe data corruption.
        """
    )
    return


@app.cell
def _(mo):
    mo.md("## Step 1: Authenticate to the cluster")
    return


@app.cell
def _():
    import os
    import sys

    sys.path.insert(0, os.path.abspath("../../"))

    from library.pve_auth import get_proxmox_client

    try:
        proxmox = get_proxmox_client()
        _status = "✅ Connected successfully."
    except ValueError as e:
        proxmox = None
        _status = f"❌ Auth failed: {e}"

    print(_status)
    return os, proxmox, sys


@app.cell
def _(mo):
    mo.md("## Step 2: Identify locked VMs")
    return


@app.cell
def _(mo, proxmox):
    from library.pve_safety import is_vzdump_active

    locked_vms = []

    if proxmox:
        for node in proxmox.nodes.get():
            for vm in proxmox.nodes(node["node"]).qemu.get():
                if vm.get("lock") == "backup":
                    locked_vms.append(
                        {
                            "node": node["node"],
                            "vmid": vm["vmid"],
                            "name": vm.get("name", "unknown"),
                        }
                    )

    if locked_vms:
        table = mo.ui.table(
            locked_vms,
            label=f"Found **{len(locked_vms)}** locked VM(s)",
        )
    else:
        table = mo.callout(
            mo.md("✅ No locked VMs found. Nothing to do."),
            kind="success",
        )

    table
    return is_vzdump_active, locked_vms, table


@app.cell
def _(mo):
    mo.md("## Step 3: Safety check — verify no active `vzdump` I/O")
    return


@app.cell
def _(is_vzdump_active, locked_vms, mo, proxmox):
    safe_to_unlock = []
    blocked = []

    if proxmox:
        for v in locked_vms:
            if is_vzdump_active(proxmox, v["node"], v["vmid"]):
                blocked.append(v)
            else:
                safe_to_unlock.append(v)

    rows = []
    for _v in locked_vms:
        is_blocked = _v in blocked
        rows.append(
            {
                "vmid": _v["vmid"],
                "name": _v["name"],
                "node": _v["node"],
                "status": (
                    "🔴 ABORT — active I/O" if is_blocked else "🟢 Safe to unlock"
                ),
            }
        )

    if rows:
        mo.ui.table(rows, label="Safety check results")
    else:
        mo.md("_No VMs to check._")
    return blocked, rows, safe_to_unlock


@app.cell
def _(mo):
    mo.md("## Step 4: Execute unlock")
    return


@app.cell
def _(mo, safe_to_unlock):
    confirm = mo.ui.checkbox(
        label=f"I confirm it is safe to unlock **{len(safe_to_unlock)}** VM(s). I have reviewed the safety check above.",
        value=False,
    )
    confirm
    return (confirm,)


@app.cell
def _(confirm, mo, proxmox, safe_to_unlock):
    results = []

    if confirm.value and proxmox:
        for _v in safe_to_unlock:
            try:
                # Uncomment the line below to perform the actual unlock:
                # proxmox.nodes(v["node"]).qemu(v["vmid"]).config.post(skiplock=1)
                results.append(
                    {
                        "vmid": _v["vmid"],
                        "name": _v["name"],
                        "result": "✅ Lock cleared (dry run)",
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "vmid": _v["vmid"],
                        "name": _v["name"],
                        "result": f"❌ Failed: {e}",
                    }
                )

    if not confirm.value:
        mo.callout(
            mo.md("Check the confirmation box above to execute the unlock."),
            kind="warn",
        )
    elif results:
        mo.ui.table(results, label="Unlock results")
    else:
        mo.md("_No VMs were unlocked._")
    return (results,)


if __name__ == "__main__":
    app.run()
