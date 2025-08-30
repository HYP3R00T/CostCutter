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
        "costcutter.orchestrator.get_config",
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
