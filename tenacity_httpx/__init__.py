import typing

import httpx
import tenacity
from tenacity.retry import retry_base
from tenacity.wait import wait_base

# Default maximum attempts.
MAX_ATTEMPTS = 3

# Potentially transient HTTP 5xx error statuses to retry.
RETRY_SERVER_ERROR_CODES = {
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


def _is_rate_limited(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == httpx.codes.TOO_MANY_REQUESTS
    return False


def _is_server_error(
    exc: BaseException,
    error_status_codes: typing.Union[typing.Tuple[int], typing.List[int]],
) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        return status_code in error_status_codes


class retry_if_rate_limited(retry_base):
    """Retry if rate limited (429 Too Many Requests)."""

    def __call__(self, retry_state: tenacity.RetryCallState) -> bool:
        exc = retry_state.outcome.exception()
        return _is_rate_limited(exc)


class retry_if_network_error(retry_base):
    """Retry network errors."""

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
    """Retry network timeouts."""

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


class retry_if_server_error(retry_base):
    """Retry server errors (5xx).

    Accepts a list or tuple of status codes to retry (4xx or 5xx only).
    """

    def __init__(
        self,
        error_status_codes: typing.Union[
            typing.List[int], typing.Tuple[int], None
        ] = None,
    ) -> None:
        if error_status_codes is None:
            error_status_codes = RETRY_SERVER_ERROR_CODES
        self.error_status_codes = error_status_codes

    def __call__(self, retry_state: tenacity.RetryCallState) -> bool:
        exc = retry_state.outcome.exception()
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in self.error_status_codes
        return False


class wait_from_header(tenacity.wait.wait_base):
    """Wait strategy that derives the value from an HTTP header, if present.

    Default is used if header is not present.
    """

    def __init__(
        self, header: str, fallback: wait_base = tenacity.wait_exponential_jitter()
    ) -> None:
        self.header = header
        self.fallback = fallback

    def __call__(self, retry_state: tenacity.RetryCallState) -> float:
        exc = retry_state.outcome.exception()
        if isinstance(exc, httpx.HTTPStatusError):
            return float(
                exc.response.headers.get(self.header, self.fallback(retry_state))
            )
        return self.fallback(retry_state)


class wait_context_aware(wait_base):
    """Applies different wait strategies based on the type of error."""

    def __init__(
        self,
        wait_server_errors: wait_base = tenacity.wait_exponential_jitter(),
        wait_network_errors: wait_base = tenacity.wait_exponential(),
        wait_network_timeouts: wait_base = tenacity.wait_exponential_jitter(),
        wait_rate_limited: wait_base = wait_from_header(header="Retry-After"),
        error_status_codes: typing.Union[typing.Tuple[int], int, None] = None,
        network_errors: typing.Union[typing.Tuple[BaseException], None] = None,
        network_timeouts: typing.Union[typing.Tuple[BaseException], None] = None,
    ) -> None:
        if server_errors is None:
            server_errors = RETRY_SERVER_ERROR_CODES
        if network_errors is None:
            network_errors = RETRY_NETWORK_ERRORS
        if network_timeouts is None:
            network_timeouts = RETRY_NETWORK_TIMEOUTS
        self.wait_server_errors = wait_server_errors
        self.wait_network_errors = wait_network_errors
        self.wait_network_timeouts = wait_network_timeouts
        self.wait_rate_limited = wait_rate_limited
        self.error_status_codes = error_status_codes
        self.network_errors = network_errors
        self.network_timeouts = network_timeouts

    def __call__(self, retry_state: tenacity.RetryCallState) -> float:
        exc = retry_state.outcome.exception()
        if _is_server_error(exc=exc, error_status_codes=self.error_status_codes):
            return self.wait_server_errors(retry_state)
        elif isinstance(exc, self.network_errors):
            return self.wait_network_errors(retry_state)
        elif isinstance(exc, self.network_timeouts):
            return self.wait_network_timeouts(retry_state)
        elif _is_rate_limited(exc):
            return self.wait_rate_limited(retry_state)
        else:
            return 0


def retry_http_failures(
    max_attempt_number: int = 3,
    retry_server_errors: bool = True,
    retry_network_errors: bool = True,
    retry_network_timeouts: bool = True,
    retry_rate_limited: bool = True,
    wait_server_errors: wait_base = tenacity.wait_exponential_jitter(),
    wait_network_errors: wait_base = tenacity.wait_exponential(),
    wait_network_timeouts: wait_base = tenacity.wait_exponential_jitter(),
    wait_rate_limited: wait_base = wait_from_header("Retry-After"),
    server_errors: typing.Union[int, typing.Tuple[int], typing.List[int], None] = None,
    network_errors: typing.Union[
        BaseException, typing.Tuple[BaseException], None
    ] = None,
    network_timeouts: typing.Union[
        BaseException, typing.Tuple[BaseException], None
    ] = None,
    *dargs,
    **dkw,
):
    if server_errors is None:
        server_errors = RETRY_SERVER_ERROR_CODES
    if network_errors is None:
        network_errors = RETRY_NETWORK_ERRORS
    if network_timeouts is None:
        network_timeouts = RETRY_NETWORK_TIMEOUTS

    retry_strategies = []
    if retry_server_errors:
        retry_strategies.append(
            retry_if_server_error(server_errors=retry_server_errors)
        )
    if retry_network_errors:
        retry_strategies.append(retry_if_network_error(errors=network_errors))
    if retry_network_timeouts:
        retry_strategies.append(retry_if_network_timeout(timeouts=network_timeouts))
    if retry_rate_limited:
        retry_strategies.append(retry_if_rate_limited())

    retry = dkw.get("retry") or tenacity.retry_any(*retry_strategies)

    # We don't need to conditionally build our wait strategy since each strategy
    # will only apply if the corresponding retry strategy is in use.
    wait = dkw.get("wait") or wait_context_aware(
        wait_server_errors=wait_server_errors,
        wait_network_errors=wait_network_errors,
        wait_network_timeouts=wait_network_timeouts,
        wait_rate_limited=wait_rate_limited,
    )

    stop = dkw.get("stop") or tenacity.stop_after_attempt(max_attempt_number)

    def decorator(func):
        return tenacity.retry(retry=retry, wait=wait, stop=stop, *dargs, **dkw)(func)

    return decorator


__all__ = ["retry"]
