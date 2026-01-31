import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from boto3.session import Session
from botocore.exceptions import ClientError

_ACCOUNT_ID: str | None = None

logger = logging.getLogger(__name__)

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


def _get_account_id(session: Session) -> str:
    """Return (and cache) the current AWS account id (simple module cache)."""
    global _ACCOUNT_ID
    if _ACCOUNT_ID is None:
        try:
            _ACCOUNT_ID = session.client("sts").get_caller_identity().get("Account", "")
        except Exception as e:  # pragma: no cover
            logger.error("Failed to resolve account id: %s", e)
            _ACCOUNT_ID = ""
    return _ACCOUNT_ID


# Error codes that are transient and warrant retry
TRANSIENT_ERROR_CODES = {
    "VolumeInUse",
    "InvalidGroup.InUse",
    "InvalidNetworkInterface.InUse",
    "InstanceInvalidState.TerminationInProgress",
    "DependencyViolation",
    "InvalidAddress.InUse",
    "InvalidParameterValue",  # Sometimes transient during cleanup
    "RequestLimitExceeded",
    "ThrottlingException",
}


def retry_on_soft_blocker(max_retries: int = 3, backoff_base: float = 2.0) -> Callable[[F], F]:
    """Decorator to retry AWS API calls on transient dependency errors.

    Catches soft blocker errors (DependencyViolation, VolumeInUse, InvalidGroup.InUse, etc.)
    and retries with exponential backoff. Hard blockers (other ClientErrors) are re-raised
    immediately without retry.

    Args:
        max_retries: Number of retry attempts (default 3: 2s, 4s, 8s delays)
        backoff_base: Base for exponential backoff calculation (default 2.0)

    Returns:
        Decorated function that retries on transient errors

    Example:
        @retry_on_soft_blocker(max_retries=3)
        def delete_volume(session, region, volume_id):
            client = session.client("ec2", region_name=region)
            client.delete_volume(VolumeId=volume_id)
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "")
                    last_exception = e

                    # Check if error is transient (soft blocker)
                    is_transient = any(code in error_code for code in TRANSIENT_ERROR_CODES)

                    if not is_transient:
                        # Hard blocker: re-raise immediately without retry
                        raise

                    if attempt < max_retries:
                        # Calculate backoff delay: 2^attempt seconds
                        delay = backoff_base**attempt
                        logger.warning(
                            "Transient error '%s' in %s, retrying in %.1fs (attempt %d/%d): %s",
                            error_code,
                            func.__name__,
                            delay,
                            attempt + 1,
                            max_retries,
                            e.response.get("Error", {}).get("Message", ""),
                        )
                        time.sleep(delay)
                    else:
                        # All retries exhausted; will be raised below
                        logger.error(
                            "Transient error '%s' in %s persisted after %d retries: %s",
                            error_code,
                            func.__name__,
                            max_retries,
                            e.response.get("Error", {}).get("Message", ""),
                        )
                except Exception:
                    # Non-ClientError exceptions (network, timeout, etc.) are re-raised
                    raise

            # If we exhausted retries and got here, raise the last exception
            if last_exception:
                raise last_exception

        return wrapper  # type: ignore[return-value]

    return decorator
