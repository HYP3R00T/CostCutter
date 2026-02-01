# Configuration Reference

Complete reference for all CostCutter configuration options.

## Core Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `dry_run` | boolean | `true` | Simulation mode. When `true`, shows what would be deleted without making changes. Set to `false` to execute deletions. |

## AWS Settings (`aws`)

Controls AWS authentication, regions, and services.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `profile` | string | `"default"` | AWS profile name from `~/.aws/credentials` or `~/.aws/config` |
| `aws_access_key_id` | string | `""` | Explicit AWS access key. Leave empty to use profile. |
| `aws_secret_access_key` | string | `""` | Explicit AWS secret key. Leave empty to use profile. |
| `aws_session_token` | string | `""` | AWS session token for temporary credentials (STS). Optional. |
| `credential_file_path` | string | `"~/.aws/credentials"` | Path to AWS credentials file |
| `region` | list | `["us-east-1", "ap-south-1"]` | AWS regions to scan. Use `["all"]` for all enabled regions. |
| `services` | list | `["ec2", "elasticbeanstalk", "s3"]` | AWS services to clean up |
| `max_workers` | integer | `4` | Maximum concurrent workers for stage-level parallelism (1-100) |
| `resource_max_workers` | integer | `10` | Maximum concurrent workers per resource handler (1-100) |

### Available Services

| Service Key | Description |
|-------------|-------------|
| `ec2` | EC2 instances, volumes, snapshots, Elastic IPs, key pairs, security groups |
| `elasticbeanstalk` | Elastic Beanstalk environments and applications |
| `s3` | S3 buckets and all objects |

### Region Examples

```yaml
# Specific regions
region:
  - us-east-1
  - eu-west-1

# All regions (scans every region where selected services are available)
region:
  - all
```

## Logging Settings (`logging`)

Controls file-based logging.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable file logging |
| `level` | string | `"INFO"` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `dir` | string | `"~/.local/share/costcutter/logs"` | Directory for log files |

## Reporting Settings (`reporting`)

### CSV Settings (`reporting.csv`)

Controls CSV export of deletion events.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable CSV report generation |
| `path` | string | `"~/.local/share/costcutter/reports/events.csv"` | Output path for CSV file |

## Parallelism Tuning

CostCutter uses two levels of parallelism:

1. **Stage-level** (`max_workers`): How many resource types are processed in parallel
2. **Resource-level** (`resource_max_workers`): How many individual resources are deleted in parallel

**Recommendations:**

| Use Case | `max_workers` | `resource_max_workers` |
|----------|---------------|------------------------|
| Conservative | 2 | 5 |
| Default | 4 | 10 |
| Aggressive | 8 | 20 |

!!! warning "API Rate Limits"
    Higher parallelism can hit AWS API rate limits. CostCutter handles this with retries, but excessive parallelism may slow down execution.

## Environment Variable Mapping

Every option can be set via environment variable using the `COSTCUTTER_` prefix:

| Config Path | Environment Variable |
|-------------|---------------------|
| `dry_run` | `COSTCUTTER_DRY_RUN` |
| `aws.profile` | `COSTCUTTER_AWS__PROFILE` |
| `aws.region` | `COSTCUTTER_AWS__REGION` (JSON array) |
| `aws.services` | `COSTCUTTER_AWS__SERVICES` (JSON array) |
| `aws.max_workers` | `COSTCUTTER_AWS__MAX_WORKERS` |
| `logging.level` | `COSTCUTTER_LOGGING__LEVEL` |
| `reporting.csv.enabled` | `COSTCUTTER_REPORTING__CSV__ENABLED` |

**Example:**

```bash
export COSTCUTTER_DRY_RUN=false
export COSTCUTTER_AWS__PROFILE=staging
export COSTCUTTER_AWS__REGION='["us-east-1"]'
```
