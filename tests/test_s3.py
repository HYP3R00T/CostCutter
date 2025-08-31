"""Tests for costcutter.services.s3"""

import importlib
from types import SimpleNamespace


def test_cleanup_s3_calls_all_handlers(monkeypatch):
    """Ensure cleanup_s3 iterates and calls every handler with the provided args."""
    calls = []

    def handler1(session, region, dry_run=True, max_workers=1):
        calls.append(("h1", session, region, dry_run, max_workers))

    def handler2(session, region, dry_run=True, max_workers=1):
        calls.append(("h2", session, region, dry_run, max_workers))

    module = importlib.import_module("costcutter.services.s3")
    monkeypatch.setattr(module, "_HANDLERS", {"h1": handler1, "h2": handler2})

    fake_session = SimpleNamespace()
    result = module.cleanup_s3(session=fake_session, region="eu-west-1", dry_run=False, max_workers=5)

    assert result is None
    assert ("h1", fake_session, "eu-west-1", False, 5) in calls
    assert ("h2", fake_session, "eu-west-1", False, 5) in calls
    assert len(calls) == 2


def test_cleanup_s3_with_empty_handlers(monkeypatch):
    """When no handlers are registered, cleanup_s3 should be a no-op and not raise."""
    module = importlib.import_module("costcutter.services.s3")
    monkeypatch.setattr(module, "_HANDLERS", {})

    fake_session = SimpleNamespace()
    # should not raise
    assert module.cleanup_s3(session=fake_session, region="us-west-2") is None


def test_cleanup_s3_passes_default_args(monkeypatch):
    """Verify that default kwargs are passed through to handlers when used."""
    recorded = {}

    def handler(session, region, dry_run=True, max_workers=1):
        recorded.update({
            "session": session,
            "region": region,
            "dry_run": dry_run,
            "max_workers": max_workers,
        })

    module = importlib.import_module("costcutter.services.s3")
    monkeypatch.setattr(module, "_HANDLERS", {"only": handler})

    fake_session = SimpleNamespace(name="s")
    module.cleanup_s3(session=fake_session, region="ap-south-1")

    assert recorded["session"] is fake_session
    assert recorded["region"] == "ap-south-1"
    # defaults
    assert recorded["dry_run"] is True
    assert recorded["max_workers"] == 1
