"""Handler for deleting EBS volumes."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from boto3.session import Session
from botocore.exceptions import ClientError

from costcutter.reporter import get_reporter
from costcutter.services.common import _get_account_id

SERVICE: str = "ec2"
RESOURCE: str = "volume"
logger = logging.getLogger(__name__)


def catalog_volumes(session: Session, region: str) -> list[str]:
    """
    List all available (unattached) EBS volumes in a region.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.

    Returns:
        List of volume IDs.
    """
    client = session.client(service_name="ec2", region_name=region)

    volume_ids: list[str] = []
    try:
        response = client.describe_volumes(Filters=[{"Name": "status", "Values": ["available"]}])
        volumes = response.get("Volumes", [])
        volume_ids = [vol.get("VolumeId") for vol in volumes if vol.get("VolumeId")]
        logger.info("[%s][ec2][volume] Found %d available volumes", region, len(volume_ids))
    except ClientError as e:
        logger.error("[%s][ec2][volume] Failed to describe volumes: %s", region, e)
        volume_ids = []
    return volume_ids


def cleanup_volume(session: Session, region: str, volume_id: Any, dry_run: bool = True) -> None:
    """
    Delete a single EBS volume.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.
        volume_id: Volume ID to delete.
        dry_run: If True, simulate deletion without making changes.
    """
    reporter = get_reporter()
    action = "catalog" if dry_run else "delete"
    status = "discovered" if dry_run else "executing"
    account = _get_account_id(session)
    # Construct proper ARN for the volume resource
    arn = f"arn:aws:ec2:{region}:{account}:volume/{volume_id}"
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
        client.delete_volume(VolumeId=volume_id, DryRun=dry_run)
        if not dry_run:
            logger.info("[%s][ec2][volume] Deleted volume_id=%s", region, volume_id)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code") if hasattr(e, "response") else None
        if dry_run and code == "DryRunOperation":
            logger.info("[%s][ec2][volume] dry-run delete would succeed volume_id=%s", region, volume_id)
        else:
            logger.error("[%s][ec2][volume] delete failed volume_id=%s error=%s", region, volume_id, e)


def cleanup_volumes(session: Session, region: str, dry_run: bool = True, max_workers: int = 1) -> None:
    """
    Delete all available (unattached) EBS volumes in a region.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.
        dry_run: If True, simulate deletion without making changes.
        max_workers: Number of threads for parallel execution.
    """
    volume_ids: list = catalog_volumes(session=session, region=region)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(cleanup_volume, session, region, vol_id, dry_run) for vol_id in volume_ids]
        for fut in as_completed(futures):
            fut.result()
