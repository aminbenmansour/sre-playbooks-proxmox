import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium", app_title="Remediate HA Fencing Loop")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # Runbook: Remediate HA Fencing Loop on PVE Cluster

        **Severity:** P1 / P2 · **SRE Owner:** Infrastructure Pod

        > ⚠️ **WARNING:** Do NOT disable HA fencing globally to stop a loop.
        > Fencing exists to protect data integrity during split-brain scenarios.
        > Follow each step in order and validate quorum before any intervention.
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
    import time

    repo_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    from library.pve_auth import get_proxmox_client

    try:
        proxmox = get_proxmox_client()
        _status = "✅ Connected successfully."
    except ValueError as e:
        proxmox = None
        _status = f"❌ Auth failed: {e}"

    print(_status)
    return os, proxmox, sys, time


@app.cell
def _(mo):
    mo.md("## Step 2: Configure observation window")
    return


@app.cell
def _(mo, time):
    window_slider = mo.ui.slider(
        start=15,
        stop=240,
        step=15,
        value=60,
        label="Observation window (minutes)",
    )
    mo.md(
        f"""
        How far back should the fencing loop detector look?

        {window_slider}
        """
    )
    return (window_slider,)


@app.cell
def _(mo):
    mo.md("## Step 3: Detect fencing loop")
    return


@app.cell
def _(mo, proxmox, time, window_slider):
    from library.pve_ha import detect_ha_fencing_loop

    report = None
    query_node = None

    if proxmox:
        try:
            nodes = proxmox.nodes.get()
            query_node = nodes[0]["node"]
        except Exception as e:
            mo.callout(mo.md(f"❌ Could not retrieve node list: {e}"), kind="danger")

    since_epoch = int(time.time()) - (window_slider.value * 60)

    if proxmox and query_node:
        report = detect_ha_fencing_loop(
            proxmox, node=query_node, since_epoch=since_epoch
        )

    if report is None:
        mo.callout(mo.md("⚠️ No report generated — check authentication."), kind="warn")
    elif report.is_safe:
        mo.callout(
            mo.md(
                f"✅ No fencing loop detected in the last **{window_slider.value} minutes**."
                " Cluster appears healthy."
            ),
            kind="success",
        )
    else:
        rows = []
        for _node, _events in report.events_by_node.items():
            if _node in report.looping_nodes:
                for _ev in _events:
                    rows.append(
                        {
                            "fenced_node": _node,
                            "fence_count": len(_events),
                            "upid": _ev.upid,
                            "epoch": _ev.start_time,
                        }
                    )
        mo.ui.table(
            rows,
            label=f"🔴 Fencing loop detected on: {', '.join(report.looping_nodes)}",
        )
    return detect_ha_fencing_loop, query_node, report, since_epoch


@app.cell
def _(mo):
    mo.md("## Step 4: Verify cluster quorum")
    return


@app.cell
def _(mo, proxmox):
    quorum_ok = False
    quorum_detail = {}

    if proxmox:
        try:
            cluster_status = proxmox.cluster.status.get()
            for item in cluster_status:
                if item.get("type") == "cluster":
                    quorum_ok = item.get("quorate", 0) == 1
                    quorum_detail = {
                        "cluster_name": item.get("name", "N/A"),
                        "nodes_visible": item.get("nodes", "?"),
                        "quorum": "✅ OK" if quorum_ok else "🔴 LOST",
                    }
                    break
        except Exception as e:
            quorum_detail = {"error": str(e)}

    if not quorum_ok and proxmox:
        mo.callout(
            mo.md(
                "🚨 **Cluster has lost quorum.** Do NOT proceed with automated "
                "remediation. Escalate to a senior SRE and refer to the "
                "split-brain runbook."
            ),
            kind="danger",
        )
    elif quorum_ok:
        mo.ui.table(
            [quorum_detail],
            label="Cluster quorum status",
        )
    else:
        mo.md("_Connect to the cluster in Step 1 to check quorum._")
    return quorum_detail, quorum_ok


@app.cell
def _(mo):
    mo.md("## Step 5: Inspect fenced nodes")
    return


@app.cell
def _(mo, proxmox, report):
    inspection_rows = []

    if proxmox and report and not report.is_safe:
        for _bad_node in report.looping_nodes:
            row = {"node": _bad_node}
            try:
                node_status = proxmox.nodes(_bad_node).status.get()
                row["reachable"] = "✅ Yes"
                row["cpu_usage"] = f"{node_status.get('cpu', 0):.1%}"
                row["memory_used_gb"] = (
                    f"{node_status.get('memory', {}).get('used', 0) // 1024**3} GB"
                )
                row["kernel"] = node_status.get("kversion", "N/A")
            except Exception as exc:
                row["reachable"] = "🔴 No"
                row["cpu_usage"] = "N/A"
                row["memory_used_gb"] = "N/A"
                row["kernel"] = f"API error: {exc}"
            inspection_rows.append(row)

    if inspection_rows:
        mo.ui.table(inspection_rows, label="Fenced node inspection")
    elif report and report.is_safe:
        mo.md("_No looping nodes to inspect._")
    else:
        mo.md("_Connect to the cluster in Step 1 to inspect nodes._")
    return (inspection_rows,)


@app.cell
def _(mo):
    mo.md("## Step 6: Freeze HA resources on looping nodes")
    return


