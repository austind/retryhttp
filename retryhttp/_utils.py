from typing import Optional, Sequence, Tuple, Type, Union

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


def get_default_network_errors() -> (
    Tuple[Union[Type[httpx.NetworkError], Type[requests.ConnectionError]], ...]
):
    """Get all network errors to use by default.

    Args:
        N/A

    Returns:
        Tuple of network error exceptions.

    Raises:
        N/A

    """
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
        exceptions.extend(
            [
                requests.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
            ]
        )
    return tuple(exceptions)


def get_default_timeouts() -> (
    Tuple[Type[Union[httpx.TimeoutException, requests.Timeout]], ...]
):
    """Get all timeout exceptions to use by default.

    Returns:
        tuple: Timeout exceptions.

    """
    exceptions = []
    if _HTTPX_INSTALLED:
        exceptions.append(httpx.TimeoutException)
    if _REQUESTS_INSTALLED:
        exceptions.append(requests.Timeout)
    return tuple(exceptions)


def get_default_http_status_exceptions() -> (
    Tuple[Union[Type[httpx.HTTPStatusError], Type[requests.HTTPError]], ...]
):
    """Get default HTTP status 4xx or 5xx exceptions.

    Returns:
        tuple: HTTP status exceptions.

    """
    exceptions = []
    if _HTTPX_INSTALLED:
        exceptions.append(httpx.HTTPStatusError)
    if _REQUESTS_INSTALLED:
        exceptions.append(requests.HTTPError)
    return tuple(exceptions)


def is_rate_limited(exc: Union[BaseException, None]) -> bool:
    """Whether a given exception indicates the user has been rate limited.

    Rate limiting should return a `429 Too Many Requests` status, but in
    practice, servers may return `503 Service Unavailable`, or possibly
    another code. In any case, if rate limiting is the issue, the server
    will include a `Retry-After` header.

    Args:
        exc: Exception to consider.

    Returns:
        bool: Whether exc indicates rate limiting.

    """
    if isinstance(exc, get_default_http_status_exceptions()):
        return "retry-after" in exc.response.headers.keys()
    return False


def is_server_error(
    exc: Optional[BaseException],
    status_codes: Union[Sequence[int], int] = tuple(range(500, 600)),
) -> bool:
    """Whether a given exception indicates a 5xx server error.

    Args:
        exc: Exception to consider.
        status_codes: One or more 5xx status codes to consider. Defaults
            to all (500-599).

    Returns:
        bool: whether exc indicates an error included in status_codes.

    """
    if isinstance(status_codes, int):
        status_codes = [status_codes]
    if isinstance(exc, get_default_http_status_exceptions()):
        return exc.response.status_code in status_codes
    return False
