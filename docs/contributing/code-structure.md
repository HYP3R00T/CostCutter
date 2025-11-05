# Code Structure

This guide describes how the repository is organised and where to plug in new code.

## Directory layout

```
CostCutter/
├── src/costcutter/
│   ├── __init__.py
│   ├── __main__.py          # Enables `python -m costcutter`
│   ├── cli.py               # Typer CLI with Rich output
│   ├── main.py              # Minimal programmatic entry point
│   ├── orchestrator.py      # Region/service fan-out logic
│   ├── reporter.py          # Event recording and CSV export
│   ├── logger.py            # File logging configuration
│   ├── conf/
│   │   ├── config.py        # Configuration loader and helpers
│   │   └── config.yaml      # Bundled defaults
│   ├── core/
│   │   └── session_helper.py# AWS session creation helper
│   └── services/
│       ├── ec2/             # EC2 resource handlers
│       └── s3/              # S3 resource handlers
├── tests/                   # pytest suite mirroring src/
├── docs/                    # User and contributor docs
├── pyproject.toml           # Project metadata and dependencies
├── requirements.txt         # Frozen dependency export (dev included)
├── ruff.toml                # Lint and format configuration
└── mise.toml                # Reusable commands (fmt, lint, test)
```

## Key modules

- `cli.py`: wraps orchestration with Typer, renders the live Rich tables, and handles CSV export messaging
- `main.py`: exposes a `run()` function for programmatic use without the CLI presentation layer
- `orchestrator.py`: resolves regions and services, drives the worker pool, and returns summary statistics
- `conf/config.py`: loads the bundled YAML defaults, merges overrides from home files, explicit files, environment variables, and CLI arguments, and exposes a thin `Config` wrapper
- `reporter.py`: stores events in a thread-safe list, returns snapshots for the UI, and writes CSV files
- `logger.py`: builds file handlers when logging is enabled and suppresses noisy boto3 logging
- `core/session_helper.py`: constructs boto3 sessions using explicit credentials, shared credential files, or the default resolver
- `services/`: contains service-specific cleanup logic (EC2, S3, and any additional handlers you introduce)

## Service layout

Each service package exports a single `cleanup_<service>` function. For example, `services/ec2/__init__.py` defines `_HANDLERS` and iterates them while invoking resource modules such as `instances.py` and `volumes.py`. Resource modules usually expose three helpers:

1. `catalog_<resource>` to enumerate IDs
2. `cleanup_<resource>` to delete a single item (honouring `dry_run`)
3. `cleanup_<resources>` to fan out work with `ThreadPoolExecutor`

Handlers call `get_reporter()` to record catalog and delete events so the CLI stays in sync.

To register a new service, add its `cleanup_<service>` function and update the `SERVICE_HANDLERS` mapping inside `orchestrator.py`.

## Naming conventions

- Files and functions use `snake_case`
- Classes use `PascalCase`
- Module-level constants use `ALL_CAPS`
- Follow PEP 8 import grouping (stdlib, third party, local); ruff enforces this automatically

## Tests

Tests live under `tests/` and mirror the structure of `src/`. Common patterns:

- Use lightweight `DummySession` classes or monkeypatch boto3 clients to avoid network calls
- Monkeypatch `get_reporter` when you need deterministic event capture
- Rely on pytest fixtures for setup and cleanup

Example mapping:

```
src/costcutter/services/ec2/instances.py
tests/test_ec2_instances.py
```

## Supporting files

- `pyproject.toml`: declares dependencies, entry points, and the minimum Python version (3.13)
- `requirements.txt`: exported lock file that includes development dependencies (pytest, pytest-cov, ruff)
- `ruff.toml`: central place for lint, formatting, and isort settings
- `mise.toml`: defines `fmt`, `lint`, and `test` commands for consistent automation

## Related reading

- [Architecture](./architecture.md) for a closer look at runtime responsibilities
- [Adding a Service](./adding-service.md) when you need to register a new AWS service
- [Adding Subresources](./adding-subresources.md) for guidance on extending an existing service
