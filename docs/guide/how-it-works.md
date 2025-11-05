# How It Works

This page breaks down a single CostCutter run from CLI invocation to final summary.

## High level timeline

1. **CLI start** - Typer parses flags, clears the console, and prints the ASCII banner
2. **Configuration merge** - `get_config` loads defaults, home overrides, optional files, environment variables, and CLI overrides
3. **Logging** - `setup_logging` configures file handlers and suppresses noisy libraries
4. **Session creation** - `create_aws_session` builds a boto3 session using explicit keys, a credential file, or the default resolver
5. **Worklist build** - the orchestrator pairs each configured region with each requested service and filters out unsupported region/service combinations
6. **Parallel execution** - `(region, service)` pairs run in a thread pool and call the corresponding handler
7. **Resource handling** - handlers list resources, honour the `dry_run` flag, delete items when allowed, and record events via the reporter
8. **Summary and export** - when the pool drains the CLI prints the summary table and optionally exports all events to CSV

## Dry run versus destructive mode

- `dry_run=true` (default) instructs handlers to list resources and avoid destructive calls. Existing handlers either set `DryRun=True` on supported APIs (EC2) or short-circuit before deletion (S3 buckets).
- Disabling dry run (`--no-dry-run` or config update) runs the same logic without the safeguards, so resources are deleted for real.
- Every event contains a `dry_run` flag inside its metadata to help you audit what happened.

## Concurrency model

- `ThreadPoolExecutor` fans out region/service pairs in `orchestrate_services`
- Each service handler uses another `ThreadPoolExecutor` for per-resource operations (for example terminating multiple instances)
- The global reporter protects its in-memory event list with a lock so threads can record events safely

## Event lifecycle

1. A handler discovers or deletes a resource
2. It calls `reporter.record(...)` with the service, resource, action (catalog or delete), ARN, and metadata such as status
3. The CLI polls `reporter.snapshot()` to refresh the live table
4. After the run, `reporter.to_dicts()` feeds the summary returned from `orchestrate_services`
5. If CSV reporting is enabled, `reporter.write_csv()` serialises every event with light metadata formatting

## Configuration precedence

Configuration sources apply in this order:

1. Bundled defaults (`src/costcutter/conf/config.yaml`)
2. Home overrides (`~/.costcutter.yaml`, `.yml`, `.toml`, `.json`)
3. Explicit file from `--config`
4. Environment variables prefixed with `COSTCUTTER_`
5. CLI flags (`--dry-run`, `--no-dry-run`)

Later sources override earlier ones. Nested keys are merged recursively so you can set only the fields you care about.

## Safety features

- Dry run by default with opt-in destructive mode
- Rich live table so you can observe progress in real time
- Summary counts (`processed`, `skipped`, `failed`) returned to the caller for post-processing
- Optional CSV export for auditing
- Structured log files for deeper debugging

## Error handling

- Handler exceptions propagate to the future associated with that `(region, service)` pair; the orchestrator increments the `failed` count and continues with other tasks
- The CLI surfaces the first failure after shutting down the live table so shell scripts receive a non-zero exit code
- Logging captures stack traces even when the Rich UI is active

## Next steps

- Understand the static structure of the code in [Architecture](./architecture.md)
- Review the specific cleanup routines in [Supported Services](./supported-services.md)
- Learn how to solve common issues in [Troubleshooting](./troubleshooting.md)
