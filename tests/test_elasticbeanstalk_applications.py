"""Tests for costcutter.services.elasticbeanstalk.applications"""

from costcutter.services.elasticbeanstalk import applications


class DummySession:
    def client(self, service_name=None, region_name=None):
        class Client:
            def get_caller_identity(self):
                return {"Account": "123456789012"}

            def describe_applications(self):
                return {
                    "Applications": [
                        {"ApplicationName": "test-app-1"},
                        {"ApplicationName": "test-app-2"},
                    ]
                }

            def delete_application(self, **kwargs):
                return {}

        return Client()


def test_get_account_id():
    # Reset the cache before test
    import costcutter.services.common

    costcutter.services.common._ACCOUNT_ID = None

    session = DummySession()
    from costcutter.services.common import _get_account_id

    assert _get_account_id(session) == "123456789012"  # type: ignore[arg-type]


def test_catalog_applications():
    session = DummySession()
    app_names = applications.catalog_applications(session, "us-east-1")  # type: ignore[arg-type]
    assert "test-app-1" in app_names
    assert "test-app-2" in app_names
    assert len(app_names) == 2


def test_cleanup_application_dry_run(monkeypatch):
    session = DummySession()
    monkeypatch.setattr(
        "costcutter.services.elasticbeanstalk.applications.get_reporter",
        lambda: type("R", (), {"record": lambda *a, **k: None})(),
    )
    applications.cleanup_application(session, "us-east-1", "test-app-1", dry_run=True)  # type: ignore[arg-type]


def test_cleanup_application_actual(monkeypatch):
    session = DummySession()
    monkeypatch.setattr(
        "costcutter.services.elasticbeanstalk.applications.get_reporter",
        lambda: type("R", (), {"record": lambda *a, **k: None})(),
    )
    applications.cleanup_application(session, "us-east-1", "test-app-1", dry_run=False)  # type: ignore[arg-type]


def test_cleanup_applications(monkeypatch):
    session = DummySession()
    monkeypatch.setattr(
        "costcutter.services.elasticbeanstalk.applications.catalog_applications",
        lambda *args, **kwargs: ["test-app-1"],
    )
    monkeypatch.setattr(
        "costcutter.services.elasticbeanstalk.applications.cleanup_application",
        lambda *args, **kwargs: None,
    )
    applications.cleanup_applications(session, "us-east-1", dry_run=True, max_workers=1)  # type: ignore[arg-type]
