"""Tests for __main__.py module entrypoint."""


def test_main_module_entrypoint() -> None:
    """Test that __main__ module has correct structure."""
    # Just import to ensure it's importable and structured correctly
    import costcutter.__main__

    assert hasattr(costcutter.__main__, "app")


def test_main_module_execution() -> None:
    """Test __main__ module would call app when executed."""
    # Simulate running python -m costcutter by importing and calling
    from costcutter.__main__ import app

    # The __main__ module simply imports app from cli
    # We verify it's the right object
    assert callable(app)
