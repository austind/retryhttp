from typing import (
    TypeVar,
    Callable,
    Any,
    Tuple,
    Type,
    Union,
    Optional,
    Sequence,
)

import tenacity

_HTTPX_INSTALLED = False
_REQUESTS_INSTALLED = False

try:
    import httpx

    _HTTPX_INSTALLED = True
except ImportError:
    pass

try:
    import requests

    _REQUESTS_INSTALLED = True
except ImportError:
    pass

F = TypeVar("F", bound=Callable[..., Any])


# Potentially transient HTTP 5xx error statuses to retry.
RETRY_SERVER_ERROR_CODES = (
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
)


def _get_default_network_errors() -> (
    Tuple[Union[Type[httpx.NetworkError], Type[requests.ConnectionError]], ...]
):
    exceptions = []
    if _HTTPX_INSTALLED:
        exceptions.extend(
            [
                httpx.ConnectError,
                httpx.ReadError,
                httpx.WriteError,
            ]
        )
    if _REQUESTS_INSTALLED:
        exceptions.append(requests.ConnectionError)
    return tuple(exceptions)


def _get_default_timeouts() -> (
    Tuple[Type[Union[httpx.TimeoutException, requests.Timeout]], ...]
):
    exceptions = []
    if _HTTPX_INSTALLED:
        exceptions.append(httpx.TimeoutException)
    if _REQUESTS_INSTALLED:
        exceptions.append(requests.Timeout)
    return tuple(exceptions)


def _get_default_http_status_exceptions() -> (
    Tuple[Union[Type[httpx.HTTPStatusError], Type[requests.HTTPError]], ...]
):
    """Get default HTTP status 4xx or 5xx exceptions."""
    exceptions = []
    if _HTTPX_INSTALLED:
        exceptions.append(httpx.HTTPStatusError)
    if _REQUESTS_INSTALLED:
        exceptions.append(requests.HTTPError)
    return tuple(exceptions)


def _is_rate_limited(exc: Union[BaseException, None]) -> bool:
    """Whether a given exception indicates a 429 Too Many Requests error."""
    if isinstance(exc, _get_default_http_status_exceptions()):
        return exc.response.status_code == 429
    return False


def _is_server_error(
    exc: Optional[BaseException],
    status_codes: Union[Sequence[int], int] = tuple(range(500, 600)),
) -> bool:
    """Whether a given exception indicates a 5xx server error."""
    if isinstance(status_codes, int):
        status_codes = [status_codes]
    if isinstance(exc, _get_default_http_status_exceptions()):
        return exc.response.status_code in status_codes
    return False


class retry_if_rate_limited(tenacity.retry_base):
    """Retry if rate limited (429 Too Many Requests)."""

    def __call__(self, retry_state: tenacity.RetryCallState) -> bool:
        if retry_state.outcome:
            return _is_rate_limited(retry_state.outcome.exception())
        return False


class retry_if_network_error(tenacity.retry_if_exception_type):
    """Retry network errors."""

    def __init__(
        self,
        errors: Union[
            Type[BaseException], Tuple[Type[BaseException], ...], None
        ] = None,
    ) -> None:
        if errors is None:
            errors = _get_default_network_errors()
        self.errors = errors
        super().__init__(exception_types=self.errors)


class retry_if_timeout(tenacity.retry_if_exception_type):
    """Retry timeouts."""

    def __init__(
        self,
        timeouts: Union[
            Type[BaseException], Tuple[Type[BaseException], ...], None
        ] = None,
    ) -> None:
        if timeouts is None:
            timeouts = _get_default_timeouts()
        self.timeouts = timeouts
        super().__init__(exception_types=self.timeouts)


class retry_if_server_error(tenacity.retry_base):
    """Retry certain server errors (5xx).

    Accepts a list or tuple of status codes to retry (5xx only).
    """

    def __init__(
        self,
        server_error_codes: Union[Sequence[int], int, None] = None,
    ) -> None:
        if server_error_codes is None:
            server_error_codes = RETRY_SERVER_ERROR_CODES
        self.server_error_codes = server_error_codes

    def __call__(self, retry_state: tenacity.RetryCallState) -> bool:
        if retry_state.outcome:
            exc = retry_state.outcome.exception()
            return _is_server_error(exc, self.server_error_codes)
        return False


class wait_from_header(tenacity.wait.wait_base):
    """Wait strategy that derives the value from an HTTP header, if present.

    Fallback is used if header is not present.
    """

    def __init__(
        self,
        header: str,
        fallback: tenacity.wait.wait_base = tenacity.wait_exponential_jitter(
            initial=1, max=15
        ),
    ) -> None:
        self.header = header
        self.fallback = fallback

    def __call__(self, retry_state: tenacity.RetryCallState) -> float:
        if retry_state.outcome:
            exc = retry_state.outcome.exception()
            if isinstance(exc, _get_default_http_status_exceptions()):
                try:
                    return float(
                        exc.response.headers.get(
                            self.header, self.fallback(retry_state)
                        )
                    )
                except ValueError:
                    pass
        return self.fallback(retry_state)


