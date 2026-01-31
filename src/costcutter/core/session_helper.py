import logging
import os

import boto3
from boto3.session import Session

from costcutter.config import Config

logger = logging.getLogger(__name__)


def create_aws_session(config: Config) -> Session:
    """Create a boto3 Session based on aws-related settings in Config.

    Falls back through explicit keys, credential file, then default discovery.
    """
    aws_config = config.aws

    aws_access_key_id = aws_config.aws_access_key_id
    aws_secret_access_key = aws_config.aws_secret_access_key
    aws_session_token = aws_config.aws_session_token
    credential_file_path = os.path.expanduser(aws_config.credential_file_path or "")
    profile_name = aws_config.profile

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
