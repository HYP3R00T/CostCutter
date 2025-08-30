from pathlib import Path

from costcutter.reporter import Reporter, get_reporter


def test_reporter_record_snapshot_and_count():
    r = Reporter()
    assert r.count() == 0
    r.record(region="r1", service="s1", resource="res1", action="a1", arn=None, meta={"x": 1})
    r.record(region="r2", service="s2", resource="res2", action="a2", arn="arn:1", meta=None)
    snap = r.snapshot()
    assert isinstance(snap, list)
    assert r.count() == 2
    # check contents
    assert snap[0].service == "s1"
    assert snap[1].arn == "arn:1"


def test_reporter_to_dicts_and_clear(tmp_path: Path):
    r = Reporter()
    r.record(region="reg", service="svc", resource="res", action="act", arn=None, meta={"k": "v"})
    dicts = r.to_dicts()
    assert isinstance(dicts, list)
    assert dicts and dicts[0]["service"] == "svc"
    # write CSV to tmp path
    out = r.write_csv(tmp_path / "ev.csv")
    assert out.exists()
    # clear and ensure count resets
    r.clear()
    assert r.count() == 0


def test_get_reporter_is_singleton():
    r1 = get_reporter()
    r2 = get_reporter()
    assert r1 is r2
