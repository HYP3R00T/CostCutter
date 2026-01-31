"""Configuration loader using utilityhub_config."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from utilityhub_config import load_settings

# All AWS regions as of 2026 (based on https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html)
# Used for validation warnings, not strict enforcement (allows future regions)
KNOWN_AWS_REGIONS = frozenset([
    # US regions (enabled by default)
    "us-east-1",  # US East (N. Virginia)
    "us-east-2",  # US East (Ohio)
    "us-west-1",  # US West (N. California)
    "us-west-2",  # US West (Oregon)
    # Asia Pacific regions
    "ap-east-1",  # Asia Pacific (Hong Kong) - opt-in required
    "ap-east-2",  # Asia Pacific (Taipei) - opt-in required
    "ap-south-1",  # Asia Pacific (Mumbai) - enabled by default
    "ap-south-2",  # Asia Pacific (Hyderabad) - opt-in required
    "ap-southeast-1",  # Asia Pacific (Singapore) - enabled by default
    "ap-southeast-2",  # Asia Pacific (Sydney) - enabled by default
    "ap-southeast-3",  # Asia Pacific (Jakarta) - opt-in required
    "ap-southeast-4",  # Asia Pacific (Melbourne) - opt-in required
    "ap-southeast-5",  # Asia Pacific (Malaysia) - opt-in required
    "ap-southeast-6",  # Asia Pacific (New Zealand) - opt-in required
    "ap-southeast-7",  # Asia Pacific (Thailand) - opt-in required
    "ap-northeast-1",  # Asia Pacific (Tokyo) - enabled by default
    "ap-northeast-2",  # Asia Pacific (Seoul) - enabled by default
    "ap-northeast-3",  # Asia Pacific (Osaka) - enabled by default
    # Canada regions
    "ca-central-1",  # Canada (Central) - enabled by default
    "ca-west-1",  # Canada West (Calgary) - opt-in required
    # Europe regions
    "eu-central-1",  # Europe (Frankfurt) - enabled by default
    "eu-central-2",  # Europe (Zurich) - opt-in required
    "eu-west-1",  # Europe (Ireland) - enabled by default
    "eu-west-2",  # Europe (London) - enabled by default
    "eu-west-3",  # Europe (Paris) - enabled by default
    "eu-north-1",  # Europe (Stockholm) - enabled by default
    "eu-south-1",  # Europe (Milan) - opt-in required
    "eu-south-2",  # Europe (Spain) - opt-in required
    # Middle East regions
    "me-south-1",  # Middle East (Bahrain) - opt-in required
    "me-central-1",  # Middle East (UAE) - opt-in required
    # South America regions
    "sa-east-1",  # South America (São Paulo) - enabled by default
    # Africa regions
    "af-south-1",  # Africa (Cape Town) - opt-in required
    # Other regions
    "il-central-1",  # Israel (Tel Aviv) - opt-in required
    "mx-central-1",  # Mexico (Central) - opt-in required
])


class LoggingSettings(BaseModel):
    """Logging configuration.

    Controls file-based logging for CostCutter operations.
    """

    model_config = ConfigDict(
        validate_default=True,
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    enabled: bool = Field(
        default=True,
        description="Enable file-based logging. When true, logs are written to the specified directory.",
    )
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level (e.g., 'DEBUG' for detailed output, 'INFO' for normal operation, 'ERROR' for errors only).",
    )
    dir: str = Field(
        default_factory=lambda: str(Path.home() / ".local/share/costcutter/logs"),
        description="Directory path for log files (e.g., '~/.local/share/costcutter/logs' or '/var/log/costcutter').",
    )


class CSVReportingSettings(BaseModel):
    """CSV reporting configuration.

    Controls CSV export of deletion events.
    """

    model_config = ConfigDict(
        validate_default=True,
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    enabled: bool = Field(
        default=True,
        description="Enable CSV report generation. When true, deletion events are exported to a CSV file.",
    )
    path: str = Field(
        default_factory=lambda: str(Path.home() / ".local/share/costcutter/reports/events.csv"),
        description="File path for CSV report output (e.g., '~/.local/share/costcutter/reports/events.csv' or '/var/reports/cleanup.csv').",
    )


class ReportingSettings(BaseModel):
    """Reporting configuration.

    Controls various reporting outputs for CostCutter operations.
    """

    model_config = ConfigDict(
        validate_default=True,
        validate_assignment=True,
        extra="forbid",
    )

    csv: CSVReportingSettings = Field(
        default_factory=CSVReportingSettings,
        description="CSV reporting settings for deletion events.",
    )


class AWSSettings(BaseModel):
    """AWS configuration.

    Controls AWS authentication, regions, services, and parallelism settings.
    """

    model_config = ConfigDict(
        validate_default=True,
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    profile: str = Field(
        default="default",
        description="AWS profile name from ~/.aws/credentials or ~/.aws/config (e.g., 'default', 'staging', 'production').",
    )
    aws_access_key_id: str = Field(
        default="",
        description="AWS access key ID for authentication. Leave empty to use profile or credentials file.",
    )
    aws_secret_access_key: str = Field(
        default="",
        description="AWS secret access key for authentication. Leave empty to use profile or credentials file.",
    )
    aws_session_token: str = Field(
        default="",
        description="AWS session token for temporary credentials (optional). Used with STS or IAM role credentials.",
    )
    credential_file_path: str = Field(
        default_factory=lambda: str(Path.home() / ".aws/credentials"),
        description="Path to AWS credentials file (e.g., '~/.aws/credentials'). Used when access keys are not provided.",
    )
    max_workers: int = Field(
        default=4,
        ge=1,
        le=100,
        description="Maximum concurrent workers for stage-level parallelism (e.g., 4 means up to 4 tasks run in parallel per stage). Recommended: 2-10.",
    )
    resource_max_workers: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum concurrent workers per resource handler (e.g., parallel EC2 instance deletions). Higher values = faster cleanup but may hit AWS rate limits. Recommended: 5-20.",
    )
    region: list[str] = Field(
        default_factory=lambda: ["us-east-1", "ap-south-1"],
        min_length=1,
        description="""List of AWS regions to scan and clean up. Use specific region codes (e.g., ['us-east-1', 'eu-west-1']) or ['all'] for all enabled regions.

        Common regions: us-east-1 (N. Virginia), us-west-2 (Oregon), eu-west-1 (Ireland), ap-southeast-1 (Singapore).
        See https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html for complete list.
        Note: Some regions require opt-in before use.""",
    )
    services: list[str] = Field(
        default_factory=lambda: ["ec2", "elasticbeanstalk", "s3"],
        min_length=1,
        description="List of AWS services to clean up (e.g., ['ec2', 's3', 'lambda']). Must specify at least one service.",
    )

    @field_validator("region")
    @classmethod
    def validate_region_no_duplicates(cls, v: list[str]) -> list[str]:
        """Validate region list: check for duplicates and warn about unknown regions.

        This validator:
        1. Prevents duplicate regions (error)
        2. Warns about unrecognized region codes (warning, not error)
        3. Allows 'all' as a special value
        4. Accepts any string to support future AWS regions
        """
        if len(v) != len(set(v)):
            raise ValueError("region list contains duplicate values")

        # Warn about unknown regions (but don't reject them - future compatibility)
        unknown_regions = [r for r in v if r.lower() != "all" and r not in KNOWN_AWS_REGIONS]
        if unknown_regions:
            import warnings

            warnings.warn(
                f"Unknown AWS region(s): {unknown_regions}. "
                f"Known regions: {sorted(KNOWN_AWS_REGIONS)}. "
                "If using a new AWS region, this warning can be ignored. "
                "Some regions require opt-in: https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html",
                UserWarning,
                stacklevel=2,
            )

        return v

    @field_validator("services")
    @classmethod
    def validate_services_no_duplicates(cls, v: list[str]) -> list[str]:
        """Ensure services list contains no duplicates."""
        if len(v) != len(set(v)):
            raise ValueError("services list contains duplicate values")
        return v


class Config(BaseModel):
    """CostCutter configuration model.

    Root configuration containing all settings for CostCutter operations.
    Supports loading from YAML, TOML, JSON, environment variables, and programmatic overrides.
    """

    model_config = ConfigDict(
        validate_default=True,
        validate_assignment=True,
        extra="forbid",
    )

    dry_run: bool = Field(
        default=True,
        description="Enable dry-run mode. When true, simulates actions without making changes. When false, actually deletes resources.",
    )
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
        description="Logging configuration for file-based output.",
    )
    reporting: ReportingSettings = Field(
        default_factory=ReportingSettings,
        description="Reporting configuration for CSV exports and other outputs.",
    )
    aws: AWSSettings = Field(
        default_factory=AWSSettings,
        description="AWS-specific configuration including credentials, regions, and services.",
    )

    def __init__(self, data: dict[str, Any] | None = None, /, **kwargs: Any) -> None:
        """Initialize Config with dict or kwargs for backward compatibility.

        Args:
            data: Optional dict to initialize from (first positional argument only).
            **kwargs: Keyword arguments for standard Pydantic initialization.
        """
        if data is not None:
            # If a dict is passed as first argument, use it as kwargs
            super().__init__(**data)
        else:
            # Otherwise use normal kwargs initialization
            super().__init__(**kwargs)


def load_config(
    overrides: dict[str, Any] | None = None,
    config_file: Path | None = None,
) -> Config:
    """Load configuration using utilityhub_config.

    Auto-discovers config files and merges: defaults → global → project → dotenv → env vars → overrides.

    Args:
        overrides: Runtime overrides (highest precedence).
        config_file: Optional explicit config file path.

    Returns:
        Validated Config instance.
    """
    config, _ = load_settings(
        Config,
        app_name="costcutter",
        env_prefix="COSTCUTTER_",
        config_file=config_file,
        overrides=overrides,
    )
    return config
