# Code Structure

How the codebase is organized.

---

## Directory Layout

```
CostCutter/
├── src/costcutter/          # Main application code
│   ├── __main__.py          # Python module entry point
│   ├── cli.py               # Command-line interface
│   ├── main.py              # Application entry point
│   ├── orchestrator.py      # Multi-region/service coordinator
│   ├── reporter.py          # Thread-safe event tracking
│   ├── logger.py            # File-based logging
│   │
│   ├── conf/                # Configuration management
│   │   ├── config.py        # Pydantic models
│   │   └── config.yaml      # Default settings
│   │
│   ├── core/                # Shared utilities
│   │   └── session_helper.py # AWS session creation
│   │
│   └── services/            # AWS service handlers
│       ├── ec2/             # EC2 subresources
│       │   ├── __init__.py  # Service registry
│       │   ├── common.py    # Shared utilities
│       │   ├── instances.py
│       │   ├── volumes.py
│       │   └── ...
│       │
│       └── s3/              # S3 subresources
│           ├── __init__.py
│           └── buckets.py
│
├── tests/                   # Unit tests (mirrors src/)
│   ├── test_cli.py
│   ├── test_orchestrator.py
│   ├── test_ec2_instances.py
│   ├── test_ec2_volumes.py
│   └── ...
│
├── docs/                    # Documentation
│   ├── guide/               # User guides
│   └── contributing/        # Contribution guides
│
├── logs/                    # Application logs
├── pyproject.toml          # Python project config
├── requirements.txt        # Dependencies
├── ruff.toml              # Linting config
└── mise.toml              # Task runner config
```

---

## File Purposes

### Entry Points

- **`__main__.py`** : Allows running as `python -m costcutter`
- **`main.py`** : Core entry point, loads config and starts orchestrator
- **`cli.py`** : Typer-based CLI, displays UI

### Core Logic

- **`orchestrator.py`** : Coordinates parallel execution across services/regions
- **`reporter.py`** : Thread-safe event tracking and CSV export
- **`logger.py`** : Structured logging to files

### Configuration

- **`conf/config.py`** : Pydantic models for validation
- **`conf/config.yaml`** : Default configuration file

### Utilities

- **`core/session_helper.py`** : Creates AWS boto3 sessions with credentials

### Services

Each service directory (`ec2/`, `s3/`, etc.):
- **`__init__.py`** : Main handler (`cleanup_<service>()`) and `SERVICE_REGISTRY`
- **`common.py`** (optional) : Shared utilities for that service
- **`<resource>.py`** : Individual resource handlers

---

## Naming Conventions

### Files
- `snake_case.py` for all Python files
- Match resource names (e.g., `elastic_ips.py` not `eips.py`)

### Functions
- `catalog_<resource>()` : Lists available resources
- `cleanup_<resource>(resource_id, ...)` : Deletes single resource
- `cleanup_<resources>()` : Batch deletion with parallelization

### Classes
- `PascalCase` for all class names
- Example: `Config`, `Reporter`, `SessionHelper`

### Constants
- `ALL_CAPS` for module-level constants
- Example: `SERVICE_REGISTRY`, `DEFAULT_REGION`

---

## Import Organization

Standard order (enforced by ruff):
1. Standard library imports
2. Third-party imports (boto3, typer, rich, etc.)
3. Local imports from `costcutter`

Example:
```python
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import boto3
from rich.console import Console

from costcutter.logger import get_logger
from costcutter.reporter import Reporter
```

---

## Test Structure

Tests mirror the `src/` structure:
- `test_<module>.py` for each module
- Use `DummySession` mock for AWS calls
- Group related tests in classes (optional)

Example:
```
src/costcutter/services/ec2/volumes.py
tests/test_ec2_volumes.py
```

---

## Adding New Files

### New Service

1. Create directory: `src/costcutter/services/<service>/`
2. Add `__init__.py` with `cleanup_<service>()` and registry
3. Add subresource handlers (e.g., `<resource>.py`)
4. Create tests: `tests/test_<service>_<resource>.py`

### New Subresource

1. Create file: `src/costcutter/services/<service>/<resource>.py`
2. Implement three functions (catalog, cleanup single, cleanup batch)
3. Register in `services/<service>/__init__.py`
4. Create tests: `tests/test_<service>_<resource>.py`

### New Utility

1. Add to `src/costcutter/core/` if shared across services
2. Add to `src/costcutter/services/<service>/common.py` if service-specific
3. Write tests

---

## Key Patterns

### Service Registry Pattern

All subresources are registered in `SERVICE_REGISTRY` dict:

```python
# services/ec2/__init__.py
from costcutter.services import SERVICE_REGISTRY
from costcutter.services.ec2.instances import catalog_instances, cleanup_instances

SERVICE_REGISTRY["ec2"] = {
    "instances": {"catalog": catalog_instances, "cleanup": cleanup_instances},
}
```

### Three-Function Pattern

Every subresource handler has exactly three functions:

1. `catalog_<resource>()` : Returns list of resources
2. `cleanup_<resource>(resource_id, ...)` : Deletes one resource
3. `cleanup_<resources>()` : Orchestrates parallel deletion

### Reporter Integration

All handlers use Reporter to track events:

```python
reporter.record(
    service="ec2",
    region="us-east-1",
    resource_type="volume",
    resource_id="vol-abc123",
    status="deleted",
    dry_run=dry_run
)
```

---

## Dependencies Between Files

- **Orchestrator** depends on:
  - Configuration (`conf/config.py`)
  - Session Helper (`core/session_helper.py`)
  - Service Registry (`services/__init__.py`)
  - Reporter (`reporter.py`)
  - Logger (`logger.py`)

- **Service Handlers** depend on:
  - Reporter (`reporter.py`)
  - Logger (`logger.py`)
  - Service-specific utilities (`services/<service>/common.py`)

- **Resource Handlers** depend on:
  - Reporter (`reporter.py`)
  - Logger (`logger.py`)
  - boto3 clients

---

## Configuration Files

### `pyproject.toml`
- Project metadata
- Python version requirement (3.13+)
- Entry point: `costcutter = "costcutter.cli:app"`

### `requirements.txt`
- Runtime dependencies: boto3, typer, rich, pydantic

### `ruff.toml`
- Linting rules
- Line length (120 chars)
- Import sorting

### `mise.toml`
- Task runner configuration
- Commands: `mise run lint`, `mise run fmt`, `mise run test`

---

## Next Steps

- [Architecture](./architecture.md) : Understand component interactions
- [Adding a Service](./adding-service.md) : Create new service handlers
- [Adding Subresources](./adding-subresources.md) : Add resources to services
