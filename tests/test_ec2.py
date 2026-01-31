"""Tests for costcutter.services.ec2"""

import pytest


def test_cleanup_ec2_calls_all_handlers(monkeypatch):
    calls = []

    def handler_one(session, region, dry_run, max_workers):
        calls.append(("one", session, region, dry_run, max_workers))

    def handler_two(session, region, dry_run, max_workers):
        calls.append(("two", session, region, dry_run, max_workers))

    import costcutter.services.ec2 as ec2

    monkeypatch.setattr(ec2, "_HANDLERS", {"one": handler_one, "two": handler_two})

    class DummySession:
        pass

    sess = DummySession()
    ec2.cleanup_ec2(sess, "us-east-1", dry_run=False, max_workers=5)  # type: ignore[arg-type]

    # Both handlers should have been called once
    assert {c[0] for c in calls} == {"one", "two"}
    for _name, session, region, dry_run, max_workers in calls:
        assert session is sess
        assert region == "us-east-1"
        assert dry_run is False
        assert max_workers == 5


def test_cleanup_ec2_uses_default_max_workers(monkeypatch):
    seen = []

    def handler(session, region, dry_run, max_workers):
        seen.append(max_workers)

    import costcutter.services.ec2 as ec2

    monkeypatch.setattr(ec2, "_HANDLERS", {"only": handler})

    class DummySession:
        pass

    ec2.cleanup_ec2(DummySession(), "eu-west-1")  # type: ignore[arg-type]
    assert seen == [1]


def test_cleanup_ec2_propagates_handler_exception(monkeypatch):
    def handler(session, region, dry_run, max_workers):
        raise RuntimeError("handler failed")

    import costcutter.services.ec2 as ec2

    monkeypatch.setattr(ec2, "_HANDLERS", {"fail": handler})

    class DummySession:
        pass

    with pytest.raises(RuntimeError):
        ec2.cleanup_ec2(DummySession(), "ap-south-1", dry_run=True, max_workers=2)  # type: ignore[arg-type]
