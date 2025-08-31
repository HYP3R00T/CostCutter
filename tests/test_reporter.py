"""Tests for costcutter.reporter"""

from pathlib import Path

from costcutter.reporter import Reporter, get_reporter


def test_reporter_write_csv(tmp_path: Path):
    r = Reporter()
    r.record(
        region="us-east-1",
        service="ec2",
        resource="instance",
        action="terminate",
        arn="arn:aws:ec2:123",
        meta={"id": 1},
    )
    r.record(region="ap-south-1", service="ec2", resource="key-pair", action="delete", arn=None, meta={"name": "kp"})

    out_file = tmp_path / "events.csv"
    written = r.write_csv(out_file)

    assert written.exists()
    content = written.read_text().strip().splitlines()
    # header + 2 rows
    assert len(content) == 3
    header = content[0].split(",")
    assert header == ["timestamp", "region", "service", "resource", "action", "arn", "meta"]

    # append mode
    r.record(
        region="us-east-1",
        service="ec2",
        resource="instance",
        action="terminate",
        arn="arn:aws:ec2:456",
        meta={"id": 2},
    )
    r.write_csv(out_file, overwrite=False)
    content2 = out_file.read_text().strip().splitlines()
    assert len(content2) == 4  # one more row, header not duplicated


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
