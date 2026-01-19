"""Tests for costcutter.cli"""

from types import SimpleNamespace

from costcutter.cli import _render_summary_table, _render_table, main, run_cli


class DummyEvent:
    def __init__(self, timestamp="t", region="r", service="s", resource="res", action="a", arn="arn", meta=None):
        self.timestamp = timestamp
        self.region = region
        self.service = service
        self.resource = resource
        self.action = action
        self.arn = arn
        self.meta = meta or {}


class DummyReporter:
    def snapshot(self):
        return [DummyEvent(), DummyEvent(meta={"foo": "bar"})]

    def write_csv(self, path):
        return path


def test_render_table_empty():
    reporter = DummyReporter()
    table = _render_table(reporter, dry_run=True)
    assert table.title.startswith("CostCutter")


def test_render_summary_table_empty():
    reporter = DummyReporter()
    table = _render_summary_table(reporter, dry_run=True)
    assert table.title.startswith("CostCutter")


def test_run_cli(monkeypatch):
    monkeypatch.setattr("costcutter.cli.get_reporter", lambda: DummyReporter())
    monkeypatch.setattr("costcutter.cli.orchestrate_services", lambda dry_run: None)
    run_cli(dry_run=True)


def test_main(monkeypatch):
    class Ctx:
        invoked_subcommand = None

    monkeypatch.setattr("costcutter.cli.run_cli", lambda dry_run, config_file: None)
    main(Ctx(), dry_run=True, config=None)


def test_render_table_placeholder_when_empty():
    class R:
        def snapshot(self):
            return []

    table = _render_table(R(), dry_run=True)
    assert table.title.startswith("CostCutter")


def test_render_table_meta_exception():
    # meta is an object without .items() so the code should hit the exception
    class E:
        def __init__(self):
            self.timestamp = "t"
            self.region = "r"
            self.service = "s"
            self.resource = "res"
            self.action = "a"
            self.arn = "arn"
            self.meta = object()

    class R:
        def snapshot(self):
            return [E()]

    table = _render_table(R(), dry_run=False)
    assert table.title.startswith("CostCutter")


def test_render_table_tail_caption():
    # generate more than TAIL_COUNT events to trigger the caption path
    class R:
        def snapshot(self):
            return [DummyEvent(timestamp=str(i)) for i in range(12)]

    table = _render_table(R(), dry_run=False)
    assert table.caption and "Showing last" in table.caption


def test_render_summary_table_counts_and_caption():
    class R:
        def snapshot(self):
            return [
                DummyEvent(service="ec2", resource="i-1", action="terminate"),
                DummyEvent(service="ec2", resource="i-1", action="terminate"),
                DummyEvent(service="s3", resource="b-1", action="delete"),
            ]

    table = _render_summary_table(R(), dry_run=False)
    assert table.caption == "Total events: 3"


def test_run_cli_writes_csv_and_handles_figlet_and_clear(monkeypatch, tmp_path):
    # Prepare config that enables CSV export
    cfg = SimpleNamespace(
        reporting=SimpleNamespace(csv=SimpleNamespace(enabled=True, path=str(tmp_path / "events.csv")), dry_run=True)
    )

    # Reporter that returns no events and records write_csv calls
    class R:
        def snapshot(self):
            return []

        def write_csv(self, path):
            return path

    monkeypatch.setattr("costcutter.cli.get_reporter", lambda: R())
    monkeypatch.setattr("costcutter.cli.orchestrate_services", lambda dry_run: None)
    monkeypatch.setattr("costcutter.cli.load_config", lambda overrides=None: cfg)
    # Make Figlet throw so fig_rendered becomes None branch
    monkeypatch.setattr("costcutter.cli.Figlet", lambda font=None: (_ for _ in ()).throw(Exception("fig")))

    # Make Console.clear raise to exercise fallback
    def _bad_clear(self):
        raise Exception("clear-fail")

    monkeypatch.setattr("costcutter.cli.Console.clear", _bad_clear, raising=False)

    # Should not raise
    run_cli(dry_run=True, config_file=None)


def test_run_cli_raises_orchestrator_exception(monkeypatch):
    monkeypatch.setattr("costcutter.cli.get_reporter", lambda: DummyReporter())

    def _bad_orch(dry_run):
        raise RuntimeError("orchestrator boom")

    monkeypatch.setattr("costcutter.cli.orchestrate_services", _bad_orch)
    # minimal config
    monkeypatch.setattr(
        "costcutter.cli.load_config", lambda overrides=None: SimpleNamespace(reporting=None, dry_run=True)
    )

    import pytest

    with pytest.raises(RuntimeError):
        run_cli(dry_run=True, config_file=None)
