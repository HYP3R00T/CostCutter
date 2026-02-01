# Contributing

We welcome contributions! Please follow standard Python development practices.

## Setup

Requires Python 3.12+. We strictly use `uv` for dependency management.

```bash
uv sync --extra dev
source .venv/bin/activate
pre-commit install
```

## adding a New Service

1.  **Create Handler**: Add `src/costcutter/services/<service>/<resource>.py`. It must return a list of dicts with `id` and `deleted` status.
2.  **Register**: Update `SERVICE_HANDLERS` in `src/costcutter/orchestrator.py`.
3.  **Dependencies**: Define relationships in `src/costcutter/dependencies.py` if needed.
4.  **Test**: Add unit tests in `tests/`. Mock `boto3` calls appropriately.

## Testing

Run the full suite before submitting:

```bash
uv run pytest --cov=src/costcutter
uv run ruff check .
uv run ruff format .
```

## Pull Requests

1.  Fork and branch.
2.  Add tests for new features.
3.  Update docs if behavior changes.
4.  Submit PR.
