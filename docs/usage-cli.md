# CostCutter CLI

This guide explains how to run the CostCutter command line interface, what each option does, and how to interpret the Rich output.

## Running the Command

- Installed package: `costcutter [OPTIONS]`
- Module execution: `python -m costcutter.cli [OPTIONS]`
- Temporary run with uv: `uvx costcutter [OPTIONS]`

All modes expose the same options.

## Available Options

| Flag | Description |
| ---- | ----------- |
| `--dry-run` | Force dry run mode even if the config disables it. |
| `--no-dry-run` | Disable dry run for the current invocation. |
| `--config PATH` | Load an explicit YAML, YML, TOML, or JSON file. |

Dry run is enabled by default through `src/costcutter/conf/config.yaml`. Use `--no-dry-run` only when you intend to delete resources.

## Typical Workflows

### Show help

```sh
uvx costcutter --help
```

### Preview deletions (default)

```sh
uvx costcutter --dry-run --config ./costcutter.yaml
```

### Execute a cleanup

```sh
uvx costcutter --no-dry-run --config ./costcutter.yaml
```

### Use the default config and overrides from the home directory

```sh
costcutter --dry-run
```

When `--config` is omitted the loader merges the bundled defaults, any `~/.costcutter.*` file, environment variables with the `COSTCUTTER_` prefix, and the CLI flags shown above.

## What You Will See

- A Rich powered live table that tails the most recent events recorded by the reporter
- A Rich summary table once orchestration finishes or is interrupted
- A message pointing to the CSV export if `reporting.csv.enabled` is true in the merged configuration

Logs are written to the directory from `logging.dir` when logging is enabled. The CLI itself does not print raw log records.

## Troubleshooting Basics

- Invalid file extensions on `--config` raise a Typer validation error before the run starts
- Keyboard interrupts stop orchestration gracefully and still show a final summary
- Enable debug logs by setting `logging.level` to `DEBUG` in the config or via `COSTCUTTER_LOGGING__LEVEL=DEBUG`

Consult [Troubleshooting](/guide/troubleshooting.md) for deeper diagnostics and escalation paths.
