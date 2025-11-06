import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from boto3.session import Session
from botocore.exceptions import ClientError

from costcutter.reporter import get_reporter
from costcutter.services.common import _get_account_id

SERVICE: str = "ec2"
RESOURCE: str = "security_group"
logger = logging.getLogger(__name__)


def catalog_security_groups(session: Session, region: str) -> list[str]:
    client = session.client(service_name="ec2", region_name=region)

    security_group_ids: list[str] = []
    try:
        security_groups = client.describe_security_groups().get("SecurityGroups", [])
        for security_group in security_groups:
            if security_group.get("GroupName") == "default":
                continue
            group_id = security_group.get("GroupId")
            if group_id:
                security_group_ids.append(group_id)
        logger.info("[%s][ec2][security_group] Found %d security groups", region, len(security_group_ids))
    except ClientError as e:
        logger.error("[%s][ec2][security_group] Failed to describe security groups: %s", region, e)
        security_group_ids = []
    return security_group_ids


def cleanup_security_group(session: Session, region: str, security_group_id: str, dry_run: bool = True) -> None:
    reporter = get_reporter()
    action = "catalog" if dry_run else "delete"
    status = "discovered" if dry_run else "executing"
    account = _get_account_id(session)
    arn = f"arn:aws:ec2:{region}:{account}:security-group/{security_group_id}"
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
        client.delete_security_group(GroupId=security_group_id, DryRun=dry_run)
        logger.info(
            "[%s][ec2][security_group] delete requested group_id=%s dry_run=%s",
            region,
            security_group_id,
            dry_run,
        )
        if not dry_run:
            # Update reporter with success status
            reporter.record(
                region,
                SERVICE,
                RESOURCE,
                "delete",
                arn=arn,
                meta={"status": "deleted", "dry_run": False},
            )
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code") if hasattr(e, "response") else None
        if dry_run and code == "DryRunOperation":
            logger.info(
                "[%s][ec2][security_group] dry-run delete would succeed group_id=%s",
                region,
                security_group_id,
            )
        else:
            logger.error(
                "[%s][ec2][security_group] delete failed group_id=%s error=%s",
                region,
                security_group_id,
                e,
            )
            reporter.record(
                region,
                SERVICE,
                RESOURCE,
                "delete",
                arn=arn,
                meta={"status": "failed", "dry_run": dry_run, "error": str(e)},
            )


def cleanup_security_groups(session: Session, region: str, dry_run: bool = True, max_workers: int = 1) -> None:
    security_group_ids: list[str] = catalog_security_groups(session=session, region=region)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [
            ex.submit(cleanup_security_group, session, region, security_group_id, dry_run)
            for security_group_id in security_group_ids
        ]
        for fut in as_completed(futures):
            fut.result()
