"""Tests for costcutter.services.s3.buckets"""

from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError

from costcutter.services.s3 import buckets


class DummyClientNonVersioned:
    def get_paginator(self, name):
        class P:
            def paginate(self, **kwargs):
                yield {"Contents": [{"Key": "foo.txt"}, {"Key": "bar.txt"}]}

        return P()


class DummyClientVersioned:
    def get_paginator(self, name):
        class P:
            def paginate(self, **kwargs):
                # return a page with Versions and DeleteMarkers
                yield {
                    "Versions": [{"Key": "v1.txt", "VersionId": "111"}],
                    "DeleteMarkers": [{"Key": "v2.txt", "VersionId": "222"}],
                }

        return P()


def test_catalog_objects_non_versioned():
    client = DummyClientNonVersioned()
    objs = buckets.catalog_objects(client=client, bucket_name="b", region="r")
    assert any(o["Key"] == "foo.txt" for o in objs)
    assert all("VersionId" in o for o in objs)


def test_catalog_objects_versioned():
    client = DummyClientVersioned()
    objs = buckets.catalog_objects(client=client, bucket_name="b", region="r")
    # should include both versions and delete markers with VersionId
    keys = {o["Key"] for o in objs}
    assert "v1.txt" in keys and "v2.txt" in keys
    assert all(o.get("VersionId") for o in objs)


def test_cleanup_objects_records_and_calls(monkeypatch):
    recorded = []

    class DummyReporter:
        def record(self, *a, **k):
            recorded.append((a, k))

    # Client that records last delete_objects payload
    last = {}

    class DummyClient:
        def delete_objects(self, **kwargs):
            last.update(kwargs)
            return {"Deleted": kwargs["Delete"]["Objects"]}

    monkeypatch.setattr("costcutter.services.s3.buckets.get_reporter", lambda: DummyReporter())
    client = DummyClient()
    objs = [{"Key": "a.txt", "VersionId": "1"}, {"Key": "b.txt", "VersionId": None}]
    # call the batched deleter directly
    buckets.cleanup_objects(
        client=client, bucket_name="buck", objects_iter=iter(objs), region="r", reporter=buckets.get_reporter()
    )

    # reporter recorded two events
    assert len(recorded) == 2
    # client.delete_objects invoked with Objects; the second entry should omit VersionId when None
    assert last["Bucket"] == "buck"
    assert isinstance(last["Delete"], dict)
    expected = [{"Key": "a.txt", "VersionId": "1"}, {"Key": "b.txt"}]
    assert last["Delete"]["Objects"] == expected


def test_delete_errors_are_recorded(monkeypatch):
    recorded = []

    class DummyReporter:
        def record(self, *a, **k):
            recorded.append((a, k))

    # Client that returns an Errors list for delete_objects
    last = {}

    class DummyClient:
        def delete_objects(self, **kwargs):
            last.update(kwargs)
            return {"Deleted": [], "Errors": [{"Key": "x.txt", "Code": "AccessDenied", "Message": "denied"}]}

    monkeypatch.setattr("costcutter.services.s3.buckets.get_reporter", lambda: DummyReporter())
    client = DummyClient()
    objs = [{"Key": "x.txt", "VersionId": None}]
    # call the batched deleter directly
    buckets.cleanup_objects(
        client=client, bucket_name="buck", objects_iter=iter(objs), region="r", reporter=buckets.get_reporter()
    )

    # Should have recorded the initial delete record and then a failure record
    assert len(recorded) >= 2
    # last delete payload should include the object (without VersionId)
    assert last["Delete"]["Objects"] == [{"Key": "x.txt"}]


def test_catalog_buckets_and_cleanup_buckets(monkeypatch):
    # Dummy session to return client with list_buckets
    class DummySession:
        def client(self, service_name=None, region_name=None):
            class C:
                def list_buckets(self):
                    return {"Buckets": [{"Name": "one"}, {"Name": "two"}]}

                def list_objects_v2(self, **kwargs):
                    return {"KeyCount": 0}

                def delete_bucket(self, **kwargs):
                    return {}

            return C()

    session = DummySession()
    names = buckets.catalog_buckets(session, "r")  # type: ignore[arg-type]
    assert "one" in names and "two" in names

    # monkeypatch cleanup_bucket so cleanup_buckets runs quickly
    monkeypatch.setattr("costcutter.services.s3.buckets.cleanup_bucket", lambda *a, **k: None)
    buckets.cleanup_buckets(session=session, region="r", dry_run=True, max_workers=1)  # type: ignore[arg-type]


def test_cleanup_bucket_dry_run(monkeypatch):
    class DummySession:
        def client(self, service_name=None, region_name=None):
            class C:
                def list_buckets(self):
                    return {"Buckets": []}

                def list_objects_v2(self, **kwargs):
                    return {"KeyCount": 0}

            return C()

    # ensure reporter.record is callable
    monkeypatch.setattr(
        "costcutter.services.s3.buckets.get_reporter", lambda: SimpleNamespace(record=lambda *a, **k: None)
    )
    buckets.cleanup_bucket(session=DummySession(), region="r", bucket_name="b", dry_run=True)  # type: ignore[arg-type]


