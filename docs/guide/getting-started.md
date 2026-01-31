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

## 2. Create a configuration file (optional)

CostCutter loads settings from multiple sources automatically using [utilityhub_config](https://utilityhub.hyperoot.dev/packages/utilityhub_config/). You can run it immediately with defaults, or create a configuration file for customization.

**Quick start with defaults:**

```sh
# Uses built-in defaults (dry_run=true, regions=[us-east-1, ap-south-1], services=[ec2, s3])
costcutter
```

**Or create a custom config file:**

Save the following YAML to `costcutter.yaml` in your current directory:

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
    - us-west-2
  services:
    - ec2
    - s3
  max_workers: 8
```

**Configuration locations (auto-discovered in order):**

1. Global config: `~/.config/costcutter/costcutter.yaml`
2. Project config: `./costcutter.yaml` or `./config/costcutter.yaml`
3. Environment variables: `COSTCUTTER_*`
4. Runtime overrides: `--dry-run` flags

You only need to specify values you want to change—unspecified values use defaults. See [Configuration Reference](./config-reference.md) for all options and validation rules.

## 3. Run a dry run

```sh
# Uses auto-discovered config or defaults
costcutter

# Or explicitly specify dry-run mode
costcutter --dry-run

# Or with explicit config file
costcutter --config ./costcutter.yaml
```

The CLI clears the terminal, shows a banner, and then streams the most recent events in a table. Because `dry_run: true` is the default, AWS APIs are queried with `DryRun` semantics or handlers exit before deletion. The summary table at the end lists how many tasks succeeded, failed, or were skipped.

**Validation happens automatically** - if your configuration has errors (invalid regions, wrong types, constraint violations), CostCutter fails immediately with detailed error messages before making any AWS API calls.

## 4. Execute for real (optional)

After reviewing the dry run output you can launch a destructive run:

```sh
costcutter --no-dry-run
```

Or with explicit config:

```sh
costcutter --no-dry-run --config ./costcutter.yaml
```

Or via environment variable:

```sh
export COSTCUTTER_DRY_RUN=false
costcutter
```

**⚠️ Warning:** This command removes every supported resource that matches the configuration. Use it only in accounts where deletion is acceptable.

## Next steps
