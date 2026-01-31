# Architecture

This section explains how the main pieces of CostCutter fit together and why the project is structured the way it is.

## Core components

**CLI (`src/costcutter/cli.py`)**
- Typer application that parses the small set of flags (`--dry-run`, `--no-dry-run`, `--config`)
- Renders a Rich live table of events while orchestration runs and a summary when it finishes
- Handles banner rendering, CSV export messaging, and keyboard interrupt handling

**Configuration loader (`src/costcutter/config.py`)**
- Loads the default YAML file bundled with the package
- Merges home directory overrides, an explicit file, environment variables, and CLI arguments
- Exposes the merged result through a lightweight `Config` wrapper that supports attribute access

**Logger (`src/costcutter/logger.py`)**
- Creates file handlers when logging is enabled and sets the root logger level
- Suppresses noisy third party loggers such as `boto3` and `urllib3`
- Produces structured timestamped log files per run

**Reporter (`src/costcutter/reporter.py`)**
- Records events from any thread through a mutex protected list
- Provides snapshots for the CLI and writes CSV files when requested
- Normalises event metadata (service, resource, action, ARN, timestamp) across handlers

**Orchestrator (`src/costcutter/orchestrator.py`)**
- Builds the worklist by pairing every selected region with each requested service
- Uses `ThreadPoolExecutor` to process those pairs concurrently
- Tracks processed, skipped, and failed counts while the worker threads run
- Relies on `SERVICE_HANDLERS` to locate the top level function for each service

**Service handlers (`src/costcutter/services/`)**
- Each module exposes a `cleanup_<service>()` function that enumerates and deletes its resources
- Resource modules rely on boto3 clients, honour the `dry_run` flag, and report every action through the reporter
- EC2 handlers share helpers such as `_get_account_id` to construct accurate ARNs

## Data flow

1. CLI parses arguments and clears the terminal
2. `load_config` merges configuration sources into a single object
3. Logging is initialised based on the merged configuration
4. The orchestrator resolves regions and services, then creates an AWS session via `create_aws_session`
5. Each `(region, service)` pair runs in the thread pool and calls the appropriate handler
6. Resource handlers interact with AWS, record events, and respect dry run semantics
7. Reporter snapshots feed the live table; once finished the CLI prints the summary and optional CSV export location

## Concurrency model

- Region and service combinations run in parallel to maximise throughput
- Individual resource deletions inside a handler also use `ThreadPoolExecutor`
- Shared state is limited to the reporter (protected by a lock) and cached account identifiers in `services/ec2/common.py`

## Error handling

- Service handler exceptions bubble up to the orchestrator, which records the failure and continues processing other tasks
- The CLI surfaces the first orchestrator exception after the live view closes so users see a non-zero exit when problems occur
- Logging captures full tracebacks while the live table keeps the UI readable

## Extensibility

- Adding a new service only requires a new module with a `cleanup_*` function and a `SERVICE_HANDLERS` entry
- The config loader already understands nested dictionaries supplied from files or environment variables
- Reporter CSV exports automatically include new resource metadata because events carry arbitrary key-value pairs

## Related documentation

- [How It Works](./how-it-works.md) describes the runtime timeline in more detail
- [Supported Services](./supported-services.md) lists everything the current handlers manage
- [Contributing Architecture](../contributing/architecture.md) dives into implementation details for contributors
