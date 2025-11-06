import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from boto3.session import Session
from botocore.exceptions import ClientError

from costcutter.reporter import get_reporter
from costcutter.services.common import _get_account_id

SERVICE: str = "elasticbeanstalk"
RESOURCE: str = "application"
logger = logging.getLogger(__name__)


def catalog_applications(session: Session, region: str) -> list[str]:
    client = session.client(service_name="elasticbeanstalk", region_name=region)

    application_names: list[str] = []
    try:
        # Describe applications returns all applications
        response = client.describe_applications()
        applications = response.get("Applications", [])
        application_names = [app.get("ApplicationName") for app in applications]
        logger.info("[%s][elasticbeanstalk][application] Found %d applications", region, len(application_names))
    except ClientError as e:
        logger.error("[%s][elasticbeanstalk][application] Failed to describe applications: %s", region, e)
        application_names = []

    return application_names


def cleanup_application(session: Session, region: str, application_name: str, dry_run: bool = True) -> None:
    reporter = get_reporter()
    action = "catalog" if dry_run else "delete"
    status = "discovered" if dry_run else "executing"
    account = _get_account_id(session)

    # Construct proper ARN for the application resource
    arn = f"arn:aws:elasticbeanstalk:{region}:{account}:application/{application_name}"

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
            "[%s][elasticbeanstalk][application] dry-run would delete application_name=%s",
            region,
            application_name,
        )
        return

    client = session.client("elasticbeanstalk", region_name=region)

    try:
        # Delete the application with TerminateEnvByForce to handle any remaining environments
        client.delete_application(
            ApplicationName=application_name,
            TerminateEnvByForce=True,
        )
        logger.info(
            "[%s][elasticbeanstalk][application] delete requested application_name=%s",
            region,
            application_name,
        )

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
        logger.error(
            "[%s][elasticbeanstalk][application] delete failed application_name=%s error=%s",
            region,
            application_name,
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


def cleanup_applications(session: Session, region: str, dry_run: bool = True, max_workers: int = 1) -> None:
    application_names: list[str] = catalog_applications(session=session, region=region)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(cleanup_application, session, region, app_name, dry_run) for app_name in application_names]
        for fut in as_completed(futures):
            fut.result()
