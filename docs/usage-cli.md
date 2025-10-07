# costcutter CLI Usage Guide

This guide explains how to use the costcutter command-line interface (CLI) for AWS resource cleanup, including available flags, config file usage, output interpretation, and troubleshooting.

## Running the CLI

You can run the CLI using Python:

```sh
python -m costcutter.cli [OPTIONS]
```

Or, if installed as a package:

```sh
costcutter [OPTIONS]
```

Or using `uvx`:

```sh
uvx costcutter [OPTIONS]
```

## Common Flags and Options

| Flag / Option   | Description                                               |
| --------------- | --------------------------------------------------------- |
| `--help`        | Show help message and exit.                               |
| `--dry-run`     | Simulate actions without making changes to AWS resources. |
| `--config PATH` | Specify a custom config file path (YAML, TOML, JSON).     |

**Note:** If no config is provided, defaults are used. Dry-run is enabled by default for safety.

## Example Usage

**Show help:**

```sh
uvx costcutter --help
```

**Run in dry-run mode:**

```sh
uvx costcutter --dry-run
```

**Specify config file:**

```sh
uvx costcutter --config config.yaml
```

**Run in execute mode:**

```sh
uvx costcutter --dry-run false --config config.yaml
```

## Config File Usage

You can pass a config file to customize regions, services, and reporting. Supported formats: YAML, TOML, JSON.

Example:

```sh
uvx costcutter --config myconfig.yaml
```

## Output Interpretation

- **Live Event Table:** Shows recent AWS resource events (service, resource, action, region, etc.)
- **Summary Table:** Aggregated count of actions performed
- **CSV Export:** If enabled in config, events are saved to CSV after run

## Error Handling & Troubleshooting

- Invalid config file extension will raise an error (must be .yaml, .yml, .toml, or .json)
- All exceptions are logged and reported in the console
- KeyboardInterrupt (Ctrl+C) will gracefully stop the orchestrator and show a summary

## Advanced Usage

- Use custom config files for different environments
- Integrate with CI/CD for automated cleanup
- Review logs for detailed event info (see `logs/` directory)

---

For more help, see [Troubleshooting & FAQ](/guide/troubleshooting).

```sh
python -m costcutter.cli --config /path/to/config.yaml
```

## Notes

- Only `--dry-run` and `--config` are supported as CLI flags.
- All other configuration (regions, services, logging, reporting, etc.) must be set in the config file (`src/costcutter/conf/config.yaml`).
- For a full list of options, run:
  ```sh
  python -m costcutter.cli --help
  ```

---

For more details, see the main documentation or source code in `src/costcutter/cli.py`.
