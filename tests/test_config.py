"""Tests for costcutter.conf.config"""

from __future__ import annotations

from costcutter.conf.config import AWSSettings, Config, load_config


def test_config_model_defaults() -> None:
    """Test Config model has appropriate defaults."""
    cfg = Config()
    assert cfg.dry_run is True
    assert cfg.logging.enabled is True
    assert cfg.logging.level == "INFO"
    assert cfg.aws.profile == "default"
    assert cfg.aws.max_workers == 4
    assert len(cfg.aws.region) > 0
    assert len(cfg.aws.services) > 0


def test_config_model_custom_values() -> None:
    """Test Config model accepts custom values."""
    cfg = Config(
        dry_run=False,
        aws=AWSSettings(profile="custom", region=["eu-west-1"]),
    )
    assert cfg.dry_run is False
    assert cfg.aws.profile == "custom"
    assert cfg.aws.region == ["eu-west-1"]


def test_load_config_returns_config() -> None:
    """Test that load_config returns a Config instance."""
    cfg = load_config()
    assert isinstance(cfg, Config)
    assert cfg.dry_run is True
    assert cfg.aws.profile == "default"


def test_load_config_with_overrides() -> None:
    """Test load_config can accept override parameters."""
    overrides = {"dry_run": False}
    cfg = load_config(overrides=overrides)

    # Overrides should override defaults
    assert cfg.dry_run is False


def test_config_dict_access() -> None:
    """Test Config model access as Pydantic BaseModel."""
    cfg = Config()
    assert cfg.dry_run is True
    assert cfg.aws.profile == "default"
    # Pydantic model provides dict access via model_dump
    data = cfg.model_dump()
    assert data["dry_run"] is True
    assert data["aws"]["profile"] == "default"