@app.cell
def _(mo, proxmox, quorum_ok, report):
    ha_resource_rows = []

    if proxmox and report and not report.is_safe and quorum_ok:
        try:
            ha_resources = proxmox.cluster.ha.resources.get()
            for _r in ha_resources:
                ha_resource_rows.append(
                    {
                        "sid": _r.get("sid", ""),
                        "type": _r.get("type", ""),
                        "state": _r.get("state", ""),
                        "node": _r.get("node", "any"),
                    }
                )
        except Exception as e:
            ha_resource_rows = [{"error": str(e)}]

    if ha_resource_rows:
        mo.ui.table(
            ha_resource_rows,
            label="HA resources — review before freezing",
        )
    elif report and report.is_safe:
        mo.md("_No looping nodes — nothing to freeze._")
    elif not quorum_ok:
        mo.callout(
            mo.md("🚨 Quorum lost — do not modify HA resources."),
            kind="danger",
        )
    else:
        mo.md("_Connect to the cluster in Step 1 to list HA resources._")
    return (ha_resource_rows,)


@app.cell
def _(ha_resource_rows, mo, quorum_ok, report):
    freeze_confirm = mo.ui.checkbox(
        label=(
            f"I have reviewed the {len(ha_resource_rows)} HA resource(s) above "
            "and confirm it is safe to freeze them."
        ),
        value=False,
    )

    if report and not report.is_safe and quorum_ok and ha_resource_rows:
        freeze_confirm
    else:
        mo.md("_Freeze confirmation not available — check steps above._")
    return (freeze_confirm,)


@app.cell
def _(freeze_confirm, ha_resource_rows, mo, proxmox):
    freeze_results = []

    if freeze_confirm.value and proxmox:
        for _r in ha_resource_rows:
            sid = _r.get("sid", "")
            if not sid:
                continue
            try:
                # Uncomment to perform the actual freeze:
                # proxmox.cluster.ha.resources(sid).put(state="stopped")
                freeze_results.append({"sid": sid, "result": "✅ Frozen (dry run)"})
            except Exception as e:
                freeze_results.append({"sid": sid, "result": f"❌ Failed: {e}"})

    if not freeze_confirm.value:
        mo.callout(
            mo.md("Check the confirmation box above to freeze HA resources."),
            kind="warn",
        )
    elif freeze_results:
        mo.ui.table(freeze_results, label="Freeze results")
    else:
        mo.md("_No resources were frozen._")
    return (freeze_results,)


@app.cell
def _(mo):
    mo.md("## Step 7: Isolate looping nodes (maintenance mode)")
    return


@app.cell
def _(mo, proxmox, quorum_ok, report):
    isolate_confirm = mo.ui.checkbox(
        label=(
            "I confirm HA resources are frozen and it is safe to place "
            f"{report.looping_nodes if report else []} into maintenance mode."
        ),
        value=False,
    )

    if proxmox and report and not report.is_safe and quorum_ok:
        isolate_confirm
    else:
        mo.md("_Isolation not available — check steps above._")
    return (isolate_confirm,)


@app.cell
def _(isolate_confirm, mo, proxmox, report):
    isolate_results = []

    if isolate_confirm.value and proxmox and report:
        for _bad_node in report.looping_nodes:
            try:
                # Uncomment to perform the actual isolation:
                # proxmox.nodes(_bad_node).config.put(maintenance=1)
                isolate_results.append(
                    {"node": _bad_node, "result": "✅ Maintenance mode set (dry run)"}
                )
            except Exception as e:
                isolate_results.append({"node": _bad_node, "result": f"❌ Failed: {e}"})

    if not isolate_confirm.value:
        mo.callout(
            mo.md("Check the confirmation box above to isolate nodes."),
            kind="warn",
        )
    elif isolate_results:
        mo.ui.table(isolate_results, label="Isolation results")
    else:
        mo.md("_No nodes were isolated._")
    return (isolate_results,)


@app.cell
def _(mo):
    mo.md("## Step 8: Validate cluster stability")
    return


@app.cell
def _(detect_ha_fencing_loop, mo, proxmox, query_node, time, window_slider):
    recheck_button = mo.ui.button(label="🔄 Re-run fencing loop detector")
    recheck_button
    return (recheck_button,)


@app.cell
def _(
    detect_ha_fencing_loop, mo, proxmox, query_node, recheck_button, time, window_slider
):
    # Depend on recheck_button.value so this cell re-runs on each click
    _ = recheck_button.value

    recheck_report = None

    if proxmox and query_node:
        # Use a tighter 5-minute window for the post-remediation check
        recheck_since = int(time.time()) - 300
        recheck_report = detect_ha_fencing_loop(
            proxmox, node=query_node, since_epoch=recheck_since
        )

    if recheck_report is None:
        mo.md("_Click the button above to re-check._")
    elif recheck_report.is_safe:
        mo.callout(
            mo.md(
                "✅ **Fencing loop resolved.** No fence events in the last 5 minutes. "
                "Cluster is stable. You may remove the affected node from maintenance "
                "once the hardware root cause is confirmed."
            ),
            kind="success",
        )
    else:
        mo.callout(
            mo.md(
                f"🔴 **Loop persists** on: `{', '.join(recheck_report.looping_nodes)}`. "
                "Do not re-enable HA on the affected node. Escalate to the hardware team."
            ),
            kind="danger",
        )
    return recheck_report, recheck_since
