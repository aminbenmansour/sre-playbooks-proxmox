import pytest

from library.pve_ha import (
    FENCING_LOOP_THRESHOLD,
    FencingLoopReport,
    detect_ha_fencing_loop,
)

# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

BASE_EPOCH = 1_700_000_000  # Arbitrary fixed "now" for deterministic tests


def _fence_task(node: str, upid_suffix: str, start_offset: int = 0) -> dict:
    """Helper to build a minimal Proxmox hamanager fence task dict."""
    return {
        "type": "hamanager",
        "id": f"fence:{node}",
        "status": "OK",
        "node": node,
        "upid": f"UPID:{node}:000{upid_suffix}:hamanager:fence:{node}:root@pam:",
        "starttime": BASE_EPOCH + start_offset,
    }


# ---------------------------------------------------------------------------
# detect_ha_fencing_loop
# ---------------------------------------------------------------------------


class TestDetectHaFencingLoop:
    def test_returns_safe_when_no_fence_tasks(self, mock_pve_client):
        """No fence tasks → report is safe, looping_nodes is empty."""
        client, mock_get = mock_pve_client
        mock_get.return_value = [
            {
                "type": "vzdump",
                "id": "101",
                "status": "OK",
                "node": "pve1",
                "starttime": BASE_EPOCH,
            },
        ]

        report = detect_ha_fencing_loop(
            client, node="pve1", since_epoch=BASE_EPOCH - 3600
        )

        assert report.is_safe is True
        assert report.looping_nodes == []

    def test_returns_safe_below_threshold(self, mock_pve_client):
        """Fence count below threshold → not classified as a loop."""
        client, mock_get = mock_pve_client
        # Two fence events for the same node — below default threshold of 3
        mock_get.return_value = [
            _fence_task("pve2", "001", start_offset=10),
            _fence_task("pve2", "002", start_offset=20),
        ]

        report = detect_ha_fencing_loop(client, node="pve1", since_epoch=BASE_EPOCH)

        assert report.is_safe is True
        assert "pve2" not in report.looping_nodes

    def test_detects_loop_at_threshold(self, mock_pve_client):
        """Exactly threshold fence events for a node → loop detected."""
        client, mock_get = mock_pve_client
        mock_get.return_value = [
            _fence_task("pve3", f"00{i}", start_offset=i * 60)
            for i in range(FENCING_LOOP_THRESHOLD)
        ]

        report = detect_ha_fencing_loop(client, node="pve1", since_epoch=BASE_EPOCH)

        assert report.is_safe is False
        assert "pve3" in report.looping_nodes

    def test_detects_loop_above_threshold(self, mock_pve_client):
        """More than threshold fence events → loop detected."""
        client, mock_get = mock_pve_client
        mock_get.return_value = [
            _fence_task("pve4", f"0{i:02d}", start_offset=i * 30)
            for i in range(FENCING_LOOP_THRESHOLD + 2)
        ]

        report = detect_ha_fencing_loop(client, node="pve1", since_epoch=BASE_EPOCH)

        assert report.is_safe is False
        assert "pve4" in report.looping_nodes

    def test_events_outside_window_are_ignored(self, mock_pve_client):
        """Fence events older than since_epoch must not be counted."""
        client, mock_get = mock_pve_client
        # All three events happened BEFORE the observation window
        mock_get.return_value = [
            _fence_task("pve5", f"00{i}", start_offset=-(i + 1) * 600)
            for i in range(FENCING_LOOP_THRESHOLD)
        ]

        report = detect_ha_fencing_loop(
            client, node="pve1", since_epoch=BASE_EPOCH  # window starts at BASE_EPOCH
        )

        assert report.is_safe is True
        assert "pve5" not in report.looping_nodes

    def test_multiple_nodes_independent_counts(self, mock_pve_client):
        """Each node's fence count is tracked independently."""
        client, mock_get = mock_pve_client
        # pve6: 3 fences (loop) | pve7: 1 fence (safe)
        mock_get.return_value = [
            _fence_task("pve6", f"A0{i}", start_offset=i * 60)
            for i in range(FENCING_LOOP_THRESHOLD)
        ] + [
            _fence_task("pve7", "B01", start_offset=10),
        ]

        report = detect_ha_fencing_loop(client, node="pve1", since_epoch=BASE_EPOCH)

        assert report.is_safe is False
        assert "pve6" in report.looping_nodes
        assert "pve7" not in report.looping_nodes

    def test_running_fence_tasks_are_excluded(self, mock_pve_client):
        """In-flight fence tasks (status=running) should not be counted toward the loop threshold."""
        client, mock_get = mock_pve_client
        # Manufacture threshold running tasks — they must be ignored
        running_tasks = []
        for i in range(FENCING_LOOP_THRESHOLD):
            t = _fence_task("pve8", f"C0{i}", start_offset=i * 30)
            t["status"] = "running"
            running_tasks.append(t)
        mock_get.return_value = running_tasks

        report = detect_ha_fencing_loop(client, node="pve1", since_epoch=BASE_EPOCH)

        assert report.is_safe is True

    def test_custom_threshold_respected(self, mock_pve_client):
        """Callers can override the threshold for stricter or looser policies."""
        client, mock_get = mock_pve_client
        mock_get.return_value = [
            _fence_task("pve9", f"D0{i}", start_offset=i * 10) for i in range(2)
        ]

        # Default threshold=3 → safe; custom threshold=2 → loop
        report_default = detect_ha_fencing_loop(
            client, node="pve1", since_epoch=BASE_EPOCH, threshold=3
        )
        mock_get.return_value = [
            _fence_task("pve9", f"D0{i}", start_offset=i * 10) for i in range(2)
        ]
        report_strict = detect_ha_fencing_loop(
            client, node="pve1", since_epoch=BASE_EPOCH, threshold=2
        )

        assert report_default.is_safe is True
        assert report_strict.is_safe is False

    def test_fail_safe_on_api_exception(self, mock_pve_client):
        """API failure → report is unsafe (fail-safe), UNKNOWN sentinel in looping_nodes."""
        client, mock_get = mock_pve_client
        mock_get.side_effect = Exception("Connection refused")

        report = detect_ha_fencing_loop(client, node="pve1", since_epoch=BASE_EPOCH)

        assert report.is_safe is False
        assert "UNKNOWN" in report.looping_nodes

    def test_events_by_node_populated_correctly(self, mock_pve_client):
        """events_by_node must contain the right FencingEvent objects."""
        client, mock_get = mock_pve_client
        mock_get.return_value = [
            _fence_task("pveA", "E01", start_offset=5),
            _fence_task("pveA", "E02", start_offset=10),
        ]

        report = detect_ha_fencing_loop(client, node="pve1", since_epoch=BASE_EPOCH)

        assert "pveA" in report.events_by_node
        assert len(report.events_by_node["pveA"]) == 2
        upids = {e.upid for e in report.events_by_node["pveA"]}
        assert any("E01" in u for u in upids)
        assert any("E02" in u for u in upids)
