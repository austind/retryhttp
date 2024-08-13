from datetime import datetime, timezone
from typing import Optional, Sequence, Tuple, Type, Union

from pydantic import PositiveFloat, PositiveInt
from tenacity import RetryCallState, wait_exponential, wait_random_exponential
from tenacity.wait import wait_base

from ._constants import HTTP_DATE_FORMAT
from ._utils import (
    get_default_http_status_exceptions,
    get_default_network_errors,
    get_default_timeouts,
    is_rate_limited,
    is_server_error,
)


class wait_from_header(wait_base):
    """Wait strategy that derives the wait value from an HTTP header.

    Value may be either an integer representing the number of seconds to wait
    before retrying, or a date in HTTP-date format, indicating when it is
    acceptable to retry the request. If such a date value is found, this method
    will use that value to determine the correct number of seconds to wait.

    More info on HTTP-date format: https://httpwg.org/specs/rfc9110.html#http.date

    Args:
        header (str): Header to attempt to derive wait value from.
        wait_max (float): Maximum time to wait, in seconds. Defaults to 60.0s.
        fallback (wait_base): Wait strategy to use if `header` is not present,
            or unable to parse to a `float` value, or if value parsed from header
            exceeds `wait_max`. Defaults to `None`.

    Raises:
        ValueError: If `fallback` is not provided, and any one of the following is true:
            * header is not present
            * the value cannot be parsed to a `float`
            * the value exceeds `wait_max`

    """

    def __init__(
        self,
        header: str,
        wait_max: Union[PositiveFloat, PositiveInt] = 60.0,
        fallback: Optional[wait_base] = None,
    ) -> None:
        self.header = header
        self.wait_max = float(wait_max)
        self.fallback = fallback

    def __call__(self, retry_state: RetryCallState) -> float:
        if retry_state.outcome:
            exc = retry_state.outcome.exception()
            if isinstance(exc, get_default_http_status_exceptions()):
                value = exc.response.headers.get(self.header, "")
                try:
                    return float(value)
                except ValueError:
                    pass

                try:
                    retry_after = datetime.strptime(value, HTTP_DATE_FORMAT)
                    retry_after = retry_after.replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    return float((retry_after - now).seconds)
                except ValueError:
                    pass

        return self.fallback(retry_state)


class wait_rate_limited(wait_from_header):
    """Wait strategy to use when the server responds with a `Retry-After` header.

    The `Retry-After` header may be sent with the `503 Service Unavailable` or
    `429 Too Many Requests` status code. The header value may provide a date for when
    you may retry the request, or an integer, indicating the number of seconds
    to wait before retrying.

    Args:
        fallback: Wait strategy to use if `Retry-After` header is not present, or unable
            to parse to a `float` value.

    """

    def __init__(
        self,
        fallback: wait_base = wait_exponential(),
    ) -> None:
        super().__init__(header="Retry-After", fallback=fallback)


class wait_context_aware(wait_base):
    """Uses a different wait strategy based on the type of HTTP error.

    Args:
        wait_server_errors: Wait strategy to use with server errors.
        wait_network_errors: Wait strategy to use with network errors.
        wait_timeouts: Wait strategy to use with timeouts.
        wait_rate_limited: Wait strategy to use when rate limited.
        server_error_codes: One or more 5xx HTTP status codes that will trigger
            `wait_server_errors`.
        network_errors: One or more exceptions that will trigger `wait_network_errors`.
            If omitted, defaults to:

            - `httpx.ConnectError`
            - `httpx.ReadError`
            - `httpx.WriteError`
            - `requests.ConnectionError`
            - `requests.exceptions.ChunkedEncodingError`
        timeouts: One or more exceptions that will trigger `wait_timeouts`. If omitted,
            defaults to:

            - `httpx.ConnectTimeout`
            - `httpx.ReadTimeout`
            - `httpx.WriteTimeout`
            - `requests.Timeout`

    """

    def __init__(
        self,
        wait_server_errors: wait_base = wait_random_exponential(),
        wait_network_errors: wait_base = wait_exponential(),
        wait_timeouts: wait_base = wait_random_exponential(),
        wait_rate_limited: wait_base = wait_rate_limited(),
        server_error_codes: Union[Sequence[int], int] = (500, 502, 503, 504),
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

    def __call__(self, retry_state: RetryCallState) -> float:
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
