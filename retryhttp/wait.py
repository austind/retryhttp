import tenacity
from typing import Tuple, Type, Union, Sequence
from retryhttp.helpers import (
    get_default_http_status_exceptions,
    get_default_network_errors,
    get_default_timeouts,
    is_server_error,
    is_rate_limited,
)


class wait_from_header(tenacity.wait.wait_base):
    """Wait strategy that derives the value from an HTTP header, if present.

    Args:
        header: Header to attempt to derive wait value from.
        fallback: Wait strategy to use if `header` is not present, or unable
            to parse to a `float` value.

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
            if isinstance(exc, get_default_http_status_exceptions()):
                try:
                    return float(
                        exc.response.headers.get(
                            self.header, self.fallback(retry_state)
                        )
                    )
                except ValueError:
                    pass
        return self.fallback(retry_state)


class wait_rate_limited(wait_from_header):
    """Wait strategy to use with 429 Too Many Requests.

    Args:
        header: Header to attempt to derive wait value from.
        fallback: Wait strategy to use if `header` is not present, or unable
            to parse to a `float` value.

    """

    def __init__(
        self,
        header: str = "Retry-After",
        fallback: tenacity.wait.wait_base = tenacity.wait_exponential_jitter(
            initial=1, max=15
        ),
    ) -> None:
        super().__init__(header, fallback)


class wait_http_errors(tenacity.wait.wait_base):
    """Context-aware wait strategy based on the type of HTTP error.

    Args:
        wait_server_errors: Wait strategy to use with server errors.
        wait_network_errors: Wait strategy to use with network errors.
        wait_timeouts: Wait strategy to use with timeouts.
        wait_rate_limited: Wait strategy to use with 429 Too Many Requests.
        server_error_codes: One or more 5xx HTTP status codes to consider for
            `wait_server_errors`. If omitted, defaults to:

            - 500
            - 502
            - 503
            - 504
        network_errors: One or more exceptions to consider for `wait_network_errors`.
            If omitted, defaults to:

            - httpx.ConnectError
            - httpx.ReadError
            - httpx.WriteError
            - requests.ConnectionError
        timeouts: One or more exceptions to consider for `wait_timeouts`. If omitted,
            defaults to:

            - httpx.ConnectTimeout
            - httpx.ReadTimeout
            - httpx.WriteTimeout
            - requests.Timeout
    """

    def __init__(
        self,
        wait_server_errors: tenacity.wait.wait_base = tenacity.wait_exponential_jitter(),
        wait_network_errors: tenacity.wait.wait_base = tenacity.wait_exponential(),
        wait_timeouts: tenacity.wait.wait_base = tenacity.wait_exponential_jitter(),
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
        timeouts: Union[
            Type[BaseException], Tuple[Type[BaseException], ...], None
        ] = None,
    ) -> None:
        if network_errors is None:
            network_errors = get_default_network_errors()
        if timeouts is None:
            timeouts = get_default_timeouts()
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
            if is_server_error(exc=exc, status_codes=self.server_error_codes):
                return self.wait_server_errors(retry_state)
            if isinstance(exc, self.network_errors):
                return self.wait_network_errors(retry_state)
            if isinstance(exc, self.timeouts):
                return self.wait_timeouts(retry_state)
            if is_rate_limited(exc):
                return self.wait_rate_limited(retry_state)
        return 0
