from collections.abc import Callable

from boto3.session import Session

from costcutter.services.ec2.elastic_ips import cleanup_elastic_ips
from costcutter.services.ec2.instances import cleanup_instances
from costcutter.services.ec2.key_pairs import cleanup_key_pairs
from costcutter.services.ec2.security_groups import cleanup_security_groups
from costcutter.services.ec2.snapshots import cleanup_snapshots
from costcutter.services.ec2.volumes import cleanup_volumes

_HANDLERS = {
    "instances": cleanup_instances,
    "volumes": cleanup_volumes,
    "snapshots": cleanup_snapshots,
    "elastic_ips": cleanup_elastic_ips,
    "key_pairs": cleanup_key_pairs,
    "security_groups": cleanup_security_groups,
}


def get_handler_for_resource(resource_type: str) -> Callable[..., None] | None:
    """Get the handler function for a specific EC2 resource type.

    Args:
        resource_type: EC2 resource type (e.g., 'instances', 'volumes', 'security_groups')

    Returns:
        Handler function or None if resource type not found
    """
    return _HANDLERS.get(resource_type)


def cleanup_ec2(session: Session, region: str, dry_run: bool = True, max_workers: int = 1):
    # targets: list[str] or None => run all registered
    for fn in _HANDLERS.values():
        fn(session=session, region=region, dry_run=dry_run, max_workers=max_workers)
