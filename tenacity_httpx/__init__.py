import typing

import httpx
import tenacity
from tenacity.retry import retry_base

# Default maximum attempts.
MAX_ATTEMPTS = 3

# Potentially transient HTTP error statuses to retry.
RETRY_HTTP_STATUSES = {
    httpx.codes.TOO_MANY_REQUESTS,
    httpx.codes.INTERNAL_SERVER_ERROR,
    httpx.codes.BAD_GATEWAY,
    httpx.codes.GATEWAY_TIMEOUT,
    httpx.codes.SERVICE_UNAVAILABLE,
}

# Potentially transient network errors to retry.
# We could just use httpx.NetworkError, but since httpx.CloseError isn't
# usually important to retry, we use these instead.
RETRY_NETWORK_ERRORS = {
    httpx.ConnectError,
    httpx.ReadError,
    httpx.WriteError,
}

RETRY_NETWORK_TIMEOUTS = {
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
}


class retry_if_rate_limited(retry_base):
    """Retry if rate limited (429 Too Many Requests)."""
    def __call__(self, retry_state: tenacity.RetryCallState) -> bool:
        exc = retry_state.outcome.exception()
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code == httpx.codes.TOO_MANY_REQUESTS
        return False


class retry_if_network_error(retry_base):
    def __init__(
        self,
        errors: typing.Union[
            typing.List[BaseException], typing.Tuple[BaseException], None
        ] = None,
    ) -> None:
        if errors is None:
            errors = RETRY_NETWORK_ERRORS
        self.errors = errors

    def __call__(self, retry_state: tenacity.RetryCallState) -> bool:
        exc = retry_state.outcome.exception()
        return exc in self.errors


class retry_if_network_timeout(retry_base):
    def __init__(
        self,
        timeouts: typing.Union[
            typing.List[BaseException], typing.Tuple[BaseException], None
        ] = None,
    ) -> None:
        if timeouts is None:
            timeouts = RETRY_NETWORK_TIMEOUTS
        self.timeouts = timeouts

    def __call__(self, retry_state: tenacity.RetryCallState) -> bool:
        exc = retry_state.outcome.exception()
        return exc in self.timeouts


class retry_status_code(retry_base):
    """Retry strategy based on HTTP status code.

    Accepts a list or tuple of status codes to retry (4xx or 5xx only).
    """

    def __init__(
        self,
        status_codes: typing.Union[typing.List[int], typing.Tuple[int], None] = None,
    ) -> None:
        if status_codes is None:
            status_codes = RETRY_HTTP_STATUSES
        self.status_codes = status_codes

    def __call__(self, retry_state: tenacity.RetryCallState) -> bool:
        exc = retry_state.outcome.exception()
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in self.status_codes
        return False


class wait_from_header(tenacity.wait.wait_base):
    """Wait strategy that derives the value from an HTTP header, if present.

    Default is used if header is not present.
    """

    def __init__(
        self, header: str = "Retry-After", default: tenacity._utils.time_unit_type = 1.0
    ) -> None:
        self.header = header
        self.default = default

    def __call__(self, retry_state: tenacity.RetryCallState) -> float:
        exc = retry_state.outcome.exception()
        if isinstance(exc, httpx.HTTPStatusError):
            return float(exc.response.headers.get(self.header, self.default))
        return self.default


def retry(
    retry: typing.Union[tenacity.RetryBaseT, None] = None,
    wait: typing.Union[tenacity.WaitBaseT, None] = None,
    stop: typing.Union[tenacity.StopBaseT, None] = None,
    *dargs,
    **dkw,
):
    if retry is None:
        retry = tenacity.retry_any(
            tenacity.retry_if_exception(_retry_http_errors),
            tenacity.retry_if_exception_type(RETRY_NETWORK_ERRORS),
        )

    if wait is None:
        pass  # TODO

    if stop is None:
        stop = tenacity.stop_after_attempt(MAX_ATTEMPTS)

    def decorator(func):
        return tenacity.retry(retry=retry, wait=wait, stop=stop, *dargs, **dkw)(func)

    return decorator


__all__ = ["retry"]
