# Configuration Reference

Complete guide to configuring CostCutter with type-safe validation powered by [utilityhub_config](https://utilityhub.hyperoot.dev/packages/utilityhub_config/).

## Configuration Hierarchy

CostCutter uses [utilityhub_config](https://utilityhub.hyperoot.dev/packages/utilityhub_config/) to load and validate configuration from multiple sources. Settings are resolved with strict precedence from lowest to highest priority:

1. **Defaults** - Field defaults from Pydantic models (defined in [config.py](../../src/costcutter/config.py#L198-L227))
2. **Global Config** - User's home directory (`~/.config/costcutter/costcutter.{yaml,toml}`)
3. **Project Config** - Current directory (`./costcutter.{yaml,toml}` or `./config/*.{yaml,toml}`)
4. **Explicit Config File** - Path passed via `--config` (optional)
5. **Dotenv** - Environment variables from `.env` file in current directory
6. **Environment Variables** - Shell environment variables with `COSTCUTTER_` prefix
7. **Runtime Overrides** - Passed via `overrides` parameter or CLI flags (highest priority)

**Higher levels override lower levels.** Only sources that exist are consulted. Partial overrides are fully supported—you only need to specify values you want to change.

## Validation & Type Safety

CostCutter enforces strict validation at configuration load time using [Pydantic v2](https://docs.pydantic.dev/). **Invalid configurations fail immediately** with detailed error messages—no resources are modified if configuration is invalid.

### Validation Rules

**All configuration values are validated for:**

- **Type correctness** - Values must match declared types (int, str, bool, list)
- **Constraints** - Numeric bounds, string lengths, list sizes enforced
- **Literal types** - Restricted values (e.g., logging level must be DEBUG/INFO/WARNING/ERROR/CRITICAL)
- **Custom validators** - Duplicate detection, AWS region warnings
- **Extra fields** - Unknown fields in config files are rejected (catches typos)

### Validation Examples

**❌ Invalid Configurations (will fail):**

```yaml
# Error: max_workers must be >= 1 and <= 100
aws:
  max_workers: 0
```

```yaml
# Error: Literal type - must be DEBUG/INFO/WARNING/ERROR/CRITICAL
logging:
  level: TRACE
```

```yaml
# Error: Duplicate regions not allowed
aws:
  region:
    - us-east-1
    - us-east-1
```

```yaml
# Error: services list cannot be empty
aws:
  services: []
```

```yaml
# Error: Unknown field (typo detection)
aws:
  regions: [us-east-1]  # Should be 'region' (singular)
```

**✅ Valid Configurations:**

```yaml
# All constraints satisfied
aws:
  max_workers: 8
  region:
    - us-east-1
    - us-west-2
  services:
    - ec2
    - s3

logging:
  level: INFO
```

### AWS Region Validation

CostCutter validates AWS regions against **34 official regions**:

**US Regions (4):**
`us-east-1`, `us-east-2`, `us-west-1`, `us-west-2`

**Asia Pacific (14):**
`ap-east-1`, `ap-east-2`, `ap-south-1`, `ap-south-2`, `ap-southeast-1`, `ap-southeast-2`, `ap-southeast-3`, `ap-southeast-4`, `ap-southeast-5`, `ap-southeast-6`, `ap-southeast-7`, `ap-northeast-1`, `ap-northeast-2`, `ap-northeast-3`

**Canada (2):**
`ca-central-1`, `ca-west-1`

**Europe (8):**
`eu-central-1`, `eu-central-2`, `eu-west-1`, `eu-west-2`, `eu-west-3`, `eu-north-1`, `eu-south-1`, `eu-south-2`

**Other (6):**
`me-south-1`, `me-central-1`, `sa-east-1`, `af-south-1`, `il-central-1`, `mx-central-1`

**⚠️ Unknown regions generate warnings but don't fail:**

```yaml
aws:
  region:
    - us-future-1  # Warning: Unknown AWS region, but accepted
```

This preserves forward compatibility for newly released AWS regions.

**Special value `all`** is supported for region discovery:

```yaml
aws:
  region:
    - all  # Automatically discovers available regions
```

Reference: [AWS Regions Documentation](https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html)

### Error Messages

When validation fails, you get detailed error messages with:

- **Field path** - Exact location of invalid value
- **Error type** - What validation failed
- **Expected value** - What the field should contain
- **Source information** - Which file/env var caused the error
- **Checked files** - All config files searched
- **Precedence chain** - How values were merged

**Example error output:**

```
ConfigValidationError: Configuration validation failed

2 validation errors for Config
aws.max_workers
  Input should be greater than or equal to 1 [type=greater_than_equal]
logging.level
  Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL' [type=literal_error]

Checked files:
  - ~/.config/costcutter/costcutter.yaml (found)
  - ./costcutter.yaml (not found)

Precedence: defaults → global → project → explicit → dotenv → env → overrides
```



## Configuration Methods

### Method 1: Default Configuration (Built-in)

Defined in [config.py](../../src/costcutter/config.py). Used automatically if no other config is provided.

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
  resource_max_workers: 4
  region:
    - us-east-1
    - ap-south-1
  services:
    - ec2
    - s3
```

**This is the baseline.** All other configuration methods override these defaults.

### Method 2: Global Config (Home Directory)

Create a config file in your home directory:

**Location:** `~/.config/costcutter/costcutter.{yaml,toml}`

**Example (`~/.config/costcutter/costcutter.yaml`):**

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

**TOML Example (`~/.config/costcutter/costcutter.toml`):**

```toml
dry_run = false

[aws]
region = ["us-east-1", "us-west-2"]
services = ["ec2", "s3"]
max_workers = 8
```

### Method 3: Project Config (Current Directory)

Create a config file in your project directory:

**Locations (checked in order):**
- `./costcutter.yaml`
- `./costcutter.toml`
- `./config/costcutter.yaml`
- `./config/costcutter.toml`

**Example (`./costcutter.yaml`):**

```yaml
dry_run: false
aws:
  profile: production
  region:
    - us-east-1
  services:
    - ec2
```

**Priority:** Overrides defaults and global config.

### Method 4: Explicit Config File

Provide a direct config file path via `--config`:

```bash
costcutter --config /path/to/production.yaml
```

**Supported formats:** `.yaml`, `.yml`, `.toml`, `.json`

**Example (`production.yaml`):**

```yaml
dry_run: false
aws:
  profile: production
  region:
    - us-east-1
  services:
    - ec2
  max_workers: 10
```

**Priority:** Overrides defaults, global config, and project config. Lower priority than dotenv/env/overrides.

### Method 5: Dotenv File

Create a `.env` file in your current directory:

**Example (`.env`):**

```bash
COSTCUTTER_DRY_RUN=false
COSTCUTTER_AWS__REGION=["us-east-1", "us-west-2"]
COSTCUTTER_AWS__SERVICES=["ec2", "s3"]
COSTCUTTER_LOGGING__LEVEL=DEBUG
```

**Priority:** Overrides defaults, global config, and project config.

### Method 6: Environment Variables

Set environment variables with `COSTCUTTER_` prefix.

**Syntax:**

- Use double underscore (`__`) for nesting
- Variable names are case-insensitive (uppercase recommended)
- Values are automatically parsed (YAML parser for type coercion)

**Examples:**

```bash
# Override dry_run
export COSTCUTTER_DRY_RUN=false

# Override AWS region (YAML list syntax)
export COSTCUTTER_AWS__REGION='["us-west-2", "eu-central-1"]'

# Override logging level
export COSTCUTTER_LOGGING__LEVEL=DEBUG

# Override nested value
export COSTCUTTER_AWS__PROFILE=staging

# Override max_workers
export COSTCUTTER_AWS__MAX_WORKERS=8

# Run costcutter
costcutter
```

**Type Coercion Examples:**

```bash
export COSTCUTTER_DRY_RUN=true               # Boolean
export COSTCUTTER_AWS__MAX_WORKERS=8         # Integer
export COSTCUTTER_LOGGING__LEVEL=DEBUG       # String (Literal)
export COSTCUTTER_AWS__SERVICES='["ec2", "s3"]'  # List
```

**Python API:**

```python
import os
from costcutter.config import load_config

os.environ["COSTCUTTER_DRY_RUN"] = "false"
os.environ["COSTCUTTER_AWS__REGION"] = '["us-east-1"]'

config = load_config()
```

**Priority:** Overrides defaults, global config, project config, and dotenv. Only runtime overrides have higher priority.

### Method 7: Runtime Overrides

Pass overrides directly via CLI or Python API:

**CLI (via flags):**

```bash
costcutter --dry-run
costcutter --no-dry-run
```

**Python API:**

```python
from costcutter.config import load_config

# Highest priority - overrides all other sources
config = load_config(overrides={
    "dry_run": False,
    "aws": {
        "region": ["us-east-1"],
        "services": ["ec2", "s3"],
        "max_workers": 10
    },
    "logging": {
        "level": "DEBUG"
    }
})
```

**Priority:** Highest priority. Overrides all other sources including environment variables.

## Using CostCutter as a Python Package

Import and configure programmatically:

### Basic Usage

```python
from costcutter.config import load_config
from costcutter.orchestrator import orchestrate_services

# Load default config
config = load_config()

# Run cleanup
orchestrate_services(dry_run=True)
```

### Custom Configuration

```python
from costcutter.config import load_config

# Method 1: Load with defaults (auto-discovers config files)
config = load_config()

# Method 2: Override via runtime parameters
config = load_config(overrides={
    "dry_run": False,
    "aws": {
        "region": ["us-west-2"],
        "services": ["ec2", "s3"]
    }
})
```

### Reload Configuration

```python
from costcutter.config import load_config

# Reload with new settings
config = load_config(overrides={"dry_run": False})
```

### Access Configuration Values

```python
config = load_config()

# Dot notation
print(config.dry_run)
print(config.aws.region)
print(config.logging.level)

# Convert to dict
config_dict = config.model_dump()
print(config_dict["aws"]["services"])
```

## Configuration Options Reference

### Top-Level

#### `dry_run`

- **Type:** `bool`
- **Default:** `true`
- **Description:** When `true`, simulates actions without making changes. When `false`, actually deletes resources.
- **CLI:** `--dry-run` / `--no-dry-run`
- **Validation:** Must be boolean

**Examples:**

```yaml
dry_run: true  # Safe mode (default)
```

```bash
export COSTCUTTER_DRY_RUN=false
```

### Logging Section

#### `logging.enabled`

- **Type:** `bool`
- **Default:** `true`
- **Description:** Enable or disable file-based logging to capture events, errors, and execution history. Logs help with debugging and audit trails.
- **Validation:** Must be boolean

#### `logging.level`

- **Type:** `Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]`
- **Default:** `INFO`
- **Description:** Log verbosity level. Use DEBUG for detailed output during development, INFO for normal operation, WARNING/ERROR for production environments.
- **Validation:** Must be exactly one of: DEBUG, INFO, WARNING, ERROR, CRITICAL (case-sensitive)

#### `logging.dir`

- **Type:** `str` (path)
- **Default:** `~/.local/share/costcutter/logs`
- **Description:** Directory path for log files. Logs are organized by date and rotated automatically. Supports `~` expansion for home directory.
- **Validation:** Must be non-empty string

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

- **Type:** `bool`
- **Default:** `true`
- **Description:** Enable CSV export of all events (resources scanned, actions taken, errors). Useful for auditing and record-keeping.
- **Validation:** Must be boolean

#### `reporting.csv.path`

- **Type:** `str` (path)
- **Default:** `~/.local/share/costcutter/reports/events.csv`
- **Description:** File path where CSV report is saved. Appends to existing file if present. Supports `~` expansion for home directory.
- **Validation:** Must be non-empty string

**Examples:**

```yaml
reporting:
  csv:
    enabled: true
    path: ./reports/cleanup-2025-01-31.csv
```

```bash
export COSTCUTTER_REPORTING__CSV__ENABLED=true
export COSTCUTTER_REPORTING__CSV__PATH=./events.csv
```

### AWS Section

#### `aws.profile`

- **Type:** `str`
- **Default:** `default`
- **Description:** AWS CLI profile name from `~/.aws/credentials`. Use different profiles for dev/staging/production environments.
- **Validation:** Must be non-empty string

#### `aws.aws_access_key_id`

- **Type:** `str`
- **Default:** `""` (empty)
- **Description:** AWS access key ID. Leave empty to use credentials file, IAM role, or profile. Explicit credentials take precedence over other methods.
- **Validation:** Must be string (can be empty)

#### `aws.aws_secret_access_key`

- **Type:** `str`
- **Default:** `""` (empty)
- **Description:** AWS secret access key. Leave empty to use credentials file, IAM role, or profile. Should match aws_access_key_id if provided.
- **Validation:** Must be string (can be empty)

#### `aws.aws_session_token`

- **Type:** `str`
- **Default:** `""` (empty)
- **Description:** AWS session token for temporary security credentials (STS, SSO). Optional, only required for temporary credentials.
- **Validation:** Must be string (can be empty)

#### `aws.credential_file_path`

- **Type:** `str` (path)
- **Default:** `~/.aws/credentials`
- **Description:** Path to AWS credentials file. Supports `~` expansion. Used when explicit keys are not provided.
- **Validation:** Must be non-empty string

#### `aws.max_workers`

- **Type:** `int`
- **Default:** `4`
- **Description:** Number of parallel workers for orchestrator-level concurrency (regions + services). Higher values speed up processing but increase AWS API load. Recommended: 4-10 for normal use, up to 20 for large-scale cleanup.
- **Validation:** Must be integer between 1 and 100 (inclusive)
- **Constraints:** `ge=1, le=100`

#### `aws.resource_max_workers`

- **Type:** `int`
- **Default:** `4`
- **Description:** Number of parallel workers for resource-level operations within each service handler. Controls concurrency when processing individual resources. Higher values increase throughput but may hit API rate limits.
- **Validation:** Must be integer between 1 and 100 (inclusive)
- **Constraints:** `ge=1, le=100`

#### `aws.region`

- **Type:** `list[str]`
- **Default:** `["us-east-1", "ap-south-1"]`
- **Description:** List of AWS regions to process. CostCutter validates against 34 official AWS regions and warns about unknown regions (but still accepts them for forward compatibility). Use `["all"]` to auto-discover available regions. Regions are processed in parallel based on max_workers setting.
- **Validation:**
  - Must be list with at least 1 item (`min_length=1`)
  - No duplicate regions allowed (hard error)
  - Unknown regions generate warnings (not errors)
  - Special value `"all"` supported
- **Constraints:** `min_length=1`, no duplicates
- **Reference:** [AWS Regions Documentation](https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html)

**Supported regions:**
- US: us-east-1, us-east-2, us-west-1, us-west-2
- Asia Pacific: ap-east-1, ap-east-2, ap-south-1, ap-south-2, ap-southeast-1, ap-southeast-2, ap-southeast-3, ap-southeast-4, ap-southeast-5, ap-southeast-6, ap-southeast-7, ap-northeast-1, ap-northeast-2, ap-northeast-3
- Canada: ca-central-1, ca-west-1
- Europe: eu-central-1, eu-central-2, eu-west-1, eu-west-2, eu-west-3, eu-north-1, eu-south-1, eu-south-2
- Other: me-south-1, me-central-1, sa-east-1, af-south-1, il-central-1, mx-central-1

#### `aws.services`

- **Type:** `list[str]`
- **Default:** `["ec2", "s3"]`
- **Description:** List of AWS services to process. Service names must match handler names in `src/costcutter/services/`. The repository ships with ec2, s3, and elasticbeanstalk handlers. Add new services by implementing handlers following the existing pattern—no config changes needed.
- **Validation:**
  - Must be list with at least 1 item (`min_length=1`)
  - No duplicate services allowed (hard error)
  - Unknown services are accepted (runtime discovery from SERVICE_HANDLERS registry)
- **Constraints:** `min_length=1`, no duplicates

**Examples:**

```yaml
aws:
  profile: production
  max_workers: 8
  resource_max_workers: 6
  region:
    - us-east-1
    - us-west-2
    - eu-west-1
  services:
    - ec2
    - s3
    - elasticbeanstalk
```

```bash
export COSTCUTTER_AWS__PROFILE=staging
export COSTCUTTER_AWS__MAX_WORKERS=6
export COSTCUTTER_AWS__RESOURCE_MAX_WORKERS=8
export COSTCUTTER_AWS__REGION='["us-west-2", "eu-central-1"]'
export COSTCUTTER_AWS__SERVICES='["ec2", "s3"]'
```

## Complete Configuration Examples

### Example 1: Development (Dry-Run with Debug)

```yaml
# ~/.config/costcutter/costcutter.yaml
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
  max_workers: 4
```

**Usage:**

```bash
costcutter  # Auto-discovers global config
```

### Example 2: Production (Multi-Region Cleanup)

```yaml
# ./costcutter.yaml (project directory)
dry_run: false

logging:
  level: INFO
  dir: /var/log/costcutter

reporting:
  csv:
    path: /var/reports/cleanup-2025-01-31.csv

aws:
  profile: production
  region:
    - us-east-1
    - us-west-2
    - eu-west-1
  services:
    - ec2
    - s3
    - elasticbeanstalk
  max_workers: 10
  resource_max_workers: 8
```

**Usage:**

```bash
cd /path/to/project
costcutter  # Uses project config
```

### Example 3: Environment Variables Only

```bash
#!/bin/bash
# cleanup.sh

export COSTCUTTER_DRY_RUN=false
export COSTCUTTER_AWS__PROFILE=prod
export COSTCUTTER_AWS__REGION='["us-east-1", "us-west-2"]'
export COSTCUTTER_AWS__SERVICES='["ec2", "s3"]'
export COSTCUTTER_AWS__MAX_WORKERS=8
export COSTCUTTER_LOGGING__LEVEL=INFO

costcutter
```

### Example 4: Python Script with Validation

```python
# cleanup.py
from costcutter.config import load_config
from costcutter.orchestrator import orchestrate_services
from costcutter.logger import setup_logging
from utilityhub_config.errors import ConfigValidationError

try:
    # Load configuration with runtime overrides
    config = load_config(overrides={
        "dry_run": False,
        "aws": {
            "region": ["us-east-1"],
            "services": ["ec2", "s3"],
            "max_workers": 10
        },
        "logging": {
            "level": "DEBUG"
        }
    })

    # Setup logging
    setup_logging(config)

    # Run cleanup
    orchestrate_services(dry_run=config.dry_run)

except ConfigValidationError as e:
    print(f"Configuration error: {e}")
    # Error includes: validation errors, checked files, precedence chain
    exit(1)
```

### Example 5: Minimal Override with Dotenv

Create `.env` in your project directory:

```bash
# .env
COSTCUTTER_AWS__REGION=["eu-central-1", "eu-west-1"]
COSTCUTTER_LOGGING__LEVEL=WARNING
```

Create minimal project config:

```yaml
# costcutter.yaml
dry_run: false
```

**Result:**
- `dry_run: false` from project config
- `region: ["eu-central-1", "eu-west-1"]` from .env
- `logging.level: WARNING` from .env
- All other settings use defaults

### Example 6: Region Validation Warning

```yaml
# Config with future AWS region
aws:
  region:
    - us-east-1
    - us-future-1  # Not in current list, but accepted
```

**Output:**
```
UserWarning: Unknown AWS region(s): ['us-future-1'].
Known regions: ['af-south-1', 'ap-east-1', ..., 'us-west-2'].
If using a new AWS region, this warning can be ignored.
Some regions require opt-in: https://docs.aws.amazon.com/...
```

**Execution continues** - forward compatibility preserved.

## Precedence Example

Given these configurations:

**1. Defaults ([config.py](../../src/costcutter/config.py)):**

```yaml
dry_run: true
logging:
  level: INFO
aws:
  region: [us-east-1, ap-south-1]
  services: [ec2, s3]
  max_workers: 4
```

**2. Global (`~/.config/costcutter/costcutter.yaml`):**

```yaml
aws:
  region: [us-west-2]
  max_workers: 8
```

**3. Project (`./costcutter.yaml`):**

```yaml
dry_run: false
aws:
  services: [ec2]
```

**4. Explicit (`--config /path/to/explicit.yaml`):**

```yaml
aws:
  services: [s3]
```

**5. Dotenv (`.env`):**

```bash
COSTCUTTER_LOGGING__LEVEL=DEBUG
```

**6. Environment:**

```bash
export COSTCUTTER_AWS__MAX_WORKERS=12
```

**7. Runtime Overrides (Python):**

```python
config = load_config(overrides={"dry_run": True})
```

**Final merged configuration:**

```yaml
dry_run: true                       # From runtime overrides (highest)
logging:
  level: DEBUG                      # From dotenv
  enabled: true                     # From defaults
  dir: ~/.local/share/.../logs      # From defaults
aws:
  region: [us-west-2]               # From global config
  services: [s3]                    # From explicit config
  max_workers: 12                   # From environment
  resource_max_workers: 4           # From defaults
  profile: default                  # From defaults
  # ... other aws.* values from defaults
reporting:
  csv:
    enabled: true                   # From defaults
    path: ~/.local/share/.../csv    # From defaults
```

**Precedence Chain:** `defaults → global → project → explicit → dotenv → env → overrides`

## Metadata Tracking

Every configuration setting carries metadata about its source, accessible via the Python API:

```python
from costcutter.config import load_config

# Note: load_config() currently returns just config for backward compatibility
# Metadata tracking available when using utilityhub_config.load_settings() directly
from utilityhub_config import load_settings
from costcutter.config import Config

config, metadata = load_settings(Config, app_name="costcutter", env_prefix="COSTCUTTER_")

# Check where a specific setting came from
region_source = metadata.get_source("region")
if region_source:
    print(f"Region source: {region_source.source}")           # e.g., "global", "env", "overrides"
    print(f"File/path: {region_source.source_path}")          # e.g., "/home/user/.config/costcutter/costcutter.yaml"
    print(f"Raw value: {region_source.raw_value}")            # Original value before validation

# Check nested fields
level_source = metadata.get_source("logging.level")
if level_source:
    print(f"Logging level from: {level_source.source}")

# Iterate all field sources
for field, source in metadata.per_field.items():
    print(f"{field}: {source.source} ({source.source_path})")
```

**Source Types:**
- `defaults` - Field default from Pydantic model
- `global` - Global config file (`~/.config/costcutter/...`)
- `project` - Project config file (`./costcutter.yaml` or `./config/...`)
- `dotenv` - `.env` file in current directory
- `env` - Environment variable (source_path shows `ENV:VARIABLE_NAME`)
- `overrides` - Runtime overrides (source_path shows `runtime`)

**Example output:**

```
dry_run: overrides (runtime)
logging.level: env (ENV:COSTCUTTER_LOGGING__LEVEL)
logging.enabled: defaults (None)
aws.region: global (/home/user/.config/costcutter/costcutter.yaml)
aws.services: project (/workspace/costcutter.yaml)
aws.max_workers: env (ENV:COSTCUTTER_AWS__MAX_WORKERS)
aws.profile: defaults (None)
```

## Common Validation Errors

### Type Errors

**❌ Error: Wrong type**
```yaml
aws:
  max_workers: "eight"  # Should be integer
```

**Error message:**
```
ConfigValidationError: 1 validation error for Config
aws.max_workers
  Input should be a valid integer [type=int_type]
```

**✅ Fix:**
```yaml
aws:
  max_workers: 8
```

### Constraint Violations

**❌ Error: Out of bounds**
```yaml
aws:
  max_workers: 200  # Must be <= 100
```

**Error message:**
```
ConfigValidationError: 1 validation error for Config
aws.max_workers
  Input should be less than or equal to 100 [type=less_than_equal]
```

**✅ Fix:**
```yaml
aws:
  max_workers: 50
```

### Literal Type Errors

**❌ Error: Invalid logging level**
```yaml
logging:
  level: TRACE  # Must be DEBUG/INFO/WARNING/ERROR/CRITICAL
```

**Error message:**
```
ConfigValidationError: 1 validation error for Config
logging.level
  Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL' [type=literal_error]
```

**✅ Fix:**
```yaml
logging:
  level: DEBUG
```

### Duplicate Values

**❌ Error: Duplicate regions**
```yaml
aws:
  region:
    - us-east-1
    - us-west-2
    - us-east-1  # Duplicate
```

**Error message:**
```
ConfigValidationError: 1 validation error for Config
aws.region
  Value error, region list contains duplicate values [type=value_error]
```

**✅ Fix:**
```yaml
aws:
  region:
    - us-east-1
    - us-west-2
```

### Empty Lists

**❌ Error: Empty services**
```yaml
aws:
  services: []  # Must have at least 1 service
```

**Error message:**
```
ConfigValidationError: 1 validation error for Config
aws.services
  List should have at least 1 item after validation [type=min_length]
```

**✅ Fix:**
```yaml
aws:
  services:
    - ec2
```

### Extra Fields (Typos)

**❌ Error: Unknown field**
```yaml
aws:
  regions: [us-east-1]  # Should be 'region' (singular)
```

**Error message:**
```
ConfigValidationError: 1 validation error for Config
aws.regions
  Extra inputs are not permitted [type=extra_forbidden]
```

**✅ Fix:**
```yaml
aws:
  region: [us-east-1]
```

## Validation

CostCutter performs comprehensive validation at startup using Pydantic v2:

1. **Type Validation** - All values must match declared types
2. **Constraint Validation** - Numeric bounds (ge/le), string lengths, list sizes checked
3. **Literal Validation** - Restricted values (logging level) enforced
4. **Custom Validators** - Duplicates, unknown regions checked
5. **Extra Field Rejection** - Unknown keys in config files are rejected (typo detection)

**When validation fails:**
- CLI exits immediately with detailed error message
- No AWS resources are modified
- Error shows: field path, error type, expected value, source information, checked files

**Validation happens at:**
- Application startup (CLI or Python API)
- Configuration reload
- Any call to `load_config()`

**Supported file formats:** `.yaml`, `.toml` (JSON and YML also work but not recommended)

## Troubleshooting

### Configuration not taking effect

**Check precedence order:**

1. Verify which config sources are active
2. Higher priority sources override lower ones
3. Use metadata tracking to see where each value comes from

**Debug configuration:**

```python
from costcutter.config import load_config

config = load_config()
print(config.model_dump())  # See final merged config
print(config.model_dump_json(indent=2))  # JSON format
```

**Check with metadata:**

```python
from utilityhub_config import load_settings
from costcutter.config import Config

config, metadata = load_settings(Config, app_name="costcutter", env_prefix="COSTCUTTER_")

# See where each field came from
for field in ["dry_run", "aws.region", "aws.services", "logging.level"]:
    source = metadata.get_source(field)
    if source:
        print(f"{field}: {source.source} from {source.source_path}")
```

### Environment variables not working

**Ensure correct syntax:**

- Prefix: `COSTCUTTER_` (case-insensitive but uppercase recommended)
- Nesting: Use `__` (double underscore)
- Lists: Use YAML/JSON syntax with quotes

**Test:**

```bash
# Boolean
export COSTCUTTER_DRY_RUN=false

# String
export COSTCUTTER_LOGGING__LEVEL=DEBUG

# List (YAML syntax, use quotes)
export COSTCUTTER_AWS__REGION='["us-east-1", "us-west-2"]'
export COSTCUTTER_AWS__SERVICES='["ec2", "s3"]'

# Integer
export COSTCUTTER_AWS__MAX_WORKERS=8

# Verify
python -c "from costcutter.config import load_config; c = load_config(); print(f'dry_run={c.dry_run}, region={c.aws.region}')"
```

### Validation errors

**Understanding error messages:**

```
ConfigValidationError: Configuration validation failed

2 validation errors for Config
aws.max_workers
  Input should be greater than or equal to 1 [type=greater_than_equal]
logging.level
  Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL' [type=literal_error]

Checked files:
  - ~/.config/costcutter/costcutter.yaml (found)
  - ./costcutter.yaml (not found)

Precedence: defaults → global → project → explicit → dotenv → env → overrides
```

**Error components:**
1. **Field path** - `aws.max_workers`, `logging.level` (exact location of error)
2. **Error type** - `greater_than_equal`, `literal_error` (what validation failed)
3. **Checked files** - Shows which files were searched and found
4. **Precedence** - Shows the merge order used

**Common fixes:**
- Check field name spelling (typos trigger `extra_forbidden`)
- Verify value type matches expected (int vs string)
- Check constraints (min/max values, list lengths)
- For Literal fields, use exact allowed values
- Remove duplicate values from lists

### Config file discovery issues

**Check file locations and names:**

```bash
# Global config (either works)
ls -la ~/.config/costcutter/costcutter.yaml
ls -la ~/.config/costcutter/costcutter.toml

# Project config (checked in order)
ls -la ./costcutter.yaml
ls -la ./costcutter.toml
ls -la ./config/costcutter.yaml
ls -la ./config/costcutter.toml

# Dotenv
ls -la ./.env
```

**Note:** Old locations (`~/.costcutter.yaml`, `~/.costcutter.json`) are NOT supported. Use new locations above.

### Unknown AWS region warnings

**Warning (not error):**
```yaml
aws:
  region:
    - us-future-1  # Warning: Unknown region, but accepted
```

**Output:**
```
UserWarning: Unknown AWS region(s): ['us-future-1'].
Known regions: ['af-south-1', 'ap-east-1', ..., 'us-west-2'].
If using a new AWS region, this warning can be ignored.
```

**This is intentional** - forward compatibility for new AWS regions. Execution continues normally.

**To suppress warnings:**
- Verify region name is correct (check for typos)
- If using opt-in region, ensure it's enabled in your AWS account
- If using new region, warning can be safely ignored

## Next Steps

- [How It Works](./how-it-works.md) - Understand execution flow
- [Getting Started](./getting-started.md) - Quick start guide
- [Troubleshooting](./troubleshooting.md) - Common issues
- [utilityhub_config docs](https://utilityhub.hyperoot.dev/packages/utilityhub_config/) - Configuration loading library
