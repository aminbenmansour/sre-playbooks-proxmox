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
