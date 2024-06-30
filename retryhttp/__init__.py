from typing import (
    TypeVar,
    Callable,
    Any,
    Tuple,
    Type,
    Union,
    Sequence,
)

import tenacity
from retryhttp.wait import wait_rate_limited, wait_http_errors, wait_from_header
from retryhttp.retry import (
    retry_if_network_error,
    retry_if_rate_limited,
    retry_if_server_error,
    retry_if_timeout,
)
from retryhttp.helpers import get_default_network_errors, get_default_timeouts

F = TypeVar("F", bound=Callable[..., Any])


def retry(
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
    wait_rate_limited: tenacity.wait.wait_base = wait_rate_limited(),
    server_error_codes: Union[Sequence[int], int] = (
        500,
        502,
        503,
        504,
    ),
    network_errors: Union[
        Type[BaseException], Tuple[Type[BaseException], ...], None
    ] = None,
    timeouts: Union[Type[BaseException], Tuple[Type[BaseException], ...], None] = None,
    *dargs,
    **dkw,
) -> Any:
    """Retry potentially-transient HTTP errors with sensible default behavior.

    By default, retries the following errors, for a total of 3 attempts, with
    exponential backoff (except for 429 Too Many Requests, which defaults to the
    Retry-After header, if present):

    - HTTP status errors:
        - 429 Too Many Requests (rate limited)
        - 500 Internal Server Error
        - 502 Bad Gateway
        - 503 Service Unavailable
        - 504 Gateway Timeout
    - Network errors:
        - httpx.ConnectError
        - httpx.ReadError
        - httpx.WriteError
        - requests.ConnectError
    - Timeouts:
        - httpx.TimeoutException
        - requests.Timeout

    The retry, wait, and stop args for `tenacity.retry` are automatically constructed
    based on the args below. You can override any of them by passing them as keyword arguments.
    Any other positional or keyword args are passed directly to `tenacity.retry()`.

    Args:
        max_attempt_number: Total times to attempt a request.
        retry_server_errors: Whether to retry 5xx server errors.
        retry_network_errors: Whether to retry network errors.
        retry_timeouts: Whether to retry timeouts.
        retry_rate_limited: Whether to retry 429 Too Many Requests errors.
        wait_server_errors: Wait strategy to use for server errors.
        wait_network_errors: Wait strategy to use for network errors.
        wait_timeouts: Wait strategy to use for timeouts.
        wait_rate_limited: Wait strategy to use for 429 Too Many Requests errors.
        server_error_codes: One or more 5xx error codes that will trigger wait_server_errors
            if retry_server_errors is True. Defaults to 500, 502, 503, and 504.
        network_errors: One or more exceptions that will trigger wait_network_errors if
            retry_network_errors is True. Defaults to:

            - httpx.ConnectError
            - httpx.ReadError
            - httpx.WriteError
            - requests.ConnectError
        timeouts: One or more exceptions that will trigger wait_timeouts if
            retry_timeouts is True. Defaults to:

            - httpx.TimeoutException
            - requests.Timeout

    Returns:
        Decorated function.

    Raises:
        RuntimeError: if `retry_server_errors`, `retry_network_errors`, `retry_timeouts`,
            and `retry_rate_limited` are all `False`.

    """
    if network_errors is None:
        network_errors = get_default_network_errors()
    if timeouts is None:
        timeouts = get_default_timeouts()

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
    "retry",
    "retry_if_network_error",
    "retry_if_timeout",
    "retry_if_rate_limited",
    "retry_if_server_error",
    "wait_http_errors",
    "wait_from_header",
    "wait_rate_limited",
]
