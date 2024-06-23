from tenacity import retry, stop_after_attempt
import httpx
from tenacity_httpx import retry_if_rate_limited, wait_from_header
import respx

MOCK_URL = "https://example.com/"


def rate_limited_response(retry_after: int = 1):
    return httpx.Response(
        status_code=httpx.codes.TOO_MANY_REQUESTS,
        headers={"Retry-After": str(retry_after)},
    )


@retry(
    retry=retry_if_rate_limited(),
    wait=wait_from_header(header="Retry-After"),
    stop=stop_after_attempt(3),
)
def retry_rate_limited():
    response = httpx.get(MOCK_URL)
    response.raise_for_status()
    return response


@respx.mock
def test_rate_limited_success():
    route = respx.get(MOCK_URL).mock(
        side_effect=[
            rate_limited_response(retry_after=1),
            rate_limited_response(retry_after=1),
            httpx.Response(200),
        ]
    )
    response = retry_rate_limited()
    assert response.status_code == 200
    assert route.call_count == 3
