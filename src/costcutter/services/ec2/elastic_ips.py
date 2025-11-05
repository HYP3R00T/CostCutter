"""Handler for releasing Elastic IP addresses."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from boto3.session import Session
from botocore.exceptions import ClientError

from costcutter.reporter import get_reporter
from costcutter.services.ec2.common import _get_account_id

SERVICE: str = "ec2"
RESOURCE: str = "elastic_ip"
logger = logging.getLogger(__name__)


def catalog_elastic_ips(session: Session, region: str) -> list[dict[str, Any]]:
    """
    List all Elastic IP addresses in a region.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.

    Returns:
        List of Elastic IP address details (allocation_id, public_ip, association_id).
    """
    client = session.client(service_name="ec2", region_name=region)

    addresses: list[dict[str, Any]] = []
    try:
        response = client.describe_addresses()
        all_addresses = response.get("Addresses", [])
        # Filter VPC EIPs (have AllocationId)
        for addr in all_addresses:
            allocation_id = addr.get("AllocationId")
            if allocation_id:
                addresses.append({
                    "allocation_id": allocation_id,
                    "public_ip": addr.get("PublicIp", "N/A"),
                    "association_id": addr.get("AssociationId"),
                })
        logger.info("[%s][ec2][elastic_ip] Found %d Elastic IPs", region, len(addresses))
    except ClientError as e:
        logger.error("[%s][ec2][elastic_ip] Failed to describe addresses: %s", region, e)
        addresses = []
    return addresses


def cleanup_elastic_ip(session: Session, region: str, eip_info: dict[str, Any], dry_run: bool = True) -> None:
    """
    Release a single Elastic IP address.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.
        eip_info: Dictionary with allocation_id, public_ip, association_id.
        dry_run: If True, simulate release without making changes.
    """
    reporter = get_reporter()
    action = "catalog" if dry_run else "delete"
    status = "discovered" if dry_run else "executing"
    account = _get_account_id(session)
    allocation_id = eip_info["allocation_id"]
    public_ip = eip_info["public_ip"]
    association_id = eip_info.get("association_id")

    # Construct proper ARN for the elastic IP resource
    arn = f"arn:aws:ec2:{region}:{account}:elastic-ip/{allocation_id}"

    # Add extra info about association status
    association_status = "associated" if association_id else "unassociated (BILLING)"
    meta = {"status": status, "dry_run": dry_run, "public_ip": public_ip, "association_status": association_status}

    reporter.record(
        region,
        SERVICE,
        RESOURCE,
        action,
        arn=arn,
        meta=meta,
    )
    client = session.client("ec2", region_name=region)
    try:
        # If associated, disassociate first
        if association_id and not dry_run:
            try:
                client.disassociate_address(AssociationId=association_id, DryRun=dry_run)
                logger.info(
                    "[%s][ec2][elastic_ip] Disassociated allocation_id=%s association_id=%s",
                    region,
                    allocation_id,
                    association_id,
                )
            except ClientError as e:
                code = e.response.get("Error", {}).get("Code") if hasattr(e, "response") else None
                if code != "DryRunOperation":
                    logger.error(
                        "[%s][ec2][elastic_ip] disassociate failed allocation_id=%s error=%s",
                        region,
                        allocation_id,
                        e,
                    )
                    return

        # Release the allocation
        client.release_address(AllocationId=allocation_id, DryRun=dry_run)
        if not dry_run:
            logger.info(
                "[%s][ec2][elastic_ip] Released allocation_id=%s public_ip=%s", region, allocation_id, public_ip
            )
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code") if hasattr(e, "response") else None
        if dry_run and code == "DryRunOperation":
            logger.info("[%s][ec2][elastic_ip] dry-run release would succeed allocation_id=%s", region, allocation_id)
        else:
            logger.error("[%s][ec2][elastic_ip] release failed allocation_id=%s error=%s", region, allocation_id, e)


def cleanup_elastic_ips(session: Session, region: str, dry_run: bool = True, max_workers: int = 1) -> None:
    """
    Release all Elastic IP addresses in a region.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.
        dry_run: If True, simulate release without making changes.
        max_workers: Number of threads for parallel execution.
    """
    addresses: list = catalog_elastic_ips(session=session, region=region)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(cleanup_elastic_ip, session, region, eip_info, dry_run) for eip_info in addresses]
        for fut in as_completed(futures):
            fut.result()
