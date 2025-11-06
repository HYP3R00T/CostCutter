"""Handler for deleting EBS snapshots."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from boto3.session import Session
from botocore.exceptions import ClientError

from costcutter.reporter import get_reporter
from costcutter.services.common import _get_account_id

SERVICE: str = "ec2"
RESOURCE: str = "snapshot"
logger = logging.getLogger(__name__)


def catalog_snapshots(session: Session, region: str) -> list[str]:
    """
    List all EBS snapshots owned by the account in a region.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.

    Returns:
        List of snapshot IDs.
    """
    client = session.client(service_name="ec2", region_name=region)

    snapshot_ids: list[str] = []
    try:
        # Only get snapshots owned by this account
        response = client.describe_snapshots(OwnerIds=["self"])
        snapshots = response.get("Snapshots", [])
        snapshot_ids = [snap.get("SnapshotId") for snap in snapshots if snap.get("SnapshotId")]
        logger.info("[%s][ec2][snapshot] Found %d snapshots", region, len(snapshot_ids))
    except ClientError as e:
        logger.error("[%s][ec2][snapshot] Failed to describe snapshots: %s", region, e)
        snapshot_ids = []
    return snapshot_ids


def cleanup_snapshot(session: Session, region: str, snapshot_id: Any, dry_run: bool = True) -> None:
    """
    Delete a single EBS snapshot.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.
        snapshot_id: Snapshot ID to delete.
        dry_run: If True, simulate deletion without making changes.
    """
    reporter = get_reporter()
    action = "catalog" if dry_run else "delete"
    status = "discovered" if dry_run else "executing"
    account = _get_account_id(session)
    # Construct proper ARN for the snapshot resource
    arn = f"arn:aws:ec2:{region}:{account}:snapshot/{snapshot_id}"
    reporter.record(
        region,
        SERVICE,
        RESOURCE,
        action,
        arn=arn,
        meta={"status": status, "dry_run": dry_run},
    )
    client = session.client("ec2", region_name=region)
    try:
        client.delete_snapshot(SnapshotId=snapshot_id, DryRun=dry_run)
        if not dry_run:
            logger.info("[%s][ec2][snapshot] Deleted snapshot_id=%s", region, snapshot_id)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code") if hasattr(e, "response") else None
        if dry_run and code == "DryRunOperation":
            logger.info("[%s][ec2][snapshot] dry-run delete would succeed snapshot_id=%s", region, snapshot_id)
        else:
            logger.error("[%s][ec2][snapshot] delete failed snapshot_id=%s error=%s", region, snapshot_id, e)


def cleanup_snapshots(session: Session, region: str, dry_run: bool = True, max_workers: int = 1) -> None:
    """
    Delete all EBS snapshots owned by the account in a region.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.
        dry_run: If True, simulate deletion without making changes.
        max_workers: Number of threads for parallel execution.
    """
    snapshot_ids: list = catalog_snapshots(session=session, region=region)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(cleanup_snapshot, session, region, snap_id, dry_run) for snap_id in snapshot_ids]
        for fut in as_completed(futures):
            fut.result()
