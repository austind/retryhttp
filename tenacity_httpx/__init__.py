import httpx
from tenacity import RetryCallState, WaitBaseT
from tenacity import retry as tenacity_retry
from tenacity import (retry_any, retry_if_exception, retry_if_exception_type,
                      wait_exponential)

# Default maximum attempts.
MAX_ATTEMPTS = 3

# Default potentially transient HTTP error statuses to retry.
RETRY_HTTP_STATUSES = (
    httpx.codes.TOO_MANY_REQUESTS,
    httpx.codes.INTERNAL_SERVER_ERROR,
    httpx.codes.BAD_GATEWAY,
    httpx.codes.GATEWAY_TIMEOUT,
    httpx.codes.SERVICE_UNAVAILABLE,
)

# Default potentially transient network errors to retry.
RETRY_NETWORK_ERRORS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadError,
    httpx.WriteError,
)


def _retry_http_errors(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRY_HTTP_STATUSES
    return False


def retry(retry=None, wait=None, *dargs, **dkw):
    if retry is None:
        retry = retry_any(
            retry_if_exception(_retry_http_errors),
            retry_if_exception_type(RETRY_NETWORK_ERRORS),
        )

    if wait is None:
        pass  # TODO

    def decorator(func):
        return tenacity_retry(retry=retry, wait=wait, *dargs, **dkw)(func)

    return decorator


__all__ = ["retry"]
