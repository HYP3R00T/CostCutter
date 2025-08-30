from costcutter.main import run


def test_run_returns_summary(monkeypatch):
    """Ensure the programmatic API returns the orchestrator summary dict."""
    import costcutter.main as main_mod

    monkeypatch.setattr(
        main_mod, "orchestrate_services", lambda dry_run: {"processed": 0, "skipped": 0, "failed": 0, "events": []}
    )
    summary = run(dry_run=True)
    assert isinstance(summary, dict)
    assert summary["processed"] == 0
