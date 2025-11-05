# Configuration Reference

Complete guide to configuring CostCutter.

## Configuration Hierarchy

CostCutter merges configuration from multiple sources in this order (later sources override earlier ones):

1. **Default Config** - Built-in defaults (`src/costcutter/conf/config.yaml`)
2. **Home Config** - User's home directory (`~/.costcutter.{yaml,yml,toml,json}`)
3. **Explicit File** - File specified via `--config` flag or `config_file` parameter
4. **Environment Variables** - Shell environment variables with `COSTCUTTER_` prefix
5. **CLI Arguments** - Command-line flags (highest priority)

**Partial overrides are supported:** You only need to specify the values you want to change. Unspecified values are inherited from lower priority sources.

## Configuration Methods

### Method 1: Default Configuration (Built-in)

Located at `src/costcutter/conf/config.yaml`. Used automatically if no other config is provided.

**Default Configuration:**

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
  aws_access_key_id: ""
  aws_secret_access_key: ""
  aws_session_token: ""
  credential_file_path: ~/.aws/credentials
  max_workers: 4
  region:
    - us-east-1
    - ap-south-1
  services:
    - ec2
    - s3
```

**This is the baseline.** All other configuration methods override these defaults.

### Method 2: Home Directory Config

Create a config file in your home directory:

**Supported formats:**

- `~/.costcutter.yaml`
- `~/.costcutter.yml`
- `~/.costcutter.toml`
- `~/.costcutter.json`

**Example (`~/.costcutter.yaml`):**

```yaml
# Override only what you need
aws:
  region:
    - us-west-2
    - eu-west-1
  services:
    - ec2
    - s3
```

**Result:** Regions and services are overridden. Other settings (dry_run, logging, etc.) use defaults.

**TOML Example (`~/.costcutter.toml`):**

```toml
dry_run = false

[aws]
region = ["us-east-1", "us-west-2"]
services = ["ec2", "s3"]
```

**JSON Example (`~/.costcutter.json`):**

```json
{
  "dry_run": false,
  "aws": {
    "region": ["us-east-1"],
    "services": ["ec2"]
  }
}
```

### Method 3: Explicit Config File

Specify a config file when running CostCutter:

**CLI:**

```bash
costcutter --config /path/to/myconfig.yaml
```

**Python API:**

```python
from pathlib import Path
from costcutter.conf.config import get_config

config = get_config(config_file=Path("/path/to/myconfig.yaml"))
```

**Supported formats:** `.yaml`, `.yml`, `.toml`, `.json`

**Example (`myconfig.yaml`):**

```yaml
dry_run: false
aws:
  profile: production
  region:
    - us-east-1
  services:
    - ec2
```

**Priority:** Overrides both defaults and home directory config.

### Method 4: Environment Variables

Set environment variables with `COSTCUTTER_` prefix.

**Syntax:**

- Use double underscore (`__`) for nesting
- Variable names are case-insensitive
- Values are automatically parsed (YAML parser used for type coercion)

**Examples:**

```bash
# Override dry_run
export COSTCUTTER_DRY_RUN=false

# Override AWS region (YAML list syntax)
export COSTCUTTER_AWS__REGION="[us-west-2, eu-central-1]"

# Override logging level
export COSTCUTTER_LOGGING__LEVEL=DEBUG

# Override single nested value
export COSTCUTTER_AWS__PROFILE=staging

# Run costcutter
costcutter
```

**Type Coercion Examples:**

```bash
export COSTCUTTER_DRY_RUN=true          # Boolean
export COSTCUTTER_AWS__MAX_WORKERS=8    # Integer
export COSTCUTTER_LOGGING__LEVEL=DEBUG  # String
export COSTCUTTER_AWS__SERVICES="[ec2, s3]"  # List
```

**Python API:**

```python
import os
from costcutter.conf.config import get_config

os.environ["COSTCUTTER_DRY_RUN"] = "false"
os.environ["COSTCUTTER_AWS__REGION"] = "[us-east-1]"

config = get_config()
```

**Priority:** Overrides defaults, home config, and explicit files. Only CLI arguments have higher priority.

### Method 5: CLI Arguments

Pass arguments directly via command line:

```bash
# Override dry_run
costcutter --dry-run

# Combine with config file
costcutter --config myconfig.yaml --dry-run
```

**Available CLI Arguments:**

- `--dry-run` / `--no-dry-run` - Enable or disable dry-run mode
- `--config PATH` - Specify config file

**Python API:**

```python
from costcutter.conf.config import get_config

cli_overrides = {
    "dry_run": False,
    "aws": {
        "region": ["us-east-1"]
    }
}

