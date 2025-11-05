# Adding a Service

How to create handlers for new AWS services (Lambda, RDS, etc.).

---

## Steps

### 1. Create Service Directory

```bash
mkdir -p src/costcutter/services/<service>
touch src/costcutter/services/<service>/__init__.py
```

---

### 2. Create `__init__.py`

**File:** `src/costcutter/services/<service>/__init__.py`

```python
from costcutter.services import SERVICE_REGISTRY

def cleanup_<service>(session, region, reporter, dry_run=True):
    """Main entry point for <service> cleanup."""
    # Import subresource handlers
    from costcutter.services.<service>.resource1 import cleanup_resource1
    from costcutter.services.<service>.resource2 import cleanup_resource2

    # Execute in order
    cleanup_resource1(session, region, reporter, dry_run)
    cleanup_resource2(session, region, reporter, dry_run)

# Register service
SERVICE_REGISTRY["<service>"] = {
    "resource1": {...},
    "resource2": {...},
}
```

---

### 3. Add Subresource Handlers

Follow [Adding Subresources](./adding-subresources.md) guide for each resource type.

---

### 4. Update Configuration

**File:** `src/costcutter/conf/config.yaml`

Add service to `services` list:

```yaml
services:
  - ec2
  - s3
  - lambda  # New!
```

---

### 5. Write Tests

**File:** `tests/test_<service>.py`

```python
def test_cleanup_service():
    session = DummySession()
    reporter = Reporter()

    cleanup_lambda(session, "us-east-1", reporter, dry_run=True)

    events = reporter.get_events()
    assert len(events) > 0
```

---

### 6. Quality Checks

```bash
mise run fmt
mise run lint
mise run test
```

---

## Example

See `src/costcutter/services/ec2/` for a complete service implementation with multiple subresources.

---

## Next Steps

- [Adding Subresources](./adding-subresources.md) : Add resource handlers
- [Testing Guide](./testing.md) : Write tests
- [Submission Guidelines](./submission.md) : Submit PR
