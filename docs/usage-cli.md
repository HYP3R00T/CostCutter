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
| `--config PATH` | Load an explicit config file (YAML/TOML/JSON/YML). |

Dry run is enabled by default (`dry_run: true` in config). Use `--no-dry-run` only when you intend to delete resources.

## Typical Workflows

### Show help

```sh
uvx costcutter --help
```

### Preview deletions (default)

```sh
# Uses auto-discovered config or defaults
uvx costcutter

# Or explicitly enable dry-run
uvx costcutter --dry-run
```

### Execute a cleanup

```sh
uvx costcutter --no-dry-run
```

### Use custom config file location

```sh
# Use an explicit config file path
uvx costcutter --config /path/to/production.yaml

# Auto-discovery still works
uvx costcutter  # Uses ./costcutter.yaml or ~/.config/costcutter/costcutter.yaml
```

Configuration is automatically discovered from multiple locations using [utilityhub_config](https://utilityhub.hyperoot.dev/packages/utilityhub_config/). See [Configuration Reference](./guide/config-reference.md) for precedence order and all options.

## What You Will See

- A Rich powered live table that tails the most recent events recorded by the reporter
- A Rich summary table once orchestration finishes or is interrupted
- A message pointing to the CSV export if `reporting.csv.enabled` is true in the merged configuration

Logs are written to the directory from `logging.dir` when logging is enabled. The CLI itself does not print raw log records.

## Troubleshooting Basics

- **Configuration validation errors** - Invalid config (wrong types, constraint violations, duplicate regions/services, unknown fields) causes immediate failure with detailed error messages showing field path, error type, and checked files. See [Configuration Reference](./guide/config-reference.md#common-validation-errors) for examples.
- **File discovery** - Config files are auto-discovered from `~/.config/costcutter/`, `./`, and `./config/`. Old locations (`~/.costcutter.*`) are not supported.
- **Keyboard interrupts** - Stop orchestration gracefully and still show a final summary
- **Debug logs** - Enable by setting `logging.level: DEBUG` in config or via `COSTCUTTER_LOGGING__LEVEL=DEBUG`
- **Region warnings** - Unknown AWS regions generate warnings but execution continues (forward compatibility)

Consult [Troubleshooting](./guide/troubleshooting.md) for deeper diagnostics and escalation paths.
