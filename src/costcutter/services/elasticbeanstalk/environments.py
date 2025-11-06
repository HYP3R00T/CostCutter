import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from boto3.session import Session
from botocore.exceptions import ClientError

from costcutter.reporter import get_reporter
from costcutter.services.common import _get_account_id

SERVICE: str = "elasticbeanstalk"
RESOURCE: str = "environment"
logger = logging.getLogger(__name__)


def catalog_environments(session: Session, region: str) -> list[str]:
    client = session.client(service_name="elasticbeanstalk", region_name=region)

    environment_names: list[str] = []
    try:
        # Use paginator for large result sets
        paginator = client.get_paginator("describe_environments")

        for page in paginator.paginate(IncludeDeleted=False):
            environments = page.get("Environments", [])
            environment_names.extend([env.get("EnvironmentName") for env in environments])

        logger.info("[%s][elasticbeanstalk][environment] Found %d environments", region, len(environment_names))
    except ClientError as e:
        logger.error("[%s][elasticbeanstalk][environment] Failed to describe environments: %s", region, e)
        environment_names = []

    return environment_names


def cleanup_environment(session: Session, region: str, environment_name: str, dry_run: bool = True) -> None:
    reporter = get_reporter()
    action = "catalog" if dry_run else "delete"
    status = "discovered" if dry_run else "executing"
    account = _get_account_id(session)

    # Construct proper ARN for the environment resource
    arn = f"arn:aws:elasticbeanstalk:{region}:{account}:environment/{environment_name}"

    reporter.record(
        region,
        SERVICE,
        RESOURCE,
        action,
        arn=arn,
        meta={"status": status, "dry_run": dry_run},
    )

    if dry_run:
        logger.info(
            "[%s][elasticbeanstalk][environment] dry-run would terminate environment_name=%s",
            region,
            environment_name,
        )
        return

    client = session.client("elasticbeanstalk", region_name=region)

    try:
        # Terminate the environment (does not delete immediately, but marks for termination)
        client.terminate_environment(
            EnvironmentName=environment_name,
            ForceTerminate=True,
        )
        logger.info(
            "[%s][elasticbeanstalk][environment] terminate requested environment_name=%s",
            region,
            environment_name,
        )

        # Update reporter with success status
        reporter.record(
            region,
            SERVICE,
            RESOURCE,
            "delete",
            arn=arn,
            meta={"status": "terminated", "dry_run": False},
        )

    except ClientError as e:
        logger.error(
            "[%s][elasticbeanstalk][environment] terminate failed environment_name=%s error=%s",
            region,
            environment_name,
            e,
        )
        reporter.record(
            region,
            SERVICE,
            RESOURCE,
            "delete",
            arn=arn,
            meta={"status": "failed", "dry_run": False, "error": str(e)},
        )


def cleanup_environments(session: Session, region: str, dry_run: bool = True, max_workers: int = 1) -> None:
    environment_names: list[str] = catalog_environments(session=session, region=region)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(cleanup_environment, session, region, env_name, dry_run) for env_name in environment_names]
        for fut in as_completed(futures):
            fut.result()
