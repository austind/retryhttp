import httpx
import pytest
import respx
from tenacity import RetryError, retry, stop_after_attempt

from retryhttp import retry_if_rate_limited, wait_retry_after
from retryhttp._utils import get_http_date

from .conftest import MOCK_URL, rate_limited_response


@retry(
    retry=retry_if_rate_limited(),
    wait=wait_retry_after(),
    stop=stop_after_attempt(3),
)
def rate_limited_request():
    response = httpx.get(MOCK_URL)
    response.raise_for_status()
    return response


@respx.mock
def test_rate_limited_failure():
    route = respx.get(MOCK_URL).mock(
        side_effect=[
            rate_limited_response(retry_after=1),
            rate_limited_response(retry_after=1),
            rate_limited_response(retry_after=1),
        ]
    )
    with pytest.raises(RetryError):
        rate_limited_request()
    assert route.call_count == 3
    assert route.calls[2].response.status_code == 429


@respx.mock
def test_rate_limited_failure_httpdate():
    http_date_2sec = get_http_date(delta_seconds=2)
    http_date_3sec = get_http_date(delta_seconds=3)
    http_date_4sec = get_http_date(delta_seconds=4)
    route = respx.get(MOCK_URL).mock(
        side_effect=[
            rate_limited_response(retry_after=http_date_2sec),
            rate_limited_response(retry_after=http_date_3sec),
            rate_limited_response(retry_after=http_date_4sec),
        ]
    )
    with pytest.raises(RetryError):
        rate_limited_request()
    assert route.call_count == 3
    assert route.calls[0].response.status_code == 429
    assert route.calls[0].response.headers.get("retry-after") == http_date_2sec
    assert route.calls[1].response.status_code == 429
    assert route.calls[1].response.headers.get("retry-after") == http_date_3sec
    assert route.calls[2].response.status_code == 429
    assert route.calls[2].response.headers.get("retry-after") == http_date_4sec


@respx.mock
def test_rate_limited_success():
    http_date = get_http_date(delta_seconds=2)
    route = respx.get(MOCK_URL).mock(
        side_effect=[
            rate_limited_response(retry_after=1),
            rate_limited_response(retry_after=http_date),
            httpx.Response(200),
        ]
    )
    response = rate_limited_request()
    assert route.calls[0].response.status_code == 429
    assert route.calls[1].response.status_code == 429
    assert route.calls[1].response.headers.get("retry-after") == http_date
    assert response.status_code == 200
    assert response.headers.get("retry-after") is None
    assert route.call_count == 3
