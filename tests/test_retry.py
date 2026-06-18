import httpx
import httpx2
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


@retryhttp.retry
def default_args_httpx2():
    return httpx2.get(MOCK_URL)


@retryhttp.retry(max_attempt_number=2)
def retry_max_2_httpx2():
    return httpx2.get(MOCK_URL)


@retryhttp.retry(reraise=True)
def reraise_httpx2():
    return httpx2.get(MOCK_URL)


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


# pytest-httpx2 mocks at the httpcore2 layer via the standard respx router, which is
# built on the original httpx. Mocked responses must therefore be original
# httpx.Response objects (respx re-serializes them through httpcore2, and httpx2 then
# re-wraps them), while raised exceptions can be httpx2 types as they propagate directly.
def test_httpx2_default_args_success(httpx2_mock):
    route = httpx2_mock.get(MOCK_URL)
    route.side_effect = [
        httpx2.ConnectError("Mock Error"),
        httpx2.ReadTimeout("Mock Error"),
        httpx.Response(httpx.codes.OK),
    ]

    response = default_args_httpx2()

    assert route.call_count == 3
    assert response.status_code == httpx2.codes.OK


def test_httpx2_default_args_connect_error(httpx2_mock):
    route = httpx2_mock.get(MOCK_URL)
    route.side_effect = [
        httpx2.ConnectError("Mock Error"),
        httpx2.ConnectError("Mock Error"),
        httpx2.ConnectError("Mock Error"),
    ]
    with pytest.raises(RetryError):
        default_args_httpx2()

    assert route.call_count == 3


def test_httpx2_non_http_error(httpx2_mock):
    route = httpx2_mock.get(MOCK_URL)
    route.side_effect = IOError
    with pytest.raises(IOError):
        default_args_httpx2()
    assert route.call_count == 1


def test_httpx2_non_default_http_error(httpx2_mock):
    route = httpx2_mock.get(MOCK_URL).mock(side_effect=httpx2.CloseError("Mock Error"))
    with pytest.raises(httpx2.CloseError):
        default_args_httpx2()
    assert route.call_count == 1


def test_httpx2_max_attempts(httpx2_mock):
    route = httpx2_mock.get(MOCK_URL).mock(
        side_effect=[
            httpx2.ConnectError("Mock Error"),
            httpx2.ConnectTimeout("Mock Error"),
            httpx.Response(200),
        ]
    )
    with pytest.raises(RetryError):
        retry_max_2_httpx2()
    assert route.call_count == 2


def test_httpx2_reraise(httpx2_mock):
    route = httpx2_mock.get(MOCK_URL).mock(
        side_effect=[
            httpx2.ConnectError("Mock Error"),
            httpx2.ConnectError("Mock Error"),
            httpx2.ConnectError("Mock Error"),
        ]
    )
    with pytest.raises(httpx2.ConnectError):
        reraise_httpx2()
    assert route.call_count == 3
