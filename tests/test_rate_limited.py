from typing import Union

import httpx
import pytest
import respx
from pydantic import PositiveInt
from tenacity import RetryError, retry, stop_after_attempt

from retryhttp import retry_if_rate_limited, wait_rate_limited
from retryhttp._types import HTTPDate
from retryhttp._utils import get_http_date

MOCK_URL = "https://example.com/"


def rate_limited_response(retry_after: Union[HTTPDate, PositiveInt] = 1):
    return httpx.Response(
        status_code=httpx.codes.TOO_MANY_REQUESTS,
        headers={"Retry-After": str(retry_after)},
    )


@retry(
    retry=retry_if_rate_limited(),
    wait=wait_rate_limited(),
    stop=stop_after_attempt(3),
)
def retry_rate_limited():
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
        retry_rate_limited()
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
        retry_rate_limited()
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
    response = retry_rate_limited()
    assert route.calls[0].response.status_code == 429
    assert route.calls[1].response.status_code == 429
    assert route.calls[1].response.headers.get("retry-after") == http_date
    assert response.status_code == 200
    assert response.headers.get("retry-after") is None
    assert route.call_count == 3
