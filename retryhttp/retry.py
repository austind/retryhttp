import tenacity
from retryhttp.helpers import (
    get_default_network_errors,
    get_default_timeouts,
    is_rate_limited,
    is_server_error,
)
from typing import Union, Type, Tuple, Sequence

from retryhttp.constants import RETRY_SERVER_ERROR_CODES


class retry_if_rate_limited(tenacity.retry_base):
    """Retry if rate limited (429 Too Many Requests)."""

    def __call__(self, retry_state: tenacity.RetryCallState) -> bool:
        if retry_state.outcome:
            return is_rate_limited(retry_state.outcome.exception())
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
            errors = get_default_network_errors()
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
            timeouts = get_default_timeouts()
        self.timeouts = timeouts
        super().__init__(exception_types=self.timeouts)


class retry_if_server_error(tenacity.retry_base):
    """Retry certain server errors (5xx).

    Args:
        server_error_codes: One or more 5xx errors to retry. Defaults to
            500, 502, 503, and 504.

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
            return is_server_error(exc, self.server_error_codes)
        return False
