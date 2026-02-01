# Configuration File Formats

CostCutter supports YAML, TOML, and JSON configuration files. All formats support the same options.

## YAML Format

The most common format. Human-readable and supports comments.

```yaml
# costcutter.yaml

# Simulation mode (default: true)
# Set to false to actually delete resources
dry_run: true

# Logging configuration
logging:
  enabled: true
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  dir: ~/.local/share/costcutter/logs

# Reporting configuration
reporting:
  csv:
    enabled: true
    path: ~/.local/share/costcutter/reports/events.csv

# AWS configuration
aws:
  # AWS profile from ~/.aws/credentials
  profile: default

  # Explicit credentials (leave empty to use profile)
  aws_access_key_id: ""
  aws_secret_access_key: ""
  aws_session_token: ""  # Optional, for temporary credentials

  # Path to credentials file
  credential_file_path: ~/.aws/credentials

  # Parallelism settings
  max_workers: 4          # Concurrent stages
  resource_max_workers: 10  # Concurrent deletions per resource

  # Regions to scan
  region:
    - us-east-1
    - ap-south-1
    # - all  # Uncomment to scan all regions

  # Services to clean up
  services:
    - ec2
    - elasticbeanstalk
    - s3
```

## TOML Format

More explicit syntax, popular in Python projects.

```toml
# costcutter.toml

dry_run = true

[logging]
enabled = true
level = "INFO"
dir = "~/.local/share/costcutter/logs"

[reporting.csv]
enabled = true
path = "~/.local/share/costcutter/reports/events.csv"

[aws]
profile = "default"
aws_access_key_id = ""
aws_secret_access_key = ""
aws_session_token = ""
credential_file_path = "~/.aws/credentials"
max_workers = 4
resource_max_workers = 10
region = ["us-east-1", "ap-south-1"]
services = ["ec2", "elasticbeanstalk", "s3"]
```

## JSON Format

Machine-readable, no comments supported.

```json
{
  "dry_run": true,
  "logging": {
    "enabled": true,
    "level": "INFO",
    "dir": "~/.local/share/costcutter/logs"
  },
  "reporting": {
    "csv": {
      "enabled": true,
      "path": "~/.local/share/costcutter/reports/events.csv"
    }
  },
  "aws": {
    "profile": "default",
    "aws_access_key_id": "",
    "aws_secret_access_key": "",
    "aws_session_token": "",
    "credential_file_path": "~/.aws/credentials",
    "max_workers": 4,
    "resource_max_workers": 10,
    "region": ["us-east-1", "ap-south-1"],
    "services": ["ec2", "elasticbeanstalk", "s3"]
  }
}
```

## Minimal Examples

### Scan Specific Region Only

```yaml
aws:
  region:
    - us-west-2
```

### EC2 Only Cleanup

```yaml
aws:
  services:
    - ec2
```

### Production-Safe Defaults

```yaml
dry_run: true
logging:
  enabled: true
  level: INFO
aws:
  profile: production
  region:
    - us-east-1
  services:
    - ec2
```

-> **See also**: [Configuration Reference](reference.md)
