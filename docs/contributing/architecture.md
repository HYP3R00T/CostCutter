# Architecture

This document takes a closer look at how the main modules collaborate. It complements the user-facing [Architecture guide](/guide/architecture.md) with implementation details useful to contributors.

## Core components

### Configuration (`conf/config.py`)

- Loads the bundled defaults from `config.yaml`
- Merges optional overrides from home directory files, an explicit `--config` file, environment variables, and CLI keyword arguments
- Returns a lightweight `Config` object that supports attribute access (`config.aws.region`) and dictionary-style lookups (`config["aws"]`)

### Services (`services/`)

- Each service package exposes a `cleanup_<service>` function (for example `cleanup_ec2` and `cleanup_s3`)
- Service modules import their resource handlers and execute them in a fixed order; ordering is hard-coded to satisfy dependencies (instances before volumes, buckets last after objects are removed)
- Resource modules encapsulate AWS interactions, call `get_reporter()` to record events, and honour the `dry_run` flag

### Orchestrator (`orchestrator.py`)

- Maintains the `SERVICE_HANDLERS` mapping that links service names to their top-level cleanup functions
- Builds the worklist by crossing configured regions with allowed services and filtering out unsupported region/service combinations
- Uses `ThreadPoolExecutor` to run each `(region, service)` pair concurrently, counts successes, skips, and failures, and returns a summary dictionary alongside events captured by the reporter

### Reporter (`reporter.py`)

- Provides a process-wide singleton obtainable via `get_reporter()`
- Records events with timestamps, ARNs, resource metadata, and dry run status in a thread-safe list
- Supplies snapshots to the CLI and can flush events to CSV with optional append behaviour

### Logger (`logger.py`)

- Builds file handlers when logging is enabled in the merged configuration
- Sets the root log level and quiets chatty third-party loggers such as boto3 and urllib3

### CLI (`cli.py`)

- Exposes the Typer command that accepts `--dry-run`, `--no-dry-run`, and `--config`
- Clears the terminal, prints the banner, and renders a Rich live table while the orchestrator runs
- Handles keyboard interrupts gracefully and prints a summary along with CSV export information at the end of the run

## Execution flow

1. `costcutter [--dry-run|--no-dry-run] [--config PATH]` launches the Typer command
2. The CLI loads the merged configuration and initialises logging
3. `orchestrate_services` creates a boto3 session using `create_aws_session`
4. The orchestrator expands the requested regions and services into discrete tasks, filtering out combinations that the AWS SDK reports as unsupported
5. Worker threads invoke the service cleanup functions; each resource handler records events through the reporter
6. As events stream in, the CLI updates the live table; once tasks complete it prints a summary table and optionally writes the CSV report
7. The orchestrator returns a dictionary containing `processed`, `skipped`, `failed`, and `events` so callers can assert on results in tests or automation

## Concurrency model

- Parallelism is achieved at two levels: the orchestrator runs multiple `(region, service)` combinations at once, and individual resource handlers use `ThreadPoolExecutor` when performing per-resource API calls
- The reporter guards its internal list with a lock; this is the only shared mutable state across threads
- AWS sessions are thread-safe according to boto3 so handlers reuse the session passed to them

## Error handling

- Service handler exceptions propagate through their futures; the orchestrator increments the `failed` counter, logs the stack trace, and continues processing remaining work
- After all futures settle, the CLI checks for recorded exceptions and re-raises the first one so shell scripts receive a non-zero exit code when a cleanup fails
- Resource handlers log recoverable AWS errors (such as DryRunOperation) at info level so users know the API call would succeed

## Extending the system

- Register new services by adding an entry to `SERVICE_HANDLERS` and providing a corresponding `cleanup_<service>` implementation
- Resource modules should follow the catalog/delete/cleanup trio found in existing EC2 and S3 handlers
- Update the default configuration and documentation when exposing new services or regions

## Related material

- [Code Structure](./code-structure.md) for an overview of repository layout
- [Adding a Service](./adding-service.md) for step-by-step guidance on new services
- [Adding Subresources](./adding-subresources.md) when extending an existing service package
