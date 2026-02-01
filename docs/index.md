# CostCutter

A kill-switch for AWS. Scan and clean up resources across regions with a single command.

!!! danger "Destructive Tool"
    CostCutter **permanently deletes AWS resources**. This cannot be undone. Always run with `--dry-run` first and use only in sandbox/dev environments.

## What Is CostCutter?

CostCutter is an automated cleanup tool that scans your AWS account and deletes resources to prevent unexpected costs. It's designed as an emergency "kill switch" for:

- 🎓 **Students** learning AWS who fear accidental charges
- 🧪 **Experimenters** testing services without financial risk
- 🏖️ **Sandbox environments** that need automatic teardown
- 🚀 **Hackathons** where resources must be cleaned up after events

## Quick Example

```bash
# Preview what would be deleted (safe)
costcutter --dry-run

# Actually delete resources (irreversible!)
costcutter --no-dry-run
```

## Documentation

### Getting Started

New to CostCutter? Start here.

- [Installation](getting-started/installation.md) - Install via uvx, pip, or virtual environment
- [Quick Start](getting-started/quickstart.md) - Run your first dry-run in 2 minutes

### Configuration

Customize CostCutter's behavior.

- [Configuration Overview](configuration/index.md) - How configuration works
- [File Formats](configuration/file-formats.md) - YAML, TOML, JSON examples
- [Reference](configuration/reference.md) - All configuration options

### Services

What resources CostCutter can delete.

- [Services Overview](services/index.md) - What CostCutter does and doesn't do
- [EC2](services/ec2.md) - Instances, volumes, snapshots, IPs, keys, security groups
- [Elastic Beanstalk](services/elasticbeanstalk.md) - Environments and applications
- [S3](services/s3.md) - Buckets and all objects

### Concepts

Understand how CostCutter works.

- [How It Works](concepts/how-it-works.md) - Dependency graph, execution model, parallelism

### Contributing

Help improve CostCutter.

- [Contributing Guide](contributing.md) - Setup, adding services, pull requests