def test_catalog_objects_clienterror():
    class DummyClient:
        def get_paginator(self, name):
            # Simulate a client error while getting paginator
            error_response = {"Error": {"Code": "500", "Message": "boom"}}
            raise ClientError(error_response, "list_object_versions")

    client = DummyClient()
    objs = buckets.catalog_objects(client=client, bucket_name="b", region="r")
    # catalog_objects catches ClientError and returns early; iterator should be empty
    assert list(objs) == []


def test_abort_multipart_uploads_handles_uploads_and_errors():
    called = []

    class DummyClient:
        def get_paginator(self, name):
            class P:
                def paginate(self, **kwargs):
                    # include one valid upload and some malformed ones
                    yield {
                        "Uploads": [
                            {"Key": "good.txt", "UploadId": "u1"},
                            {"Key": None, "UploadId": "u2"},
                            {"Key": "missingid", "UploadId": None},
                        ]
                    }

            return P()

        def abort_multipart_upload(self, **kwargs):
            # abort only the valid upload; raise for anything else to exercise logging
            bucket = kwargs.get("Bucket")
            key = kwargs.get("Key")
            upload_id = kwargs.get("UploadId")
            if key == "good.txt":
                called.append((bucket, key, upload_id))
            else:
                raise ClientError({"Error": {"Code": "Err", "Message": "fail"}}, "abort")

    client = DummyClient()
    aborted = buckets.abort_multipart_uploads(client=client, bucket_name="buck", region="r")
    assert aborted == 1
    assert called == [("buck", "good.txt", "u1")]


def test_catalog_buckets_no_get_bucket_location_and_none():
    # Client without get_bucket_location attribute
    class DummySession1:
        def client(self, service_name=None, region_name=None):
            class C:
                def list_buckets(self):
                    return {"Buckets": [{"Name": "one"}, {"Name": "two"}]}

            return C()

    names = buckets.catalog_buckets(DummySession1(), "r")  # type: ignore[arg-type]
    assert "one" in names and "two" in names

    # Client where get_bucket_location returns None should map to us-east-1
    class DummySession2:
        def client(self, service_name=None, region_name=None):
            class C:
                def list_buckets(self):
                    return {"Buckets": [{"Name": "east"}]}

                def get_bucket_location(self, **kwargs):
                    return {"LocationConstraint": None}

            return C()

    names2 = buckets.catalog_buckets(DummySession2(), "us-east-1")  # type: ignore[arg-type]
    assert "east" in names2


def test_cleanup_bucket_non_dry_run_success(monkeypatch):
    recorded = []

    class DummyReporter:
        def record(self, *a, **k):
            recorded.append((a, k))

    monkeypatch.setattr("costcutter.services.s3.buckets.get_reporter", lambda: DummyReporter())

    class Client:
        def __init__(self):
            self.deleted_payload = None
            self.bucket_deleted = False

        def get_paginator(self, name):
            class P:
                def __init__(self, name):
                    self._name = name

                def paginate(self, **kwargs):
                    if self._name == "list_multipart_uploads":
                        # no uploads in progress
                        yield {}
                    elif self._name == "list_object_versions":
                        # return one version to be deleted
                        yield {"Versions": [{"Key": "v1.txt", "VersionId": "1"}]}
                    else:
                        yield {}

            return P(name)

        def abort_multipart_upload(self, **kwargs):
            # no-op
            return None

        def delete_objects(self, **kwargs):
            # record payload and return Deleted list
            self.deleted_payload = kwargs
            return {"Deleted": kwargs["Delete"]["Objects"]}

        def delete_bucket(self, **kwargs):
            self.bucket_deleted = True
            return {}

    client = Client()

    class DummySession:
        def client(self, service_name=None, region_name=None):
            return client

    buckets.cleanup_bucket(session=DummySession(), region="r", bucket_name="buck", dry_run=False)  # type: ignore[arg-type]

    assert client.bucket_deleted is True
    assert client.deleted_payload is not None
    # ensure reporter recorded the final delete action for the bucket
    assert any(args[3] == "delete" for args, kwargs in recorded)


def test_cleanup_buckets_propagates_exceptions(monkeypatch):
    # catalog_buckets returns one bucket, cleanup_bucket raises -> propagated
    monkeypatch.setattr("costcutter.services.s3.buckets.catalog_buckets", lambda session, region: ["b1"])

    def raiseer(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr("costcutter.services.s3.buckets.cleanup_bucket", raiseer)

    with pytest.raises(RuntimeError):
        buckets.cleanup_buckets(session=object(), region="r", dry_run=True, max_workers=1)  # type: ignore[arg-type]
