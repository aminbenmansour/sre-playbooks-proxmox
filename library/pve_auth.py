import logging
import os

from proxmoxer import ProxmoxAPI

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def get_proxmox_client():
    """Authenticates to Proxmox API using environment variables."""
    host = os.getenv("PVE_CLUSTER_ENDPOINT")
    user = os.getenv("PVE_USER", "sre-api@pam")
    token_name = os.getenv("PVE_TOKEN_NAME", "runbook-token")
    token_value = os.getenv("PVE_TOKEN")

    if not all([host, user, token_name, token_value]):
        raise ValueError(
            "❌ Missing required PVE environment variables. Check your vault/env."
        )

    logging.info(f"Authenticating to PVE Cluster at {host} as {user}...")
    return ProxmoxAPI(
        host, user=user, token_name=token_name, token_value=token_value, verify_ssl=True
    )
