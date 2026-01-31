"""Tests for EC2 Snapshots handler."""

from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from costcutter.services.ec2.snapshots import catalog_snapshots, cleanup_snapshot, cleanup_snapshots


def test_catalog_snapshots() -> None:
    """Test cataloging EBS snapshots."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.describe_snapshots.return_value = {
        "Snapshots": [
            {"SnapshotId": "snap-123"},
            {"SnapshotId": "snap-456"},
        ]
    }

    result = catalog_snapshots(mock_session, "us-east-1")

    assert result == ["snap-123", "snap-456"]
    mock_client.describe_snapshots.assert_called_once_with(OwnerIds=["self"])


def test_catalog_snapshots_client_error() -> None:
    """Test catalog handles ClientError."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.describe_snapshots.side_effect = ClientError(
        {"Error": {"Code": "UnauthorizedOperation"}}, "DescribeSnapshots"
    )

    result = catalog_snapshots(mock_session, "us-east-1")

    assert result == []


def test_cleanup_snapshot_dry_run() -> None:
    """Test dry-run cleanup of snapshot."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    cleanup_snapshot(mock_session, "us-east-1", "snap-123", dry_run=True)

    mock_client.delete_snapshot.assert_called_once_with(SnapshotId="snap-123", DryRun=True)


def test_cleanup_snapshot_actual() -> None:
    """Test actual cleanup of snapshot."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    cleanup_snapshot(mock_session, "us-east-1", "snap-123", dry_run=False)

    mock_client.delete_snapshot.assert_called_once_with(SnapshotId="snap-123", DryRun=False)


def test_cleanup_snapshot_fails() -> None:
    """Test cleanup when deletion fails."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.delete_snapshot.side_effect = ClientError(
        {"Error": {"Code": "InvalidSnapshot.NotFound"}}, "DeleteSnapshot"
    )

    cleanup_snapshot(mock_session, "us-east-1", "snap-123", dry_run=False)

    mock_client.delete_snapshot.assert_called_once()


def test_cleanup_snapshots() -> None:
    """Test cleanup of multiple snapshots."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.describe_snapshots.return_value = {
        "Snapshots": [
            {"SnapshotId": "snap-123"},
            {"SnapshotId": "snap-456"},
        ]
    }

    cleanup_snapshots(mock_session, "us-east-1", dry_run=True, max_workers=2)

    assert mock_client.delete_snapshot.call_count == 2
