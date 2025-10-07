# Getting Started with `costcutter`

This guide will help you quickly run CostCutter to clean up AWS resources.

## Quick Start

1. **Install uv (required):**

   ```sh
   curl -Ls https://astral.sh/uv/install.sh | sh
   uv --version
   ```

   For more details, see [Installing uv](https://docs.astral.sh/uv/getting-started/installation/).

2. **Run CostCutter:**

   ```sh
   uvx costcutter --help
   uvx costcutter --dry-run --config config.yaml
   ```

## Configuration

CostCutter requires a configuration file to define regions, services, and reporting options. Create a file in YAML, TOML, or JSON format.

**Example config:**

::: code-group

```yaml
dry_run: true
regions:
  - us-east-1
services:
  - ec2
  - s3
reporting:
  csv:
    enabled: true
    path: ./events.csv
```

```json
{
  "dry_run": true,
  "regions": ["us-east-1"],
  "services": ["ec2", "s3"],
  "reporting": {
    "csv": {
      "enabled": true,
      "path": "./events.csv"
    }
  }
}
```

```toml
dry_run = true
regions = ["us-east-1"]
services = ["ec2", "s3"]

[reporting.csv]
enabled = true
path = "./events.csv"
```

:::

## What to Expect

- **Live Event Table:** Displays AWS resource actions (service, resource, action, region, etc.).
- **Summary Table:** Shows a summary of actions performed.
- **CSV Export:** If enabled, events are saved to a CSV file.

By default, CostCutter runs in dry-run mode for safety. No changes are made to AWS resources unless you disable dry-run.

---

**Next Steps:**

- Learn about advanced flags and options in [Usage (CLI)](/usage-cli).
- Review supported AWS services in [Supported Services & Resources](/guide/supported-services).
