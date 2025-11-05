# Testing Guide

How to write and run tests.
## Writing Tests

### Test File Location

Mirror the `src/` structure:
- `src/costcutter/services/ec2/volumes.py` → `tests/test_ec2_volumes.py`
### Test Pattern

```python
from costcutter.services.ec2.volumes import catalog_volumes, cleanup_volumes
from costcutter.reporter import Reporter

class DummySession:
    """Mock AWS session."""
    def client(self, service_name, region_name):
        return DummyClient()

class DummyClient:
    """Mock boto3 client."""
    def describe_volumes(self):
        return {"Volumes": [{"VolumeId": "vol-123"}]}

    def delete_volume(self, VolumeId):
        pass

def test_catalog_volumes():
    session = DummySession()
    reporter = Reporter()

    volume_ids = catalog_volumes(session, "us-east-1", reporter)

    assert isinstance(volume_ids, list)
    assert "vol-123" in volume_ids

def test_cleanup_volumes_dry_run():
    session = DummySession()
    reporter = Reporter()

    cleanup_volumes(session, "us-east-1", reporter, dry_run=True)

    events = reporter.get_events()
    assert all(e["status"] == "skipped (dry-run)" for e in events)
```
## Running Tests

```bash
# Run all tests
mise run test

# Run specific test file
pytest tests/test_ec2_volumes.py

# Run with coverage
mise run test_cov
```
## Coverage

Target: 80%+ coverage for new code.

Check coverage report:
```bash
mise run test_cov
# Opens HTML report in browser
```
## Next Steps

- [Code Standards](./code-standards.md) : Follow conventions
- [Submission Guidelines](./submission.md) : Submit PR
