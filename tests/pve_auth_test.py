import os

import pytest

from library.pve_auth import get_proxmox_client


@pytest.fixture
def clean_env(monkeypatch):
    """Ensures a predictable environment for auth tests."""
    vars_to_clear = ["PVE_CLUSTER_ENDPOINT", "PVE_USER", "PVE_TOKEN_NAME", "PVE_TOKEN"]
    for var in vars_to_clear:
        monkeypatch.delenv(var, raising=False)


def test_get_proxmox_client_success(monkeypatch, mocker):
    """Should instantiate ProxmoxAPI when all env vars are present."""
    # Arrange
    monkeypatch.setenv("PVE_CLUSTER_ENDPOINT", "pve.internal.net")
    monkeypatch.setenv("PVE_USER", "sre-api@pam")
    monkeypatch.setenv("PVE_TOKEN_NAME", "runbook-token")
    monkeypatch.setenv("PVE_TOKEN", "super-secret-token")

    mock_proxmox_api = mocker.patch("library.pve_auth.ProxmoxAPI")

    # Act
    client = get_proxmox_client()

    # Assert
    mock_proxmox_api.assert_called_once_with(
        "pve.internal.net",
        user="sre-api@pam",
        token_name="runbook-token",
        token_value="super-secret-token",
        verify_ssl=True,
    )
    assert client == mock_proxmox_api.return_value


@pytest.mark.parametrize(
    "missing_var", ["PVE_CLUSTER_ENDPOINT", "PVE_USER", "PVE_TOKEN_NAME", "PVE_TOKEN"]
)
def test_get_proxmox_client_missing_vars(clean_env, monkeypatch, missing_var, mocker):
    """Should raise ValueError if any required env var is missing."""
    # Arrange
    full_env = {
        "PVE_CLUSTER_ENDPOINT": "pve.internal.net",
        "PVE_USER": "sre-api@pam",
        "PVE_TOKEN_NAME": "runbook-token",
        "PVE_TOKEN": "super-secret-token",
    }
    # Set all except the one we want to test for failure
    for key, val in full_env.items():
        if key != missing_var:
            monkeypatch.setenv(key, val)

    mocker.patch("library.pve_auth.ProxmoxAPI")

    # Act & Assert
    with pytest.raises(ValueError, match="Missing required PVE environment variables"):
        get_proxmox_client()