class wait_retry_after_header(wait_from_header):
    def __init__(
        self,
        header: str = "Retry-After",
        fallback: tenacity.wait.wait_base = tenacity.wait_exponential_jitter(
            initial=1, max=15
        ),
    ) -> None:
        super().__init__(header, fallback)


class wait_http_errors(tenacity.wait.wait_base):
    """Context-aware wait strategy based on the type of HTTP error."""

    def __init__(
        self,
        wait_server_errors: tenacity.wait.wait_base = tenacity.wait_exponential_jitter(),
        wait_network_errors: tenacity.wait.wait_base = tenacity.wait_exponential(),
        wait_timeouts: tenacity.wait.wait_base = tenacity.wait_exponential_jitter(),
        wait_rate_limited: tenacity.wait.wait_base = wait_retry_after_header(),
        server_error_codes: Union[Sequence[int], int] = RETRY_SERVER_ERROR_CODES,
        network_errors: Union[
            Type[BaseException], Tuple[Type[BaseException], ...], None
        ] = None,
        timeouts: Union[
            Type[BaseException], Tuple[Type[BaseException], ...], None
        ] = None,
    ) -> None:
        if network_errors is None:
            network_errors = _get_default_network_errors()
        if timeouts is None:
            timeouts = _get_default_timeouts()
        self.wait_server_errors = wait_server_errors
        self.wait_network_errors = wait_network_errors
        self.wait_timeouts = wait_timeouts
        self.wait_rate_limited = wait_rate_limited
        self.server_error_codes = server_error_codes
        self.network_errors = network_errors
        self.timeouts = timeouts

    def __call__(self, retry_state: tenacity.RetryCallState) -> float:
        if retry_state.outcome:
            exc = retry_state.outcome.exception()
            if _is_server_error(exc=exc, status_codes=self.server_error_codes):
                return self.wait_server_errors(retry_state)
            if isinstance(exc, self.network_errors):
                return self.wait_network_errors(retry_state)
            if isinstance(exc, self.timeouts):
                return self.wait_timeouts(retry_state)
            if _is_rate_limited(exc):
                return self.wait_rate_limited(retry_state)
        return 0


def retry_http_errors(
    max_attempt_number: int = 3,
    retry_server_errors: bool = True,
    retry_network_errors: bool = True,
    retry_timeouts: bool = True,
    retry_rate_limited: bool = True,
    wait_server_errors: tenacity.wait.wait_base = tenacity.wait_exponential_jitter(
        initial=1, max=15
    ),
    wait_network_errors: tenacity.wait.wait_base = tenacity.wait_exponential(
        multiplier=1, max=15
    ),
    wait_timeouts: tenacity.wait.wait_base = tenacity.wait_exponential_jitter(
        initial=1, max=15
    ),
    wait_rate_limited: tenacity.wait.wait_base = wait_retry_after_header(),
    server_error_codes: Union[Sequence[int], int] = RETRY_SERVER_ERROR_CODES,
    network_errors: Union[
        Type[BaseException], Tuple[Type[BaseException], ...], None
    ] = None,
    timeouts: Union[Type[BaseException], Tuple[Type[BaseException], ...], None] = None,
    *dargs,
    **dkw,
) -> Any:
    """Retry potentially-transient HTTP errors with sensible default behavior.

    Wraps retry() with retry, wait, and stop strategies optimized for
    retrying potentially-transient HTTP errors with sensible defaults, which are
    all configurable.

    """
    if network_errors is None:
        network_errors = _get_default_network_errors()
    if timeouts is None:
        timeouts = _get_default_timeouts()

    retry_strategies = []
    if retry_server_errors:
        retry_strategies.append(
            retry_if_server_error(server_error_codes=server_error_codes)
        )
    if retry_network_errors:
        retry_strategies.append(retry_if_network_error(errors=network_errors))
    if retry_timeouts:
        retry_strategies.append(retry_if_timeout(timeouts=timeouts))
    if retry_rate_limited:
        retry_strategies.append(retry_if_rate_limited())
    if not retry_strategies:
        raise RuntimeError("No retry strategies enabled.")

    retry = dkw.get("retry") or tenacity.retry_any(*retry_strategies)

    # We don't need to conditionally build our wait strategy since each strategy
    # will only apply if the corresponding retry strategy is in use.
    wait = dkw.get("wait") or wait_http_errors(
        wait_server_errors=wait_server_errors,
        wait_network_errors=wait_network_errors,
        wait_timeouts=wait_timeouts,
        wait_rate_limited=wait_rate_limited,
    )

    stop = dkw.get("stop") or tenacity.stop_after_attempt(max_attempt_number)

    def decorator(func: F) -> F:
        return tenacity.retry(retry=retry, wait=wait, stop=stop, *dargs, **dkw)(func)

    return decorator


__all__ = [
    "retry_http_errors",
    "wait_http_errors",
]
