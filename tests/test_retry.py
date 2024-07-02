import httpx
import pytest
import respx
from tenacity import RetryError

import retryhttp

MOCK_URL = "https://example.com/"


@retryhttp.retry
def default_args():
    return httpx.get(MOCK_URL)


@retryhttp.retry(max_attempt_number=2)
def retry_max_2():
    return httpx.get(MOCK_URL)


@retryhttp.retry(reraise=True)
def reraise():
    return httpx.get(MOCK_URL)


@respx.mock
def test_default_args_success():
    route = respx.get(MOCK_URL)
    route.side_effect = [
        httpx.ConnectError,
        httpx.ReadTimeout,
        httpx.Response(httpx.codes.OK),
    ]

    response = default_args()

    assert route.call_count == 3
    assert response.status_code == httpx.codes.OK


@respx.mock
def test_default_args_connect_error():
    route = respx.get(MOCK_URL)
    route.side_effect = [
        httpx.ConnectError,
        httpx.ConnectError,
        httpx.ConnectError,
    ]
    with pytest.raises(RetryError):
        default_args()

    assert route.call_count == 3


@respx.mock
def test_non_http_error():
    route = respx.get(MOCK_URL)
    route.side_effect = IOError
    with pytest.raises(IOError):
        default_args()
    assert route.call_count == 1


@respx.mock
def test_non_default_http_error():
    route = respx.get(MOCK_URL).mock(side_effect=httpx.CloseError)
    with pytest.raises(httpx.CloseError):
        default_args()
    assert route.call_count == 1


@respx.mock
def test_max_attempts():
    route = respx.get(MOCK_URL).mock(
        side_effect=[httpx.ConnectError, httpx.ConnectTimeout, httpx.Response(200)]
    )
    with pytest.raises(RetryError):
        retry_max_2()
    assert route.call_count == 2


@respx.mock
def test_reraise():
    route = respx.get(MOCK_URL).mock(
        side_effect=[httpx.ConnectError, httpx.ConnectError, httpx.ConnectError]
    )
    with pytest.raises(httpx.ConnectError):
        reraise()
    assert route.call_count == 3
