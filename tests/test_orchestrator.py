"""Tests for costcutter.orchestrator"""

import pytest

from costcutter.orchestrator import _service_supported_in_region, orchestrate_services, process_region_service


def test_service_supported_in_region():
    assert _service_supported_in_region({"svc": {"us-east-1"}}, "svc", "us-east-1")
    assert _service_supported_in_region({}, "svc", "us-east-1")


def test_process_region_service(monkeypatch):
    class DummySession:
        pass

    def handler(session, region, dry_run):
        return None

    process_region_service(DummySession(), "us-east-1", "svc", handler, True)
    with pytest.raises(TypeError):
        process_region_service(DummySession(), "us-east-1", "svc", object(), True)


def test_orchestrate_services(monkeypatch):
    monkeypatch.setattr(
        "costcutter.orchestrator.load_config",
        lambda: type(
            "Cfg", (), {"aws": type("AWS", (), {"services": ["ec2"], "region": ["us-east-1"], "max_workers": 1})()}
        )(),
    )
    monkeypatch.setattr(
        "costcutter.orchestrator.create_aws_session",
        lambda cfg: type("Session", (), {"get_available_regions": lambda self, svc: ["us-east-1"]})(),
    )
    # Replace the handler mapping entry so SERVICE_HANDLERS uses our stub
    monkeypatch.setattr("costcutter.orchestrator.SERVICE_HANDLERS", {"ec2": (lambda session, region, dry_run: None)})
    summary = orchestrate_services(dry_run=True)
    # summary should include counters and events
    assert isinstance(summary, dict)
    assert {"processed", "skipped", "failed", "events"}.issubset(set(summary.keys()))
    assert summary["processed"] == 1
    assert summary["skipped"] == 0
    assert summary["failed"] == 0
    assert isinstance(summary["events"], list)


def test_service_supported_in_region_false():
    # When mapping exists but does not include region, should be False
    assert not _service_supported_in_region({"svc": {"us-west-2"}}, "svc", "us-east-1")


def test_process_region_service_handler_raises(monkeypatch):
    class DummySession:
        pass

    def handler(session, region, dry_run):
        raise ValueError("boom")

    with pytest.raises(ValueError):
        process_region_service(DummySession(), "us-east-1", "svc", handler, True)


def test_orchestrate_services_no_services_configured(monkeypatch):
    # No services configured should raise
    monkeypatch.setattr(
        "costcutter.orchestrator.load_config",
        lambda: type("Cfg", (), {"aws": type("AWS", (), {"services": [], "region": ["us-east-1"]})()})(),
    )
    with pytest.raises(ValueError):
        orchestrate_services(dry_run=True)


def test_orchestrate_services_invalid_services(monkeypatch):
    # Config services contain an invalid service -> ValueError
    monkeypatch.setattr(
        "costcutter.orchestrator.load_config",
        lambda: type("Cfg", (), {"aws": type("AWS", (), {"services": ["invalidsvc"], "region": ["us-east-1"]})()})(),
    )
    with pytest.raises(ValueError):
        orchestrate_services(dry_run=True)


def test_orchestrate_services_regions_all_union_empty(monkeypatch):
    # If aws.region == ['all'] but AWS session cannot resolve any regions, orchestrate should raise
    monkeypatch.setattr(
        "costcutter.orchestrator.load_config",
        lambda: type("Cfg", (), {"aws": type("AWS", (), {"services": ["ec2"], "region": ["all"]})()})(),
    )
    # create_aws_session returns a session whose get_available_regions returns empty list
    monkeypatch.setattr(
        "costcutter.orchestrator.create_aws_session",
        lambda cfg: type("Session", (), {"get_available_regions": lambda self, svc: []})(),
    )
    with pytest.raises(ValueError):
        orchestrate_services(dry_run=True)


def test_orchestrate_services_skipped_and_processed_counts(monkeypatch):
    # Services configured with one region available -> one processed, one skipped
    monkeypatch.setattr(
        "costcutter.orchestrator.load_config",
        lambda: type(
            "Cfg",
            (),
            {
                "aws": type(
                    "AWS",
                    (),
                    {"services": ["ec2"], "region": ["us-west-2", "us-east-1"], "max_workers": 1},
                )(),
            },
        )(),
    )

    # Session reports ec2 only available in us-east-1
    monkeypatch.setattr(
        "costcutter.orchestrator.create_aws_session",
        lambda cfg: type("Session", (), {"get_available_regions": lambda self, svc: ["us-east-1"]})(),
    )

    # Use a noop handler for ec2
    monkeypatch.setattr("costcutter.orchestrator.SERVICE_HANDLERS", {"ec2": (lambda session, region, dry_run: None)})

    # Reporter stub
    class ReporterStub:
        def to_dicts(self):
            return []

    monkeypatch.setattr("costcutter.orchestrator.get_reporter", lambda: ReporterStub())

    summary = orchestrate_services(dry_run=True)
    assert summary["processed"] == 1
    assert summary["skipped"] == 1
    assert summary["failed"] == 0
