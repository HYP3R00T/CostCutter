# Adding Subresources

How to add new resource types to existing AWS services.

---

## The Three-Function Pattern

Every subresource handler needs exactly three functions:

```python
def catalog_resources(session, region, reporter):
    """List all resources in the region."""
    client = session.client("service", region_name=region)
    response = client.describe_resources()
    return [r["Id"] for r in response.get("Resources", [])]

def cleanup_resource(session, region, resource_id, reporter, dry_run):
    """Delete a single resource."""
    if dry_run:
        reporter.record("service", region, "resource", resource_id, "skipped (dry-run)")
        return

    client = session.client("service", region_name=region)
    client.delete_resource(ResourceId=resource_id)
    reporter.record("service", region, "resource", resource_id, "deleted")

def cleanup_resources(session, region, reporter, dry_run=True):
    """Delete all resources in parallel."""
    resource_ids = catalog_resources(session, region, reporter)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(cleanup_resource, session, region, rid, reporter, dry_run)
            for rid in resource_ids
        ]
        for future in as_completed(futures):
            future.result()  # Raise exceptions if any
```

---

## Steps

### 1. Create Handler File

**Location:** `src/costcutter/services/<service>/<resource>.py`

**Example:** `src/costcutter/services/ec2/volumes.py`

---

### 2. Implement Three Functions

Copy the pattern above and adjust:
- Replace `"service"` with actual service name (e.g., `"ec2"`)
- Replace `describe_resources()` with actual boto3 method (e.g., `describe_volumes()`)
- Replace `delete_resource()` with actual delete method (e.g., `delete_volume()`)
- Adjust response parsing based on actual API response structure

**Important:** Handle dependencies! Example: EC2 volumes must be detached before deletion.

---

### 3. Register in `__init__.py`

**File:** `src/costcutter/services/<service>/__init__.py`

Add to `SERVICE_REGISTRY`:

```python
from costcutter.services.ec2.volumes import catalog_volumes, cleanup_volumes

SERVICE_REGISTRY["ec2"] = {
    "instances": {...},
    "volumes": {  # New!
        "catalog": catalog_volumes,
        "cleanup": cleanup_volumes,
    },
}
```

**Order matters!** Place dependent resources after their dependencies (e.g., volumes after instances).

---

### 4. Write Tests

**File:** `tests/test_<service>_<resource>.py`

```python
from costcutter.services.ec2.volumes import catalog_volumes, cleanup_volumes

def test_catalog_volumes():
    session = DummySession()  # Mock session
    reporter = Reporter()

    volume_ids = catalog_volumes(session, "us-east-1", reporter)
    assert isinstance(volume_ids, list)

def test_cleanup_volumes_dry_run():
    session = DummySession()
    reporter = Reporter()

    cleanup_volumes(session, "us-east-1", reporter, dry_run=True)
    events = reporter.get_events()
    assert all(e["status"] == "skipped (dry-run)" for e in events)
```

---

### 5. Quality Checks

```bash
mise run fmt     # Format code
mise run lint    # Check linting
mise run test    # Run tests
```

---

## Common Patterns

### Pagination

If resources exceed one page:

```python
def catalog_resources(session, region, reporter):
    client = session.client("service", region_name=region)
    paginator = client.get_paginator("describe_resources")

    resource_ids = []
    for page in paginator.paginate():
        resource_ids.extend([r["Id"] for r in page.get("Resources", [])])

    return resource_ids
```

### Dependencies

If resource must be detached/stopped first:

```python
def cleanup_resource(session, region, resource_id, reporter, dry_run):
    if dry_run:
        reporter.record(...)
        return

    client = session.client("service", region_name=region)

    # Detach/stop first
    client.detach_resource(ResourceId=resource_id)

    # Then delete
    client.delete_resource(ResourceId=resource_id)
    reporter.record(...)
```

### Error Handling

```python
def cleanup_resource(session, region, resource_id, reporter, dry_run):
    try:
        # ... deletion logic
        reporter.record(..., "deleted")
    except ClientError as e:
        logger.error(f"Failed to delete {resource_id}: {e}")
        reporter.record(..., "failed")
```

---

## Example: Adding EC2 Volumes

See `src/costcutter/services/ec2/volumes.py` for a complete real-world example.

---

## Next Steps

- [Architecture](./architecture.md) : Understand execution flow
- [Testing Guide](./testing.md) : Write comprehensive tests
- [Submission Guidelines](./submission.md) : Submit your PR
