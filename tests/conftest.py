from typing import Union

import httpx
from pydantic import PositiveInt

from retryhttp._types import HTTPDate

MOCK_URL = "https://example.com/"


def get_url(url: str = MOCK_URL) -> httpx.Response:
    response = httpx.get(url=url)
    response.raise_for_status()
    return response


def scheduled_downtime_response(retry_after: Union[HTTPDate, PositiveInt] = 1):
    return httpx.Response(
        status_code=httpx.codes.SERVICE_UNAVAILABLE,
        headers={"Retry-After": str(retry_after)},
    )


def rate_limited_response(retry_after: Union[HTTPDate, PositiveInt] = 1):
    return httpx.Response(
        status_code=429,
        headers={"Retry-After": str(retry_after)},
    )
