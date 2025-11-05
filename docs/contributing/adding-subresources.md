# Adding Subresources

How to add a new resource handler inside an existing service package.

## The three-function pattern

Each resource module typically exposes:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

from boto3.session import Session
from botocore.exceptions import ClientError

from costcutter.logger import logger
from costcutter.reporter import get_reporter


def catalog_resources(session: Session, region: str) -> list[str]:
    client = session.client("service", region_name=region)
    response = client.describe_resources()
    return [r["Id"] for r in response.get("Resources", [])]


def cleanup_resource(session: Session, region: str, resource_id: str, dry_run: bool) -> None:
    reporter = get_reporter()
    if dry_run:
        reporter.record("service", region, "resource", resource_id, "skipped (dry-run)")
        return

    client = session.client("service", region_name=region)
    try:
        client.delete_resource(ResourceId=resource_id)
        reporter.record("service", region, "resource", resource_id, "deleted")
    except ClientError as error:
        logger.error("Failed to delete %s in %s: %s", resource_id, region, error)
        reporter.record("service", region, "resource", resource_id, "failed")


def cleanup_resources(session: Session, region: str, dry_run: bool, max_workers: int) -> None:
    resource_ids = catalog_resources(session=session, region=region)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(cleanup_resource, session, region, resource_id, dry_run)
            for resource_id in resource_ids
        ]
        for future in as_completed(futures):
            future.result()
```

Keep signatures consistent with existing modules so `cleanup_<service>` can pass through `dry_run` and `max_workers` without adaptation.

## Steps

### 1. Create Handler File

**Location:** `src/costcutter/services/<service>/<resource>.py`

**Example:** `src/costcutter/services/ec2/volumes.py`
### 2. Implement the functions

- Replace `"service"` with the actual service identifier used in reporter logs
- Replace `describe_resources()` and `delete_resource()` with the correct boto3 calls
- Adjust the response parsing and pagination for the service-specific API shape
- Respect dependencies (for example, ensure EC2 volumes are detached before deletion)

### 3. Wire the handler into the service package

In `src/costcutter/services/<service>/__init__.py`, import the module and delegate from `cleanup_<service>`:

```python
from costcutter.services.<service>.<resource> import cleanup_resources


def cleanup_<service>(session: Session, region: str, dry_run: bool = True, max_workers: int = 1) -> None:
    cleanup_resources(session=session, region=region, dry_run=dry_run, max_workers=max_workers)
```

Call order inside `cleanup_<service>` should reflect dependencies. For example, delete EC2 instances before their security groups.

Finally, confirm the service is registered in `SERVICE_HANDLERS` (see [Adding a Service](./adding-service.md)).
### 4. Write Tests

**File:** `tests/test_<service>_<resource>.py`

```python
from unittest.mock import MagicMock

from costcutter.services.ec2.volumes import catalog_volumes, cleanup_volumes


def test_catalog_volumes(monkeypatch):
    session = MagicMock()
    session.client.return_value.describe_volumes.return_value = {"Volumes": [{"VolumeId": "vol-1"}]}

    volume_ids = catalog_volumes(session=session, region="us-east-1")
    assert volume_ids == ["vol-1"]


def test_cleanup_volumes_dry_run(monkeypatch):
    reporter = MagicMock()
    monkeypatch.setattr("costcutter.services.ec2.volumes.get_reporter", lambda: reporter)

    cleanup_volumes(session=MagicMock(), region="us-east-1", dry_run=True, max_workers=1)
    reporter.record.assert_called()
```
### 5. Quality Checks

```bash
mise run fmt     # Format code
mise run lint    # Check linting
mise run test    # Run tests
```
## Common Patterns

### Pagination

If resources exceed one page:

```python
def catalog_resources(session: Session, region: str) -> list[str]:
    client = session.client("service", region_name=region)
    paginator = client.get_paginator("describe_resources")

    resource_ids: list[str] = []
    for page in paginator.paginate():
        resource_ids.extend([r["Id"] for r in page.get("Resources", [])])

    return resource_ids
```

### Dependencies

If resource must be detached/stopped first:

```python
def cleanup_resource(session: Session, region: str, resource_id: str, dry_run: bool) -> None:
    if dry_run:
        get_reporter().record(...)
        return

    client = session.client("service", region_name=region)

    # Detach/stop first
    client.detach_resource(ResourceId=resource_id)

    # Then delete
    client.delete_resource(ResourceId=resource_id)
    get_reporter().record(...)
```

### Error Handling

```python
def cleanup_resource(session: Session, region: str, resource_id: str, dry_run: bool) -> None:
    reporter = get_reporter()
    try:
        # ... deletion logic
        reporter.record(..., "deleted")
    except ClientError as e:
        logger.error("Failed to delete %s: %s", resource_id, e)
        reporter.record(..., "failed")
```
## Example: Adding EC2 Volumes

See `src/costcutter/services/ec2/volumes.py` for a complete real-world example.
## Next Steps

- [Architecture](./architecture.md) : Understand execution flow
- [Testing Guide](./testing.md) : Write comprehensive tests
- [Submission Guidelines](./submission.md) : Submit your PR
