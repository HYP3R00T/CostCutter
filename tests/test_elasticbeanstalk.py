"""Tests for costcutter.services.elasticbeanstalk"""


def test_cleanup_elasticbeanstalk_calls_all_handlers(monkeypatch):
    calls = []

    def handler_environments(session, region, dry_run, max_workers):
        calls.append(("environments", session, region, dry_run, max_workers))

    def handler_applications(session, region, dry_run, max_workers):
        calls.append(("applications", session, region, dry_run, max_workers))

    import costcutter.services.elasticbeanstalk as elasticbeanstalk

    # Update the _HANDLERS dictionary directly
    monkeypatch.setattr(
        elasticbeanstalk,
        "_HANDLERS",
        {
            "environments": handler_environments,
            "applications": handler_applications,
        },
    )

    class DummySession:
        pass

    sess = DummySession()
    elasticbeanstalk.cleanup_elasticbeanstalk(sess, "us-east-1", dry_run=False, max_workers=5)

    # Both handlers should have been called once
    assert len(calls) == 2
    assert {c[0] for c in calls} == {"environments", "applications"}

    # Verify environments is called before applications (dependency order)
    assert calls[0][0] == "environments"
    assert calls[1][0] == "applications"

    for _name, session, region, dry_run, max_workers in calls:
        assert session is sess
        assert region == "us-east-1"
        assert dry_run is False
        assert max_workers == 5


def test_cleanup_elasticbeanstalk_uses_default_max_workers(monkeypatch):
    seen = []

    def handler(session, region, dry_run, max_workers):
        seen.append(max_workers)

    import costcutter.services.elasticbeanstalk as elasticbeanstalk

    # Update the _HANDLERS dictionary directly
    monkeypatch.setattr(
        elasticbeanstalk,
        "_HANDLERS",
        {
            "environments": handler,
            "applications": handler,
        },
    )

    class DummySession:
        pass

    elasticbeanstalk.cleanup_elasticbeanstalk(DummySession(), "eu-west-1")
    assert seen == [1, 1]  # Both handlers called with default value
