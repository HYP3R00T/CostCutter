"""Tests for EC2 Volumes handler."""

from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from costcutter.services.ec2.volumes import catalog_volumes, cleanup_volume, cleanup_volumes


def test_catalog_volumes() -> None:
    """Test cataloging EBS volumes."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.describe_volumes.return_value = {
        "Volumes": [
            {"VolumeId": "vol-123"},
            {"VolumeId": "vol-456"},
        ]
    }

    result = catalog_volumes(mock_session, "us-east-1")

    assert result == ["vol-123", "vol-456"]
    mock_client.describe_volumes.assert_called_once_with(Filters=[{"Name": "status", "Values": ["available"]}])


def test_catalog_volumes_client_error() -> None:
    """Test catalog handles ClientError."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.describe_volumes.side_effect = ClientError(
        {"Error": {"Code": "UnauthorizedOperation"}}, "DescribeVolumes"
    )

    result = catalog_volumes(mock_session, "us-east-1")

    assert result == []


def test_cleanup_volume_dry_run() -> None:
    """Test dry-run cleanup of volume."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    cleanup_volume(mock_session, "us-east-1", "vol-123", dry_run=True)

    mock_client.delete_volume.assert_called_once_with(VolumeId="vol-123", DryRun=True)


def test_cleanup_volume_actual() -> None:
    """Test actual cleanup of volume."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    cleanup_volume(mock_session, "us-east-1", "vol-123", dry_run=False)

    mock_client.delete_volume.assert_called_once_with(VolumeId="vol-123", DryRun=False)


def test_cleanup_volume_fails() -> None:
    """Test cleanup when deletion fails."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.delete_volume.side_effect = ClientError({"Error": {"Code": "InvalidVolume.NotFound"}}, "DeleteVolume")

    cleanup_volume(mock_session, "us-east-1", "vol-123", dry_run=False)

    mock_client.delete_volume.assert_called_once()


def test_cleanup_volumes() -> None:
    """Test cleanup of multiple volumes."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.describe_volumes.return_value = {
        "Volumes": [
            {"VolumeId": "vol-123"},
            {"VolumeId": "vol-456"},
        ]
    }

    cleanup_volumes(mock_session, "us-east-1", dry_run=True, max_workers=2)

    assert mock_client.delete_volume.call_count == 2
