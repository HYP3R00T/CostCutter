# How It Works

This page breaks down a single CostCutter run from CLI invocation to final summary.

## High level timeline

1. **CLI start** - Typer parses flags, clears the console, and prints the ASCII banner
2. **Configuration merge & validation** - `load_config` uses [utilityhub_config](https://utilityhub.hyperoot.dev/packages/utilityhub_config/) to load and merge configuration from defaults, global config, project config, explicit config files, dotenv, environment variables, and runtime overrides. Pydantic validation runs immediately—invalid configurations fail here with detailed error messages before any AWS API calls.
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

Configuration sources are resolved using [utilityhub_config](https://utilityhub.hyperoot.dev/packages/utilityhub_config/) in this order (lowest to highest priority):

1. Built-in defaults (field defaults in Pydantic models, defined in [config.py](../../src/costcutter/config.py))
2. Global config (`~/.config/costcutter/costcutter.{yaml,toml}`)
3. Project config (`./costcutter.{yaml,toml}` or `./config/costcutter.{yaml,toml}`)
4. Explicit config file (via `--config`)
5. Dotenv (`.env` file in current directory)
6. Environment variables (prefixed with `COSTCUTTER_`)
7. Runtime overrides (CLI flags like `--dry-run` or Python API `overrides` parameter)

Later sources override earlier ones. Nested keys are merged so you can set only the fields you care about. **All values are validated with Pydantic** - type errors, constraint violations, and unknown fields cause immediate failure with detailed error messages.

See [Configuration Reference](./config-reference.md) for complete details on precedence, validation, and all available options.

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
