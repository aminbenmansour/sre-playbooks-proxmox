import logging
from proxmoxer import ProxmoxAPI

logger = logging.getLogger(__name__)


def is_vzdump_active(
    proxmox_client: ProxmoxAPI,
    node: str,
    vmid: int | str,
) -> bool:
    """
    Return True if a vzdump backup task is currently running for the given VM.
    """
    try:
        tasks = proxmox_client.nodes(node).tasks.get()

        for task in tasks:
            if (
                task.get("status") == "running"
                and task.get("type") == "vzdump"
                and str(vmid) in task.get("id", "")
            ):
                logger.warning(
                    "Active vzdump task found for VM %s on node %s (Task UPID: %s)",
                    vmid,
                    node,
                    task.get("upid"),
                )
                return True

        return False

    except Exception as exc:
        logger.error("Failed to query tasks on node %s: %s", node, exc)
        # Fail safe: if the query fails, assume a backup may be running.
        return True
        