import logging
from dataclasses import dataclass, field

from proxmoxer import ProxmoxAPI

logger = logging.getLogger(__name__)

# A node that has been fenced more than this many times within the observation
# window is considered to be in a fencing loop.
FENCING_LOOP_THRESHOLD = 3


@dataclass
class FencingEvent:
    node: str
    upid: str
    start_time: int  # Unix epoch from Proxmox task record


@dataclass
class FencingLoopReport:
    """Aggregated result returned by detect_ha_fencing_loop."""

    looping_nodes: list[str] = field(default_factory=list)
    events_by_node: dict[str, list[FencingEvent]] = field(default_factory=dict)

    @property
    def is_safe(self) -> bool:
        """True only when no node is stuck in a fencing loop."""
        return len(self.looping_nodes) == 0


def _extract_fencing_tasks(tasks: list[dict]) -> list[FencingEvent]:
    """
    Filter a raw Proxmox task list down to completed HA fence operations.

    Proxmox records fence events as tasks with type ``hamanager`` and an id
    field that contains the substring ``fence``.  We intentionally include
    *stopped* tasks here (not just running ones) because a loop is identified
    by rapid repeated completions, not a single in-flight fence.
    """
    events: list[FencingEvent] = []
    for task in tasks:
        task_type = task.get("type", "")
        task_id = task.get("id", "")
        status = task.get("status", "")

        if task_type == "hamanager" and "fence" in task_id and status != "running":
            events.append(
                FencingEvent(
                    node=task.get("node", "unknown"),
                    upid=task.get("upid", ""),
                    start_time=int(task.get("starttime", 0)),
                )
            )
    return events


def detect_ha_fencing_loop(
    proxmox_client: ProxmoxAPI,
    node: str,
    since_epoch: int,
    threshold: int = FENCING_LOOP_THRESHOLD,
) -> FencingLoopReport:
    """
    Return a FencingLoopReport describing whether any cluster node has been
    fenced more than *threshold* times since *since_epoch*.

    Parameters
    ----------
    proxmox_client:
        Authenticated ProxmoxAPI instance.
    node:
        The PVE node whose task log is queried (cluster-wide task history is
        accessible from any node).
    since_epoch:
        Lower-bound Unix timestamp.  Only fence events at or after this time
        are counted.  Callers typically pass ``int(time.time()) - 3600`` for
        a one-hour observation window.
    threshold:
        Number of fence events that triggers a loop classification.
        Defaults to FENCING_LOOP_THRESHOLD (3).

    Fail-safe behaviour
    -------------------
    If the API call fails for any reason, the function returns a report that
    marks the situation as unsafe (``is_safe == False``) and logs the error,
    consistent with the fail-safe paradigm used throughout this library.
    """
    report = FencingLoopReport()

    try:
        tasks = proxmox_client.nodes(node).tasks.get()
    except Exception as exc:
        logger.error(
            "Failed to retrieve task list from node %s: %s — assuming unsafe.",
            node,
            exc,
        )
        # Fail safe: treat as if a loop is active so callers block remediation.
        report.looping_nodes.append("UNKNOWN")
        return report

    fence_events = _extract_fencing_tasks(tasks)

    # Group events per fenced node, filtering to the observation window.
    events_by_node: dict[str, list[FencingEvent]] = {}
    for event in fence_events:
        if event.start_time >= since_epoch:
            events_by_node.setdefault(event.node, []).append(event)

    report.events_by_node = events_by_node

    for fenced_node, node_events in events_by_node.items():
        count = len(node_events)
        if count >= threshold:
            logger.warning(
                "Fencing loop detected: node %s has been fenced %d time(s) "
                "since epoch %d (threshold: %d). UPIDs: %s",
                fenced_node,
                count,
                since_epoch,
                threshold,
                [e.upid for e in node_events],
            )
            report.looping_nodes.append(fenced_node)

    return report
