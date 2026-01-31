"""Tests for EC2 Elastic IP handler."""

from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from costcutter.services.ec2.elastic_ips import catalog_elastic_ips, cleanup_elastic_ip, cleanup_elastic_ips


def test_catalog_elastic_ips() -> None:
    """Test cataloging Elastic IPs."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.describe_addresses.return_value = {
        "Addresses": [
            {
                "AllocationId": "eipalloc-123",
                "PublicIp": "1.2.3.4",
                "AssociationId": "eipassoc-abc",
            },
            {
                "AllocationId": "eipalloc-456",
                "PublicIp": "5.6.7.8",
            },
            {
                "PublicIp": "9.10.11.12",  # EC2-Classic EIP without AllocationId
            },
        ]
    }

    result = catalog_elastic_ips(mock_session, "us-east-1")

    assert len(result) == 2
    assert result[0]["allocation_id"] == "eipalloc-123"
    assert result[0]["public_ip"] == "1.2.3.4"
    assert result[0]["association_id"] == "eipassoc-abc"
    assert result[1]["allocation_id"] == "eipalloc-456"
    assert result[1]["public_ip"] == "5.6.7.8"
    assert result[1]["association_id"] is None


def test_catalog_elastic_ips_client_error() -> None:
    """Test catalog handles ClientError."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.describe_addresses.side_effect = ClientError(
        {"Error": {"Code": "UnauthorizedOperation"}}, "DescribeAddresses"
    )

    result = catalog_elastic_ips(mock_session, "us-east-1")

    assert result == []


def test_cleanup_elastic_ip_dry_run() -> None:
    """Test dry-run cleanup of Elastic IP."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    eip_info = {
        "allocation_id": "eipalloc-123",
        "public_ip": "1.2.3.4",
    }

    cleanup_elastic_ip(mock_session, "us-east-1", eip_info, dry_run=True)

    # Should attempt release with DryRun=True
    mock_client.release_address.assert_called_once_with(AllocationId="eipalloc-123", DryRun=True)


def test_cleanup_elastic_ip_associated_dry_run() -> None:
    """Test dry-run cleanup of associated Elastic IP."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    eip_info = {
        "allocation_id": "eipalloc-123",
        "public_ip": "1.2.3.4",
        "association_id": "eipassoc-abc",
    }

    cleanup_elastic_ip(mock_session, "us-east-1", eip_info, dry_run=True)

    # Should attempt release with DryRun=True (disassociation not called in dry-run)
    mock_client.release_address.assert_called_once_with(AllocationId="eipalloc-123", DryRun=True)


def test_cleanup_elastic_ip_actual() -> None:
    """Test actual cleanup of Elastic IP."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    eip_info = {
        "allocation_id": "eipalloc-123",
        "public_ip": "1.2.3.4",
    }

    cleanup_elastic_ip(mock_session, "us-east-1", eip_info, dry_run=False)

    # Should release with DryRun=False
    mock_client.release_address.assert_called_once_with(AllocationId="eipalloc-123", DryRun=False)


def test_cleanup_elastic_ip_associated_actual() -> None:
    """Test actual cleanup of associated Elastic IP."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    eip_info = {
        "allocation_id": "eipalloc-123",
        "public_ip": "1.2.3.4",
        "association_id": "eipassoc-abc",
    }

    cleanup_elastic_ip(mock_session, "us-east-1", eip_info, dry_run=False)

    # Should disassociate first, then release
    mock_client.disassociate_address.assert_called_once_with(AssociationId="eipassoc-abc", DryRun=False)
    mock_client.release_address.assert_called_once_with(AllocationId="eipalloc-123", DryRun=False)


def test_cleanup_elastic_ip_disassociate_fails() -> None:
    """Test cleanup when disassociation fails."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.disassociate_address.side_effect = ClientError(
        {"Error": {"Code": "InvalidAssociationID.NotFound"}}, "DisassociateAddress"
    )

    eip_info = {
        "allocation_id": "eipalloc-123",
        "public_ip": "1.2.3.4",
        "association_id": "eipassoc-abc",
    }

    cleanup_elastic_ip(mock_session, "us-east-1", eip_info, dry_run=False)

    # Should attempt disassociate but not release due to error
    mock_client.disassociate_address.assert_called_once()
    mock_client.release_address.assert_not_called()


def test_cleanup_elastic_ip_release_fails() -> None:
    """Test cleanup when release fails."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.release_address.side_effect = ClientError(
        {"Error": {"Code": "InvalidAllocationID.NotFound"}}, "ReleaseAddress"
    )

    eip_info = {
        "allocation_id": "eipalloc-123",
        "public_ip": "1.2.3.4",
    }

    cleanup_elastic_ip(mock_session, "us-east-1", eip_info, dry_run=False)

    # Should attempt release and handle error
    mock_client.release_address.assert_called_once()


def test_cleanup_elastic_ips() -> None:
    """Test cleanup of multiple Elastic IPs."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.describe_addresses.return_value = {
        "Addresses": [
            {"AllocationId": "eipalloc-123", "PublicIp": "1.2.3.4"},
            {"AllocationId": "eipalloc-456", "PublicIp": "5.6.7.8"},
        ]
    }

    cleanup_elastic_ips(mock_session, "us-east-1", dry_run=True, max_workers=2)

    # Should call release for each EIP
    assert mock_client.release_address.call_count == 2
