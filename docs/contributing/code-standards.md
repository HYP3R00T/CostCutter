# Code Standards

Conventions for contributing code.

---

## Naming

- **Variables/functions:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `ALL_CAPS`
- **Files:** `snake_case.py`
- **Private members:** `_prefixed`

---

## Type Hints

**Required** for all functions:

```python
def cleanup_volumes(
    session: Session,
    region: str,
    reporter: Reporter,
    dry_run: bool = True
) -> None:
    """Delete volumes."""
    pass
```

Use modern syntax:
- `list[str]` not `List[str]`
- `dict[str, Any]` not `Dict[str, Any]`
- `str | None` not `Optional[str]`

---

## Docstrings

**Required** for all public functions (Google style):

```python
def catalog_volumes(session: Session, region: str, reporter: Reporter) -> list[str]:
    """
    List all EBS volumes in a region.

    Args:
        session: Boto3 session for AWS credentials.
        region: AWS region name.
        reporter: Event reporter instance.

    Returns:
        List of volume IDs.
    """
    pass
```

---

## Imports

Order (enforced by ruff):
1. Standard library
2. Third-party (boto3, typer, rich)
3. Local (`from costcutter...`)

---

## Error Handling

- Catch specific exceptions: `ClientError`, `ValueError`
- Never use bare `except:`
- Log errors: `logger.error(...)`
- Report failures: `reporter.record(..., status="failed")`

---

## Formatting

```bash
# Auto-format
mise run fmt

# Check linting
mise run lint
```

---

## Quality Checks

Before submitting:
```bash
mise run fmt     # Format
mise run lint    # Lint
mise run test    # Test
```

All must pass.

---

## Next Steps

- [Testing Guide](./testing.md) : Write tests
- [Submission Guidelines](./submission.md) : Submit PR
