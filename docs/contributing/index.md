# Contributing to CostCutter

Welcome! This guide helps you contribute to CostCutter - whether adding AWS services, fixing bugs, or improving documentation.

---

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

---

## What is CostCutter?

An AWS kill-switch that deletes resources across multiple services to prevent runaway costs.

**Tech Stack:**
- Python 3.13 + boto3 (AWS SDK)
- Typer + Rich (CLI with live UI)
- pytest (testing)
- ruff (linting/formatting)

**Core Principles:**
- Safety first (dry-run by default)
- Parallel execution (fast cleanup)
- Clear reporting (terminal UI + CSV)
- Easy to extend (simple patterns)

---

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

---

## Development Setup

```bash
# Clone and install
git clone https://github.com/YOUR_USERNAME/CostCutter.git
cd CostCutter
pip install -r requirements.txt

# Verify setup
mise run test
```

**Quality checks before submitting:**
```bash
mise run lint    # Check code quality
mise run fmt     # Format code
mise run test    # Run tests
```

---

## Project Structure

```
src/costcutter/
├── services/        # AWS service handlers (EC2, S3, etc.)
├── core/           # Shared utilities (ARN parsing, session)
├── conf/           # Configuration management
├── orchestrator.py # Parallel execution coordinator
├── reporter.py     # Event tracking and CSV export
└── logger.py       # File-based logging

tests/              # Unit tests (mirror src/ structure)
```

---

## Key Components

### Configuration (`conf/`)
Manages settings from `config.yaml` and environment variables. Uses Pydantic for validation.

### Services (`services/`)
Each AWS service (EC2, S3, etc.) has subresources. All handlers follow the same pattern with three mandatory functions.

### Orchestrator (`orchestrator.py`)
Coordinates parallel cleanup across all enabled services and their subresources.

### Reporter (`reporter.py`)
Thread-safe event tracking. Records all cleanup actions and generates CSV reports.

### Logger (`logger.py`)
File-based structured logging with rotation.

### CLI (`cli.py`)
Typer-based interface with Rich for live progress tables.

---

## Next Steps

Start with [Architecture Overview](./architecture.md) to understand how components work together, then follow [Adding Subresources](./adding-subresources.md) to make your first contribution.

Thank you for contributing! 🎉
