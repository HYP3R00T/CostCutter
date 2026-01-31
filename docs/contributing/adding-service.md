# Adding a Service

This guide covers the steps required to plug a new AWS service into the orchestrator.

## 1. Scaffold the package

```bash
mkdir -p src/costcutter/services/<service>
touch src/costcutter/services/<service>/__init__.py
```

Populate `__init__.py` with a top-level cleanup function that calls the service-specific resource modules:

```python
from boto3.session import Session

from costcutter.services.<service>.resource1 import cleanup_resource1
from costcutter.services.<service>.resource2 import cleanup_resource2


def cleanup_<service>(session: Session, region: str, dry_run: bool = True, max_workers: int = 1) -> None:
    cleanup_resource1(session=session, region=region, dry_run=dry_run, max_workers=max_workers)
    cleanup_resource2(session=session, region=region, dry_run=dry_run, max_workers=max_workers)
```

Keep imports at the top of the module (matching existing services) so handlers are loaded once.

## 2. Implement resource handlers

Create one module per resource (see [Adding Subresources](./adding-subresources.md) for details). Each module should:

- Provide a `catalog_<resource>` helper that returns IDs
- Provide a `cleanup_<resource>` helper that performs a single delete and records an event with `get_reporter()`
- Provide a `cleanup_<resources>` helper that orchestrates deletion for the collection, usually with `ThreadPoolExecutor`

Use the EC2 handlers (`src/costcutter/services/ec2/`) as a concrete reference.

## 3. Register the service with the orchestrator

Open `src/costcutter/orchestrator.py` and update the `SERVICE_HANDLERS` dictionary:

```python
from costcutter.services.<service> import cleanup_<service>

SERVICE_HANDLERS = {
    "ec2": cleanup_ec2,
    "s3": cleanup_s3,
    "<service>": cleanup_<service>,
}
```

If the service only supports a subset of regions, rely on `session.get_available_regions("<service>")` inside the orchestrator (already implemented) to filter unsupported combinations automatically.

## 4. Update defaults and documentation

- Append the service name to `aws.services` defaults in `src/costcutter/config.py`
- Refresh relevant documentation (for example `docs/guide/supported-services.md`)

## 5. Write tests

- Add unit tests under `tests/` that exercise the new handlers
- Monkeypatch `costcutter.reporter.get_reporter` to return a deterministic stub when asserting on recorded events
- Cover both dry run and destructive paths where practical

## 6. Run quality checks

```bash
mise run fmt
mise run lint
mise run test
```

## Reference implementation

`src/costcutter/services/ec2/` demonstrates how to coordinate multiple resource handlers and respect dependencies between them.
