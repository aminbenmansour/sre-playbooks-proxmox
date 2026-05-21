import pytest

from library.pve_safety import is_vzdump_active


def test_is_vzdump_active_true_when_running(mock_pve_client):
    """Should return True if an active vzdump task matches the VM ID."""
    client, mock_get = mock_pve_client

    # Arrange: Simulate Proxmox API returning an active backup task for VM 101
    mock_get.return_value = [
        {
            "status": "running",
            "type": "vzdump",
            "id": "101",
            "upid": "UPID:pve1:00001234:00ABCDEF:65E00000:vzdump:101:sre@pam:",
        },
        {"status": "stopped", "type": "qemu-migrate", "id": "102"},
    ]

    # Act
    result = is_vzdump_active(client, node="pve1", vmid=101)

    # Assert
    assert result is True
    client.nodes.assert_called_once_with("pve1")


def test_is_vzdump_active_false_when_no_matching_tasks(mock_pve_client):
    """Should return False if backup tasks exist but are stopped or for other VMs."""
    client, mock_get = mock_pve_client

    # Arrange: Tasks exist but don't match criteria (wrong status or wrong VM)
    mock_get.return_value = [
        {"status": "stopped", "type": "vzdump", "id": "101"},  # Not running
        {"status": "running", "type": "vzdump", "id": "999"},  # Different VM ID
        {"status": "running", "type": "aptupdate", "id": "101"},  # Wrong task type
    ]

    # Act
    result = is_vzdump_active(client, node="pve1", vmid=101)

    # Assert
    assert result is False


def test_is_vzdump_active_fail_safe_on_exception(mock_pve_client):
    """Should return True (fail-safe) if the API call throws an exception."""
    client, mock_get = mock_pve_client

    # Arrange: API endpoint blows up (network issue, auth expiration, etc.)
    mock_get.side_effect = Exception("API Connection Timeout")

    # Act
    result = is_vzdump_active(client, node="pve1", vmid=101)

    # Assert
    # The code relies on a fail-safe paradigm: error out implies "assume dangerous"
    assert result is True
