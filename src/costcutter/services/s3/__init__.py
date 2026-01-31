from collections.abc import Callable

from boto3.session import Session

from costcutter.services.s3.buckets import cleanup_buckets

_HANDLERS = {"buckets": cleanup_buckets}


def get_handler_for_resource(resource_type: str) -> Callable[..., None] | None:
    """Get the handler function for a specific S3 resource type.

    Args:
        resource_type: S3 resource type (e.g., 'buckets')

    Returns:
        Handler function or None if resource type not found
    """
    return _HANDLERS.get(resource_type)


def cleanup_s3(session: Session, region: str, dry_run: bool = True, max_workers: int = 1):
    # targets: list[str] or None => run all registered
    for fn in _HANDLERS.values():
        fn(session=session, region=region, dry_run=dry_run, max_workers=max_workers)
