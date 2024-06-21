import httpx
from tenacity import RetryBaseT, RetryCallState, StopBaseT, WaitBaseT
from tenacity import retry as tenacity_retry
from tenacity import (retry_any, retry_if_exception, retry_if_exception_type,
                      stop_after_attempt, wait_combine, wait_exponential)
from tenacity._utils import time_unit_type
from tenacity.wait import wait_base

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


def _retry_http_errors(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRY_HTTP_STATUSES
    return False


class retry_if_rate_limited:
    pass


class retry_if_network_error:
    pass


class retry_status_code:
    pass


class wait_from_header(wait_base):
    """Wait strategy that derives the value from an HTTP header, if present.

    Default is used if header is not present.
    """

    def __init__(
        self, header: str = "Retry-After", default: time_unit_type = 1.0
    ) -> None:
        self.header = header
        self.default = default

    def __call__(self, retry_state: RetryCallState) -> float:
        exc = retry_state.outcome.exception()
        if isinstance(exc, httpx.HTTPStatusError):
            return float(exc.response.headers.get(self.header, self.default))
        return self.default


def retry(
    retry: RetryBaseT | None = None,
    wait: WaitBaseT | None = None,
    stop: StopBaseT | None = None,
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
