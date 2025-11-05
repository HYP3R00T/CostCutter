# Getting Started with CostCutter

This walkthrough shows how to install the CLI, create a configuration file, and run your first dry run.

## 1. Install the tooling

CostCutter targets Python 3.13 or newer. The examples below use [uv](https://docs.astral.sh/uv/) to avoid managing a virtual environment manually.

```sh
curl -Ls https://astral.sh/uv/install.sh | sh
uv tool install costcutter
```

Verify the command is on your `PATH`:

```sh
costcutter --help
```

If you prefer an ephemeral run, skip the `uv tool install` step and use `uvx costcutter` in the following commands.

## 2. Create a configuration file

CostCutter loads settings from several locations but a dedicated file makes the first run predictable. Save the following YAML to `costcutter.yaml`:

```yaml
dry_run: true
logging:
  enabled: true
  level: INFO
  dir: ~/.local/share/costcutter/logs
reporting:
  csv:
    enabled: true
    path: ~/.local/share/costcutter/reports/events.csv
aws:
  profile: default
  region:
    - us-east-1
    - ap-south-1
  services:
    - ec2
    - s3
```

Adjust the regions or services to match the parts of AWS you want to scan. Leave `dry_run` set to `true` until you are comfortable with the output.

## 3. Run a dry run

```sh
costcutter --dry-run --config ./costcutter.yaml
```

The CLI clears the terminal, shows a banner, and then streams the most recent events in a table. Because the run is a dry run, the AWS APIs are queried with `DryRun` semantics or the handlers exit before deletion. The summary table at the end lists how many tasks succeeded, failed, or were skipped.

## 4. Execute for real (optional)

After reviewing the dry run output you can launch a destructive run:

```sh
costcutter --no-dry-run --config ./costcutter.yaml
```

This command removes every supported resource that matches the configuration. Use it only in accounts where deletion is acceptable.

## Next steps
