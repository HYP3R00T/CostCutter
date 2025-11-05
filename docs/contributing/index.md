# Contributing to CostCutter

Welcome! This guide helps you contribute to CostCutter - whether adding AWS services, fixing bugs, or improving documentation.
## Quick Navigation

**Understanding the System:**
- [Architecture Overview](./architecture.md) : System design and components
- [Code Structure](./code-structure.md) : Directory layout and organization

**Adding Features:**
- [Adding a Service](./adding-service.md) : Create handlers for new AWS services
- [Adding Subresources](./adding-subresources.md) : Add resources to existing services

**Development:**
- [Testing Guide](./testing.md) : Write and run tests
- [Code Standards](./code-standards.md) : Naming, types, and conventions
- [Submission Guidelines](./submission.md) : PR workflow
## Project at a Glance

CostCutter is a Python 3.13 CLI that cleans up cost-prone AWS resources. The repository ships with handlers for EC2 (instances, volumes, snapshots, elastic IPs, key pairs, security groups) and S3 buckets, and the architecture is intentionally designed so additional services can be dropped in with minimal plumbing. Everything runs in dry run mode by default so contributors can iterate safely.

**Technology stack:**
- boto3 for AWS APIs
- Typer and Rich for the CLI experience
- pytest and pytest-cov for unit tests
- ruff for formatting and linting
- uv or pip for dependency management

**Guiding principles:**
- Default to safety through dry run mode and clear reporting
- Keep the orchestration model simple and predictable
- Make extending the service layer straightforward
## How to Contribute

1. **Pick your contribution:**
   - Add new AWS service → [Adding a Service](./adding-service.md)
   - Add resources to existing service → [Adding Subresources](./adding-subresources.md)
   - Fix bugs → Check [GitHub Issues](https://github.com/HYP3R00T/CostCutter/issues)
   - Improve docs → Edit markdown files

2. **Understand the architecture:**
   - Read [Architecture Overview](./architecture.md)
   - Read [Code Structure](./code-structure.md)

3. **Make changes:**
   - Follow [Code Standards](./code-standards.md)
   - Write tests per [Testing Guide](./testing.md)

4. **Submit:**
   - Follow [Submission Guidelines](./submission.md)
## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/CostCutter.git
cd CostCutter

# Option A: uv (recommended)
uv sync --group dev

# Option B: pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the test suite
mise run test
```

Quality checks before opening a pull request:

```bash
mise run fmt
mise run lint
mise run test
```
## Project Structure

```
src/costcutter/
├── services/        # AWS service handlers (EC2, S3, and new ones you add)
├── core/           # Shared utilities (ARN parsing, session)
├── conf/           # Configuration management
├── orchestrator.py # Parallel execution coordinator
├── reporter.py     # Event tracking and CSV export
└── logger.py       # File-based logging

tests/              # Unit tests (mirror src/ structure)
```
## Key Components

### Configuration (`conf/`)
Loads the default YAML file, merges optional overrides, and exposes a lightweight `Config` wrapper for attribute access.

### Services (`services/`)
Each service package exposes a `cleanup_<service>` function (for example `cleanup_ec2`) that coordinates its resource modules.

### Orchestrator (`orchestrator.py`)
Pairs each configured region with each requested service and runs the registered handler in a worker pool.

### Reporter (`reporter.py`)
Records events in a thread-safe list, provides snapshots for the CLI, and writes optional CSV reports.

### Logger (`logger.py`)
Initialises file-based logging (when enabled) and suppresses noisy third-party loggers.

### CLI (`cli.py`)
Typer-based interface with Rich for live progress tables.
## Next Steps

Start with [Architecture Overview](./architecture.md) to understand how components work together, then follow [Adding Subresources](./adding-subresources.md) to make your first contribution.

Thank you for contributing! 🎉
