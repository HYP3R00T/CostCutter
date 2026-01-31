"""Configuration loader using utilityhub_config."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from utilityhub_config import load_settings


class LoggingSettings(BaseModel):
    """Logging configuration."""

    enabled: bool = True
    level: str = "INFO"
    dir: str = Field(default_factory=lambda: str(Path.home() / ".local/share/costcutter/logs"))


class CSVReportingSettings(BaseModel):
    """CSV reporting configuration."""

    enabled: bool = True
    path: str = Field(default_factory=lambda: str(Path.home() / ".local/share/costcutter/reports/events.csv"))


class ReportingSettings(BaseModel):
    """Reporting configuration."""

    csv: CSVReportingSettings = Field(default_factory=CSVReportingSettings)


class AWSSettings(BaseModel):
    """AWS configuration."""

    profile: str = "default"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""
    credential_file_path: str = Field(default_factory=lambda: str(Path.home() / ".aws/credentials"))
    max_workers: int = 4
    region: list[str] = Field(default_factory=lambda: ["us-east-1", "ap-south-1"])
    services: list[str] = Field(default_factory=lambda: ["ec2", "elasticbeanstalk", "s3"])


class Config(BaseModel):
    """CostCutter configuration model."""

    dry_run: bool = True
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    reporting: ReportingSettings = Field(default_factory=ReportingSettings)
    aws: AWSSettings = Field(default_factory=AWSSettings)

    def __init__(self, data: dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Initialize Config with dict or kwargs for backward compatibility."""
        if data is not None and not kwargs:
            # If a dict is passed as first argument, use it as kwargs
            super().__init__(**data)
        else:
            # Otherwise use normal kwargs initialization
            super().__init__(**kwargs)


def load_config(overrides: dict[str, Any] | None = None) -> Config:
    """Load configuration using utilityhub_config.

    Auto-discovers config files and merges: defaults → global → project → dotenv → env vars → overrides.

    Args:
        overrides: Runtime overrides (highest precedence).

    Returns:
        Validated Config instance.
    """
    config, _ = load_settings(
        Config,
        app_name="costcutter",
        env_prefix="COSTCUTTER_",
        overrides=overrides,
    )
    return config
