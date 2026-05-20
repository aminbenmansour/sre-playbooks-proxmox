import pytest


@pytest.fixture
def mock_pve_client(mocker):
    """
    Provides a mock ProxmoxAPI client that mimics the chained method calls:
    client.nodes(node).tasks.get()
    """
    mock_client = mocker.MagicMock()
    # Mock the chain: client.nodes -> nodes() -> tasks -> get()
    mock_nodes_method = mocker.MagicMock()
    mock_tasks_property = mocker.MagicMock()
    mock_get_method = mocker.MagicMock()

    mock_client.nodes.return_value = mock_nodes_method
    mock_nodes_method.tasks = mock_tasks_property
    mock_tasks_property.get = mock_get_method

    # Return both the base client mock and the leaf 'get' mock for easy assertions
    return mock_client, mock_get_method