config = get_config(cli_args=cli_overrides)
```

**Priority:** Highest priority. Overrides all other sources.

## Using CostCutter as a Python Package

Import and configure programmatically:

### Basic Usage

```python
from costcutter.conf.config import get_config
from costcutter.orchestrator import orchestrate_services

# Load default config
config = get_config()

# Run cleanup
orchestrate_services(dry_run=True)
```

### Custom Configuration

```python
from pathlib import Path
from costcutter.conf.config import get_config

# Method 1: Use config file
config = get_config(config_file=Path("./myconfig.yaml"))

# Method 2: Override via CLI args
config = get_config(cli_args={
    "dry_run": False,
    "aws": {
        "region": ["us-west-2"],
        "services": ["ec2", "s3"]
    }
})

# Method 3: Combine both
config = get_config(
    config_file=Path("./base.yaml"),
    cli_args={"dry_run": False}
)
```

### Reload Configuration

```python
from costcutter.conf.config import reload_config

# Reload with new settings
config = reload_config(cli_args={"dry_run": False})
```

### Access Configuration Values

```python
config = get_config()

# Dot notation
print(config.dry_run)
print(config.aws.region)
print(config.logging.level)

# Dictionary notation
print(config["dry_run"])
print(config["aws"]["region"])

# Convert to dict
config_dict = config.to_dict()
print(config_dict["aws"]["services"])
```

## Configuration Options Reference

### Top-Level

#### `dry_run`

- **Type:** `boolean`
- **Default:** `true`
- **Description:** When `true`, simulates actions without making changes. When `false`, actually deletes resources.
- **CLI:** `--dry-run` / `--no-dry-run`

**Examples:**

```yaml
dry_run: true  # Safe mode (default)
```

```bash
export COSTCUTTER_DRY_RUN=false
```

### Logging Section

#### `logging.enabled`

- **Type:** `boolean`
- **Default:** `true`
- **Description:** Enable or disable file-based logging.

#### `logging.level`

- **Type:** `string`
- **Default:** `INFO`
- **Options:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description:** Log verbosity level.

#### `logging.dir`

- **Type:** `string` (path)
- **Default:** `~/.local/share/costcutter/logs`
- **Description:** Directory where log files are written. Supports `~` expansion.

**Examples:**

```yaml
logging:
  enabled: true
  level: DEBUG
  dir: /var/log/costcutter
```

```bash
export COSTCUTTER_LOGGING__ENABLED=true
export COSTCUTTER_LOGGING__LEVEL=DEBUG
export COSTCUTTER_LOGGING__DIR=/tmp/logs
```

### Reporting Section

#### `reporting.csv.enabled`

- **Type:** `boolean`
- **Default:** `true`
- **Description:** Enable CSV export of all events.

#### `reporting.csv.path`

- **Type:** `string` (path)
- **Default:** `~/.local/share/costcutter/reports/events.csv`
- **Description:** Path where CSV report is saved. Supports `~` expansion.

**Examples:**

```yaml
reporting:
  csv:
    enabled: true
    path: ./reports/cleanup-2025-11-05.csv
```

```bash
export COSTCUTTER_REPORTING__CSV__ENABLED=true
export COSTCUTTER_REPORTING__CSV__PATH=./events.csv
```

### AWS Section

#### `aws.profile`

- **Type:** `string`
- **Default:** `default`
- **Description:** AWS CLI profile name from `~/.aws/credentials`.

#### `aws.aws_access_key_id`

- **Type:** `string`
- **Default:** `""` (empty)
- **Description:** AWS access key ID. Leave empty to use credentials file or IAM role.

#### `aws.aws_secret_access_key`

- **Type:** `string`
- **Default:** `""` (empty)
- **Description:** AWS secret access key. Leave empty to use credentials file or IAM role.

#### `aws.aws_session_token`

- **Type:** `string`
- **Default:** `""` (empty)
- **Description:** AWS session token (optional, for temporary credentials).

#### `aws.credential_file_path`

- **Type:** `string` (path)
- **Default:** `~/.aws/credentials`
- **Description:** Path to AWS credentials file.

#### `aws.max_workers`

- **Type:** `integer`
- **Default:** `4`
- **Description:** Number of parallel workers for orchestrator-level concurrency (regions + services).

#### `aws.region`

- **Type:** `list[string]`
- **Default:** `[us-east-1, ap-south-1]`
- **Description:** AWS regions to process. Specify multiple regions for parallel cleanup.

#### `aws.services`

- **Type:** `list[string]`
- **Default:** `[ec2, s3]`
- **Description:** AWS services to process. The repository ships with `ec2` and `s3` handlers; include additional service names as you add new cleanup functions.

**Examples:**

```yaml
aws:
  profile: production
  region:
    - us-east-1
    - us-west-2
    - eu-west-1
  services:
    - ec2
    - s3
  max_workers: 8
