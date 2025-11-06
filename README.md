<div align="center">

# 💰 CostCutter

### *Your AWS Budget's Last Line of Defense*

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg?style=for-the-badge)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/costcutter.svg?style=for-the-badge)](https://pypi.org/project/costcutter/)

**An automated kill-switch for AWS accounts that prevents bill shock by cleaning up resources when spending limits are breached.**

[Features](#-features) • [Quick Start](#-quick-start) • [Installation](#-installation) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

> [!CAUTION]
> **⚠️ DESTRUCTIVE TOOL WARNING**
>
> CostCutter will **delete AWS resources aggressively and indiscriminately** once triggered.
> This is not a reversible operation. All data will be permanently lost.


## 🎯 What is CostCutter?

CostCutter is a **serverless AWS cost protection system** that acts as an emergency brake for your cloud spending. It continuously monitors your AWS Budget and automatically triggers resource cleanup when costs exceed your predefined thresholds—ensuring you never wake up to a surprise $10,000 bill from a forgotten EC2 instance.

### Perfect for:
- 🎓 **Students** learning AWS who fear accidental charges
- 🧪 **Experimenters** testing AWS services without financial risk
- 🏖️ **Sandbox environments** that need automatic teardown
- 💡 **Side projects** with strict budget constraints
- 🚀 **Hackathons** where resources must be cleaned up after events

## ✨ Features

### 🎛️ **Powerful Control & Safety**

- **🏃 Dry Run Mode** - Test what would be deleted without actually deleting anything
- **🎯 Multi-Region Support** - Clean resources across all AWS regions or specific ones
- **⚙️ Flexible Configuration** - YAML-based config with environment variable overrides
- **📊 Detailed Reporting** - Live tables, summaries, and optional CSV exports
- **🔗 Dependency-Aware** - Handles resource dependencies in the correct order
- **🐍 Type-Safe** - Fully typed Python codebase with Pydantic validation

### 🚀 **Deployment Flexibility**

- **💻 CLI Mode** - Run manually from your terminal
- **☁️ Lambda Mode** - Deploy as serverless function triggered by AWS Budgets via SNS

## 🚀 Quick Start

### Installation

Run CostCutter with uvx (no global install required):

```bash
# Run without installing (recommended)
uvx costcutter --version

# Safe dry run
uvx costcutter --dry-run
```

For full setup and configuration, see the documentation: https://costcutter.hyperoot.dev

### Basic Usage

```bash
# Dry run (safe mode - shows what would be deleted)
costcutter --dry-run

# Real execution (destructive!)
costcutter

# Use custom config
costcutter --config ./my-config.yaml
```

### Example Configuration

Create a `costcutter.yaml`:

```yaml
aws:
  region:
    - us-east-1
    - eu-west-1
  services:
    - ec2
    - s3
    - elasticbeanstalk

output:
  log_level: INFO
  report_format: csv
  report_path: ./cleanup-report.csv
```


## 📚 Documentation

📖 **[Full Documentation](https://hyperoot.github.io/CostCutter/)**

- [What is CostCutter?](https://hyperoot.github.io/CostCutter/guide/what-is-costcutter.html)
- [Getting Started Guide](https://hyperoot.github.io/CostCutter/guide/getting-started.html)
- [Configuration Reference](https://hyperoot.github.io/CostCutter/guide/config-reference.html)
- [Supported Services](https://hyperoot.github.io/CostCutter/guide/supported-services.html)
- [How It Works](https://hyperoot.github.io/CostCutter/guide/how-it-works.html)
- [Terraform Integration](https://hyperoot.github.io/CostCutter/usage-terraform.html)
- [Contributing Guide](https://hyperoot.github.io/CostCutter/contributing/)

## 🤝 Contributing

We welcome contributions! CostCutter is intentionally modular to make adding new AWS services easy.

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feat/add-rds-cleanup`
3. **Follow the coding standards** (see `.github/copilot-instructions.md`)
4. **Add tests** for your changes
5. **Submit a pull request**

### Adding New Services

Check out our guides:
- [Adding a Service](https://hyperoot.github.io/CostCutter/contributing/adding-service.html)
- [Adding Subresources](https://hyperoot.github.io/CostCutter/contributing/adding-subresources.html)
- [Code Structure](https://hyperoot.github.io/CostCutter/contributing/code-structure.html)

## ⚖️ License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**USE AT YOUR OWN RISK.**

CostCutter is a destructive tool designed to permanently delete AWS resources. The authors and contributors are not responsible for:
- Data loss
- Service interruptions
- Unintended deletions
- Financial consequences
- Any other damages resulting from the use of this tool

Always test in a safe environment first. Always use dry-run mode before actual execution. Always maintain proper backups.

## 🙏 Acknowledgments

Built with ❤️ by [HYP3R00T](https://github.com/HYP3R00T)

Powered by:
- [boto3](https://github.com/boto/boto3) - AWS SDK for Python
- [Typer](https://github.com/fastapi/typer) - CLI framework
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal output
- [Pydantic](https://github.com/pydantic/pydantic) - Data validation
- [UV](https://github.com/astral-sh/uv) - Fast Python package manager

<div align="center">

### ⭐ Star us on GitHub if CostCutter saved you from a surprise AWS bill!

[Report Bug](https://github.com/HYP3R00T/CostCutter/issues) • [Request Feature](https://github.com/HYP3R00T/CostCutter/issues) • [Discussions](https://github.com/HYP3R00T/CostCutter/discussions)

</div>
