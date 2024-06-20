import httpx
from tenacity import RetryBaseT, RetryCallState, StopBaseT, WaitBaseT
from tenacity import retry as tenacity_retry
from tenacity import (
    retry_any,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Default maximum attempts.
MAX_ATTEMPTS = 3

# Default potentially transient HTTP error statuses to retry.
RETRY_HTTP_STATUSES = {
    httpx.codes.TOO_MANY_REQUESTS,
    httpx.codes.INTERNAL_SERVER_ERROR,
    httpx.codes.BAD_GATEWAY,
    httpx.codes.GATEWAY_TIMEOUT,
    httpx.codes.SERVICE_UNAVAILABLE,
}

# Default potentially transient network errors to retry.
RETRY_NETWORK_ERRORS = {
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadError,
    httpx.WriteError,
}

DEFAULT_WAIT_STRATEGY = wait_exponential(multiplier=0.5, max=30.0)


def _retry_http_errors(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRY_HTTP_STATUSES
    return False


def retry(
    retry: RetryBaseT | None = None,
    wait: WaitBaseT | None = None,
    stop: StopBaseT | None = None,
    use_retry_after_header: bool = True,
    *dargs,
    **dkw
):
    if retry is None:
        retry = retry_any(
            retry_if_exception(_retry_http_errors),
            retry_if_exception_type(RETRY_NETWORK_ERRORS),
        )

    if wait is None:
        pass  # TODO

    if stop is None:
        stop = stop_after_attempt(MAX_ATTEMPTS)

    def decorator(func):
        return tenacity_retry(retry=retry, wait=wait, stop=stop, *dargs, **dkw)(func)

    return decorator


__all__ = ["retry"]
