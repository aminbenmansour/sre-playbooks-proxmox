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
