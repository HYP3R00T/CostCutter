# Contributing to CostCutter

Thank you for your interest in contributing to **CostCutter**! This guide will help you understand the project architecture and how to add new AWS services and resources.

---

## 📋 Table of Contents

- [Project Architecture](#project-architecture)
- [Understanding the Code Structure](#understanding-the-code-structure)
- [Adding a New AWS Service](#adding-a-new-aws-service)
- [Adding Subresources to an Existing Service](#adding-subresources-to-an-existing-service)
- [The Reporter System](#the-reporter-system)
- [The Logging System](#the-logging-system)
- [The CLI System](#the-cli-system)
- [Testing Your Changes](#testing-your-changes)
- [Code Style and Standards](#code-style-and-standards)
- [Submission Guidelines](#submission-guidelines)

---

## Project Architecture

CostCutter follows a **modular, service-based architecture** where each AWS service (EC2, S3, Lambda, etc.) is implemented as a separate module with its own resource handlers.

### High-Level Flow

```
┌─────────────┐
│   CLI       │ ← Entry point (Typer-based)
│  (cli.py)   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Orchestrator   │ ← Coordinates multi-region, multi-service execution
│(orchestrator.py)│
└────────┬────────┘
         │
         ▼
┌────────────────────┐
│  Service Handlers  │ ← One per AWS service (ec2, s3, lambda, etc.)
│  (services/*/      │
│   __init__.py)     │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Resource Handlers  │ ← Individual resource cleanup logic
│  (services/*/      │ ← (instances.py, volumes.py, buckets.py, etc.)
│   <resource>.py)   │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│     Reporter       │ ← Thread-safe event tracking & CSV export
│  (reporter.py)     │
└────────────────────┘
```

### Key Components

1. **CLI** (`src/costcutter/cli.py`) : User interface with live event display
2. **Orchestrator** (`src/costcutter/orchestrator.py`) : Multi-region/service coordination
3. **Service Handlers** (`src/costcutter/services/*/`) : Per-service cleanup logic
4. **Resource Handlers** : Individual resource cleanup implementations
5. **Reporter** (`src/costcutter/reporter.py`) : Event tracking and CSV export
6. **Logger** (`src/costcutter/logger.py`) : File-based structured logging

---

## Understanding the Code Structure

```
src/costcutter/
├── cli.py                    # CLI interface (Typer + Rich)
├── orchestrator.py           # Multi-region orchestration
├── reporter.py               # Event tracking system
├── logger.py                 # Logging configuration
├── conf/
│   ├── config.py             # Configuration management
│   └── config.yaml           # Default configuration
├── core/
│   └── session_helper.py     # AWS session creation
└── services/
    ├── ec2/
    │   ├── __init__.py       # EC2 service handler (registers subresources)
    │   ├── common.py         # Shared utilities (e.g., _get_account_id)
    │   ├── instances.py      # EC2 instance cleanup
    │   ├── volumes.py        # EBS volume cleanup
    │   ├── snapshots.py      # EBS snapshot cleanup
    │   ├── elastic_ips.py    # Elastic IP cleanup
    │   ├── key_pairs.py      # Key pair cleanup
    │   └── security_groups.py# Security group cleanup
    └── s3/
        ├── __init__.py       # S3 service handler
        └── buckets.py        # S3 bucket cleanup
```

---

## Adding a New AWS Service

### Step 1: Create the Service Directory

Create a new directory under `src/costcutter/services/` for your service:

```bash
mkdir -p src/costcutter/services/lambda
```

### Step 2: Create the Service Handler (`__init__.py`)

Every service needs an `__init__.py` that:
- Imports all resource handlers
- Registers them in a `_HANDLERS` dictionary
- Exports a `cleanup_<service>` function

**Example:** `src/costcutter/services/lambda/__init__.py`

```python
from boto3.session import Session

from costcutter.services.lambda_.functions import cleanup_functions
from costcutter.services.lambda_.layers import cleanup_layers

_HANDLERS = {
    "functions": cleanup_functions,
    "layers": cleanup_layers,
}


def cleanup_lambda(session: Session, region: str, dry_run: bool = True, max_workers: int = 1):
    """
    Cleanup all Lambda resources in a region.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.
        dry_run: If True, simulate cleanup without deleting.
        max_workers: Number of threads for parallel execution.
    """
    for fn in _HANDLERS.values():
        fn(session=session, region=region, dry_run=dry_run, max_workers=max_workers)
```

### Step 3: Register the Service in the Orchestrator

Edit `src/costcutter/orchestrator.py` to register your new service:

```python
from costcutter.services.ec2 import cleanup_ec2
from costcutter.services.s3 import cleanup_s3
from costcutter.services.lambda_ import cleanup_lambda  # NEW

SERVICE_HANDLERS = {
    "ec2": cleanup_ec2,
    "s3": cleanup_s3,
    "lambda": cleanup_lambda,  # NEW
}
```

### Step 4: Enable in Configuration

Users can now enable your service in `config.yaml`:

```yaml
aws:
  services:
    - ec2
    - s3
    - lambda  # NEW
```

---

## Adding Subresources to an Existing Service

Subresources are individual resource types within a service (e.g., EC2 instances, volumes, snapshots).

### Step 1: Create the Resource Handler File

Create a new Python file for your resource under the service directory.

**Example:** `src/costcutter/services/ec2/volumes.py`

### Step 2: Follow the Standard Handler Pattern

Every resource handler must implement:

1. **`catalog_<resource>()`** : List resources in a region
2. **`cleanup_<resource>()`** : Delete a single resource
3. **`cleanup_<resources>()`** : Delete all resources (orchestrates cleanup)

**Template:**

```python
"""Handler for deleting <RESOURCE_NAME>."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from boto3.session import Session
from botocore.exceptions import ClientError

from costcutter.reporter import get_reporter
from costcutter.services.<service>.common import _get_account_id  # If available

SERVICE: str = "<service>"
RESOURCE: str = "<resource>"
logger = logging.getLogger(__name__)


def catalog_<resources>(session: Session, region: str) -> list[str]:
    """
    List all <resources> in a region.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.

    Returns:
        List of resource IDs.
    """
    client = session.client(service_name="<service>", region_name=region)

    resource_ids: list[str] = []
    try:
        response = client.describe_<resources>()  # Adjust API call
        resources = response.get("<Resources>", [])
        resource_ids = [res.get("<IdField>") for res in resources if res.get("<IdField>")]
        logger.info("[%s][%s][%s] Found %d resources", region, SERVICE, RESOURCE, len(resource_ids))
    except ClientError as e:
        logger.error("[%s][%s][%s] Failed to list: %s", region, SERVICE, RESOURCE, e)
        resource_ids = []
    return resource_ids


def cleanup_<resource>(session: Session, region: str, resource_id: Any, dry_run: bool = True) -> None:
    """
    Delete a single <resource>.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.
        resource_id: Resource ID to delete.
        dry_run: If True, simulate deletion without making changes.
    """
    reporter = get_reporter()
    action = "catalog" if dry_run else "delete"
    status = "discovered" if dry_run else "executing"
    account = _get_account_id(session)  # If available

    # Construct ARN (adjust pattern as needed)
    arn = f"arn:aws:<service>:{region}:{account}:<resource>/{resource_id}"

    reporter.record(
        region,
        SERVICE,
        RESOURCE,
        action,
        arn=arn,
        meta={"status": status, "dry_run": dry_run},
    )

    client = session.client("<service>", region_name=region)
    try:
        client.delete_<resource>(<IdParam>=resource_id, DryRun=dry_run)
        if not dry_run:
            logger.info("[%s][%s][%s] Deleted resource_id=%s", region, SERVICE, RESOURCE, resource_id)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code") if hasattr(e, "response") else None
        if dry_run and code == "DryRunOperation":
            logger.info("[%s][%s][%s] dry-run delete would succeed resource_id=%s", region, SERVICE, RESOURCE, resource_id)
        else:
            logger.error("[%s][%s][%s] delete failed resource_id=%s error=%s", region, SERVICE, RESOURCE, resource_id, e)


def cleanup_<resources>(session: Session, region: str, dry_run: bool = True, max_workers: int = 1) -> None:
    """
    Delete all <resources> in a region.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.
        dry_run: If True, simulate deletion without making changes.
        max_workers: Number of threads for parallel execution.
    """
    resource_ids: list = catalog_<resources>(session=session, region=region)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(cleanup_<resource>, session, region, res_id, dry_run) for res_id in resource_ids]
        for fut in as_completed(futures):
            fut.result()
```

### Step 3: Register the Handler in the Service's `__init__.py`

```python
from costcutter.services.<service>.<resource> import cleanup_<resources>

_HANDLERS = {
    "existing_resource": cleanup_existing,
    "<resource>": cleanup_<resources>,  # NEW
}
```

The orchestrator will **automatically discover and execute** all registered handlers when the service is enabled.

---

## The Reporter System

The `Reporter` is a **thread-safe event tracking system** that records every action CostCutter takes.

### Key Concepts

- **Events** : Immutable records of actions (discovered, deleted, failed)
- **Thread-safe** : Uses locks to prevent race conditions during parallel execution
- **CSV Export** : Events are written to CSV for auditing

### Recording Events

Always use `get_reporter()` to access the global reporter instance:

```python
from costcutter.reporter import get_reporter

reporter = get_reporter()
reporter.record(
    region="us-east-1",
    service="ec2",
    resource="instance",
    action="delete",
    arn="arn:aws:ec2:us-east-1:123456789012:instance/i-123456",
    meta={"status": "executing", "dry_run": False},
)
```

### Event Fields

| Field       | Type         | Description                                      |
|-------------|--------------|--------------------------------------------------|
| `timestamp` | `str`        | ISO 8601 timestamp (UTC)                         |
| `region`    | `str`        | AWS region (e.g., `us-east-1`)                   |
| `service`   | `str`        | AWS service (e.g., `ec2`, `s3`)                  |
| `resource`  | `str`        | Resource type (e.g., `instance`, `volume`)       |
| `action`    | `str`        | Action taken (`catalog`, `delete`, `failed`)     |
| `arn`       | `str | None` | AWS Resource Name (if applicable)                |
| `meta`      | `dict`       | Additional metadata (status, dry_run, etc.)      |

### Actions Convention

- **`catalog`** : Resource discovered (dry-run mode)
- **`delete`** : Resource deletion initiated (execute mode)
- **`failed`** : Operation failed (error occurred)

---

## The Logging System

CostCutter uses **Python's `logging` module** with file-based output.

### Configuration

Logging is configured via `config.yaml`:

```yaml
logging:
  enabled: true
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  dir: ~/.local/share/costcutter/logs
```

### Log File Location

Logs are written to timestamped files:
```
~/.local/share/costcutter/logs/costcutter_YYYYMMDD_HHMMSS.log
```

### Logging in Code

Always use module-level loggers:

```python
import logging

logger = logging.getLogger(__name__)

def cleanup_something(...):
    logger.info("[%s][ec2][volume] Starting cleanup", region)
    logger.error("[%s][ec2][volume] Failed to delete vol-123: %s", region, error)
```

### Log Format Convention

Follow this pattern for consistency:

```python
logger.info("[REGION][SERVICE][RESOURCE] Message key=value")
```

**Example:**
```python
logger.info("[us-east-1][ec2][instance] Terminated instance_id=i-123 dry_run=True")
```

### Log Levels

- **`DEBUG`** : Detailed diagnostic information
- **`INFO`** : General informational messages (default)
- **`WARNING`** : Warning messages (potential issues)
- **`ERROR`** : Error messages (failures)
- **`CRITICAL`** : Critical errors (system failures)

---

## The CLI System

The CLI is built with **Typer** (argument parsing) and **Rich** (terminal UI).

### Components

1. **Banner** : ASCII art title (Figlet)
2. **Live Event Table** : Real-time event tail (last 10 events)
3. **Summary Table** : Aggregated event counts by service/resource/action
4. **CSV Export** : Events saved to file for auditing

### How the CLI Works

```python
# Entry point
@app.command()
def run(dry_run: bool = typer.Option(True, ...)):
    # 1. Display banner
    print_banner()

    # 2. Start live event display in background thread
    live_display_thread = threading.Thread(target=_live_display, args=(reporter, dry_run))

    # 3. Execute orchestrator (which spawns workers)
    result = orchestrate_services(dry_run=dry_run)

    # 4. Display summary table
    console.print(_render_summary_table(reporter, dry_run))

    # 5. Export CSV
    reporter.write_csv(csv_path, overwrite=False)
```

### Live Event Display

The CLI uses a **background thread** that continuously updates a Rich `Live` display:

```python
def _live_display(reporter, dry_run: bool):
    with Live(_render_table(reporter, dry_run), refresh_per_second=2) as live:
        while not stop_event.is_set():
            live.update(_render_table(reporter, dry_run))
            time.sleep(0.5)
```

This creates a **live-updating table** that shows the last 10 events as they're recorded.

---

## Testing Your Changes

### 1. Write Unit Tests

Create test files in `tests/` following the naming convention `test_<service>_<resource>.py`:

**Example:** `tests/test_ec2_volumes.py`

```python
"""Tests for costcutter.services.ec2.volumes"""

from costcutter.services.ec2 import volumes


class DummySession:
    def client(self, service_name=None, region_name=None):
        class Client:
            def get_caller_identity(self):
                return {"Account": "123456789012"}

            def describe_volumes(self, **kwargs):
                return {"Volumes": [{"VolumeId": "vol-123", "Size": 8}]}

            def delete_volume(self, **kwargs):
                return {}

        return Client()


def test_catalog_volumes():
    session = DummySession()
    volume_ids = volumes.catalog_volumes(session, "us-east-1")
    assert "vol-123" in volume_ids


def test_cleanup_volume(monkeypatch):
    session = DummySession()
    monkeypatch.setattr(
        "costcutter.services.ec2.volumes.get_reporter",
        lambda: type("R", (), {"record": lambda *a, **k: None})()
    )
    volumes.cleanup_volume(session, "us-east-1", "vol-123", dry_run=True)


def test_cleanup_volumes(monkeypatch):
    session = DummySession()
    monkeypatch.setattr("costcutter.services.ec2.volumes.catalog_volumes", lambda *args, **kwargs: ["vol-123"])
    monkeypatch.setattr("costcutter.services.ec2.volumes.cleanup_volume", lambda *args, **kwargs: None)
    volumes.cleanup_volumes(session, "us-east-1", dry_run=True, max_workers=1)
```

### 2. Run Tests

```bash
mise run test
```

### 3. Check Test Coverage

```bash
mise run test_cov
```

### 4. Lint Your Code

```bash
mise run lint
```

### 5. Format Your Code

```bash
mise run fmt
```

---

## Code Style and Standards

CostCutter follows strict Python coding standards. Please review `.github/copilot-instructions.md` for complete guidelines.

### Key Standards

#### Naming Conventions

- **Variables/Functions:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `ALL_CAPS`
- **Private members:** `_leading_underscore`

#### Type Hints

Always use type hints:

```python
def cleanup_volumes(session: Session, region: str, dry_run: bool = True, max_workers: int = 1) -> None:
    ...
```

#### Docstrings

Use Google-style docstrings:

```python
def catalog_volumes(session: Session, region: str) -> list[str]:
    """
    List all available EBS volumes in a region.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.

    Returns:
        List of volume IDs.

    Raises:
        ClientError: If AWS API call fails.
    """
```

#### Error Handling

Always catch specific exceptions:

```python
try:
    client.delete_volume(VolumeId=volume_id)
except ClientError as e:
    logger.error("[%s][ec2][volume] Failed to delete: %s", region, e)
```

---

## Submission Guidelines

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/CostCutter.git
cd CostCutter
```

### 2. Create a Feature Branch

```bash
git checkout -b feat-add-lambda-support
```

### 3. Make Your Changes

- Follow the patterns documented above
- Add tests for new functionality
- Update documentation if needed

### 4. Run Quality Checks

```bash
mise run test      # All tests pass
mise run lint      # No linting errors
mise run fmt       # Code formatted
```

### 5. Commit with Conventional Commits

```bash
git add .
git commit -m "feat(lambda): add Lambda function and layer cleanup handlers"
```

**Commit message format:**
- `feat:` : New feature
- `fix:` : Bug fix
- `docs:` : Documentation changes
- `test:` : Test additions/changes
- `refactor:` : Code refactoring
- `chore:` : Maintenance tasks

### 6. Push & Create PR

```bash
git push origin feat-add-lambda-support
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Reference any related issues
- Include test results

---

## Quick Reference Checklist

### Adding a New Service

- [ ] Create `src/costcutter/services/<service>/` directory
- [ ] Create `src/costcutter/services/<service>/__init__.py` with `cleanup_<service>()` function
- [ ] Register `_HANDLERS` dictionary with resource handlers
- [ ] Add import and entry to `SERVICE_HANDLERS` in `orchestrator.py`
- [ ] Create tests in `tests/test_<service>.py`
- [ ] Update this documentation

### Adding a Subresource

- [ ] Create `src/costcutter/services/<service>/<resource>.py` file
- [ ] Implement `catalog_<resources>()` function
- [ ] Implement `cleanup_<resource>()` function (single resource)
- [ ] Implement `cleanup_<resources>()` function (all resources)
- [ ] Register in service's `_HANDLERS` dictionary
- [ ] Create tests in `tests/test_<service>_<resource>.py`
- [ ] Run tests and linter

---

## Getting Help

- **GitHub Issues:** Report bugs or request features
- **GitHub Discussions:** Ask questions or discuss ideas
- **Documentation:** Read existing docs for patterns and examples

---

**Thank you for contributing to CostCutter!** 🚀
