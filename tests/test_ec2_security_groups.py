"""Tests for EC2 Security Groups handler."""

from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from costcutter.services.ec2.security_groups import (
    catalog_security_groups,
    cleanup_security_group,
    cleanup_security_groups,
)


def test_catalog_security_groups() -> None:
    """Test cataloging security groups."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.describe_security_groups.return_value = {
        "SecurityGroups": [
            {"GroupId": "sg-123", "GroupName": "custom-sg"},
            {"GroupId": "sg-456", "GroupName": "default"},  # Should be filtered out
            {"GroupId": "sg-789", "GroupName": "another-sg"},
        ]
    }

    result = catalog_security_groups(mock_session, "us-east-1")

    assert result == ["sg-123", "sg-789"]


def test_catalog_security_groups_client_error() -> None:
    """Test catalog handles ClientError."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.describe_security_groups.side_effect = ClientError(
        {"Error": {"Code": "UnauthorizedOperation"}}, "DescribeSecurityGroups"
    )

    result = catalog_security_groups(mock_session, "us-east-1")

    assert result == []


def test_cleanup_security_group_dry_run() -> None:
    """Test dry-run cleanup of security group."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    cleanup_security_group(mock_session, "us-east-1", "sg-123", dry_run=True)

    mock_client.delete_security_group.assert_called_once_with(GroupId="sg-123", DryRun=True)


def test_cleanup_security_group_actual() -> None:
    """Test actual cleanup of security group."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    cleanup_security_group(mock_session, "us-east-1", "sg-123", dry_run=False)

    mock_client.delete_security_group.assert_called_once_with(GroupId="sg-123", DryRun=False)


def test_cleanup_security_group_fails() -> None:
    """Test cleanup when deletion fails."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.delete_security_group.side_effect = ClientError(
        {"Error": {"Code": "DependencyViolation"}}, "DeleteSecurityGroup"
    )

    cleanup_security_group(mock_session, "us-east-1", "sg-123", dry_run=False)

    mock_client.delete_security_group.assert_called_once()


def test_cleanup_security_groups() -> None:
    """Test cleanup of multiple security groups."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.describe_security_groups.return_value = {
        "SecurityGroups": [
            {"GroupId": "sg-123", "GroupName": "custom-sg"},
            {"GroupId": "sg-789", "GroupName": "another-sg"},
        ]
    }

    cleanup_security_groups(mock_session, "us-east-1", dry_run=True, max_workers=2)

    assert mock_client.delete_security_group.call_count == 2
