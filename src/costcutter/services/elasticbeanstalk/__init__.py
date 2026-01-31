from collections.abc import Callable

from boto3.session import Session

from costcutter.services.elasticbeanstalk.applications import cleanup_applications
from costcutter.services.elasticbeanstalk.environments import cleanup_environments

_HANDLERS = {
    "environments": cleanup_environments,
    "applications": cleanup_applications,
}


def get_handler_for_resource(resource_type: str) -> Callable[..., None] | None:
    """Get the handler function for a specific ElasticBeanstalk resource type.

    Args:
        resource_type: EB resource type (e.g., 'environments', 'applications')

    Returns:
        Handler function or None if resource type not found
    """
    return _HANDLERS.get(resource_type)


# Order matters: environments must be terminated before applications can be deleted
def cleanup_elasticbeanstalk(session: Session, region: str, dry_run: bool = True, max_workers: int = 1) -> None:
    for fn in _HANDLERS.values():
        fn(session=session, region=region, dry_run=dry_run, max_workers=max_workers)
