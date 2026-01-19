import logging
import os
from typing import Any

import boto3
from boto3.session import Session
from pydantic import BaseModel

from costcutter.conf.config import Config

logger = logging.getLogger(__name__)


def _get_aws_value(aws_config: BaseModel | dict[str, Any] | object, key: str, default: str | None = None) -> str | None:
    """Extract value from aws config (BaseModel, dict, or object)."""
    if isinstance(aws_config, BaseModel):
        return getattr(aws_config, key, default)
    if isinstance(aws_config, dict):
        return aws_config.get(key, default)
    return getattr(aws_config, key, default)


def create_aws_session(config: Config) -> Session:
    """Create a boto3 Session based on aws-related settings in Config.

    Falls back through explicit keys, credential file, then default discovery.
    """
    try:
        aws_config = config.aws
    except AttributeError:
        aws_config = {}

    # Handle dict-based aws_config
    aws_access_key_id = _get_aws_value(aws_config, "aws_access_key_id")
    aws_secret_access_key = _get_aws_value(aws_config, "aws_secret_access_key")
    aws_session_token = _get_aws_value(aws_config, "aws_session_token")
    credential_file_path_raw = _get_aws_value(aws_config, "credential_file_path", "")
    credential_file_path = os.path.expanduser(credential_file_path_raw or "")
    profile_name = _get_aws_value(aws_config, "profile", "default")

    if aws_access_key_id and aws_secret_access_key:
        logger.info("Using credentials from config (access key + secret)")
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
        )
        return session

    if credential_file_path and os.path.isfile(credential_file_path):
        logger.info(
            "Using credentials file at %s with profile '%s'",
            credential_file_path,
            profile_name,
        )
        os.environ["AWS_SHARED_CREDENTIALS_FILE"] = credential_file_path
        session = boto3.Session(profile_name=profile_name)
        return session

    logger.info("Using default boto3 session (env vars, ~/.aws/credentials, etc.)")
    session = boto3.Session()
    return session