```

```bash
export COSTCUTTER_AWS__PROFILE=staging
export COSTCUTTER_AWS__REGION="[us-west-2, eu-central-1]"
export COSTCUTTER_AWS__SERVICES="[ec2, s3]"
export COSTCUTTER_AWS__MAX_WORKERS=6
```

## Complete Configuration Examples

### Example 1: Development (Dry-Run)

```yaml
# ~/.costcutter.yaml
dry_run: true

logging:
  level: DEBUG
  dir: ./logs

aws:
  profile: dev
  region:
    - us-east-1
  services:
    - ec2
```

**Usage:**

```bash
costcutter  # Uses home config
```

### Example 2: Production (Execute)

```yaml
# production.yaml
dry_run: false

logging:
  level: INFO
  dir: /var/log/costcutter

reporting:
  csv:
    path: /var/reports/cleanup-$(date +%Y%m%d).csv

aws:
  profile: production
  region:
    - us-east-1
    - us-west-2
    - eu-west-1
  services:
    - ec2
    - s3
  max_workers: 10
```

**Usage:**

```bash
costcutter --config production.yaml
```

### Example 3: Environment Variables Only

```bash
#!/bin/bash
# cleanup.sh

export COSTCUTTER_DRY_RUN=false
export COSTCUTTER_AWS__PROFILE=prod
export COSTCUTTER_AWS__REGION="[us-east-1, us-west-2]"
export COSTCUTTER_AWS__SERVICES="[ec2, s3]"
export COSTCUTTER_LOGGING__LEVEL=INFO

costcutter
```

### Example 4: Python Script

```python
# cleanup.py
from pathlib import Path
from costcutter.conf.config import get_config
from costcutter.orchestrator import orchestrate_services
from costcutter.logger import setup_logging

# Load configuration
config = get_config(
    config_file=Path("./config.yaml"),
    cli_args={
        "dry_run": False,
        "aws": {
            "region": ["us-east-1"],
            "services": ["ec2"]
        }
    }
)

# Setup logging
setup_logging(config)

# Run cleanup
orchestrate_services(dry_run=False)
```

### Example 5: Minimal Override

You only need to specify what you want to change:

```yaml
# minimal.yaml
aws:
  region:
    - eu-central-1
```

**Result:** Only region is overridden. All other settings use defaults:

- `dry_run: true` (default)
- `logging.level: INFO` (default)
- `aws.services: [ec2, s3]` (default)
- etc.

## Precedence Example

Given these configurations:

**1. Default (`config.yaml`):**

```yaml
dry_run: true
aws:
  region: [us-east-1]
  services: [ec2, s3]
```

**2. Home (`~/.costcutter.yaml`):**

```yaml
aws:
  region: [us-west-2]
```

**3. Explicit (`myconfig.yaml`):**

```yaml
aws:
  services: [ec2]
```

**4. Environment:**

```bash
export COSTCUTTER_DRY_RUN=false
```

**5. CLI:**

```bash
costcutter --config myconfig.yaml --dry-run
```

**Final merged configuration:**

```yaml
dry_run: true              # From CLI (highest priority)
aws:
  region: [us-west-2]      # From home config
  services: [ec2]          # From explicit file
  # Other aws.* values from defaults
```

## Validation

CostCutter validates configuration at startup:

- **Config file format** - Must be `.yaml`, `.yml`, `.toml`, or `.json`
- **Required fields** - All required fields must have values
- **Type checking** - Values must match expected types

**Invalid config example:**

```bash
costcutter --config myconfig.txt
# Error: Config file must be one of: .yaml, .yml, .toml, .json
```

## Troubleshooting

### Configuration not taking effect

**Check precedence order:**

1. Verify which config sources are active
2. Higher priority sources override lower ones
3. Use `DEBUG` logging to see loaded values

**Debug configuration:**

```python
from costcutter.conf.config import get_config

config = get_config()
print(config.to_dict())  # See final merged config
```

### Environment variables not working

**Ensure correct syntax:**

- Prefix: `COSTCUTTER_`
- Nesting: Use `__` (double underscore)
- Case: Insensitive (but uppercase recommended)

**Test:**

```bash
export COSTCUTTER_DRY_RUN=false
python -c "import os; from costcutter.conf.config import get_config; print(get_config().dry_run)"
# Should print: False
```

### Home config ignored

**Check file exists and has correct extension:**

```bash
ls -la ~/.costcutter.*
```

Supported: `.yaml`, `.yml`, `.toml`, `.json`

## Next Steps

- [How It Works](./how-it-works.md) - Understand execution flow
- [Getting Started](./getting-started.md) - Quick start guide
- [Troubleshooting](./troubleshooting.md) - Common issues
