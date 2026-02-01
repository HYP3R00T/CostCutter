# Installation

CostCutter can be installed in several ways depending on your needs.

## Recommended: uvx (No Install)

Run CostCutter directly without installing:

```bash
uvx costcutter --help
```

This downloads and runs CostCutter in an isolated environment. Perfect for one-off usage.

**Get uvx:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Global Install

Install CostCutter system-wide:

=== "uv (Recommended)"

    ```bash
    uv tool install costcutter
    ```

=== "pip"

    ```bash
    pip install costcutter
    ```

## Project Install

Install in a virtual environment for project isolation:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install costcutter
```

## Verify Installation

```bash
costcutter --version
```

You should see the version number printed.

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.12+ |
| AWS credentials | Configured via profile or environment variables |

-> **Next**: [Quick Start](quickstart.md)
