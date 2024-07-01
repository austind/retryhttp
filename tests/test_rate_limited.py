import httpx
import pytest
import respx
from tenacity import RetryError, retry, stop_after_attempt

from retryhttp import retry_if_rate_limited, wait_rate_limited

MOCK_URL = "https://example.com/"


def rate_limited_response(retry_after: int = 1):
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
            rate_limited_response(),
            rate_limited_response(),
            rate_limited_response(),
        ]
    )
    with pytest.raises(RetryError):
        retry_rate_limited()
    assert route.call_count == 3
    assert route.calls[2].response.status_code == 429


@respx.mock
def test_rate_limited_success():
    route = respx.get(MOCK_URL).mock(
        side_effect=[
            rate_limited_response(),
            rate_limited_response(),
            httpx.Response(200),
        ]
    )
    response = retry_rate_limited()
    assert route.calls[0].response.status_code == 429
    assert route.calls[1].response.status_code == 429
    assert response.status_code == 200
    assert route.call_count == 3
