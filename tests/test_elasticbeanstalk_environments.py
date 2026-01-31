"""Tests for costcutter.services.elasticbeanstalk.environments"""

from costcutter.services.elasticbeanstalk import environments


class DummySession:
    def client(self, service_name=None, region_name=None):
        class Client:
            def get_caller_identity(self):
                return {"Account": "123456789012"}

            def get_paginator(self, operation_name):
                class Paginator:
                    def paginate(self, **kwargs):
                        return [
                            {
                                "Environments": [
                                    {"EnvironmentName": "test-env-1"},
                                    {"EnvironmentName": "test-env-2"},
                                ]
                            }
                        ]

                return Paginator()

            def terminate_environment(self, **kwargs):
                return {}

        return Client()


def test_get_account_id():
    # Reset the cache before test
    import costcutter.services.common

    costcutter.services.common._ACCOUNT_ID = None

    session = DummySession()
    from costcutter.services.common import _get_account_id

    assert _get_account_id(session) == "123456789012"  # type: ignore[arg-type]


def test_catalog_environments():
    session = DummySession()
    env_names = environments.catalog_environments(session, "us-east-1")  # type: ignore[arg-type]
    assert "test-env-1" in env_names
    assert "test-env-2" in env_names
    assert len(env_names) == 2


def test_cleanup_environment_dry_run(monkeypatch):
    session = DummySession()
    monkeypatch.setattr(
        "costcutter.services.elasticbeanstalk.environments.get_reporter",
        lambda: type("R", (), {"record": lambda *a, **k: None})(),
    )
    environments.cleanup_environment(session, "us-east-1", "test-env-1", dry_run=True)  # type: ignore[arg-type]


def test_cleanup_environment_actual(monkeypatch):
    session = DummySession()
    monkeypatch.setattr(
        "costcutter.services.elasticbeanstalk.environments.get_reporter",
        lambda: type("R", (), {"record": lambda *a, **k: None})(),
    )
    environments.cleanup_environment(session, "us-east-1", "test-env-1", dry_run=False)  # type: ignore[arg-type]


def test_cleanup_environments(monkeypatch):
    session = DummySession()
    monkeypatch.setattr(
        "costcutter.services.elasticbeanstalk.environments.catalog_environments",
        lambda *args, **kwargs: ["test-env-1"],
    )
    monkeypatch.setattr(
        "costcutter.services.elasticbeanstalk.environments.cleanup_environment",
        lambda *args, **kwargs: None,
    )
    environments.cleanup_environments(session, "us-east-1", dry_run=True, max_workers=1)  # type: ignore[arg-type]
