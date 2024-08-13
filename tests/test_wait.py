import httpx
import pytest
import respx
from tenacity import retry, stop_after_attempt, wait_exponential

from retryhttp import retry_if_server_error, wait_from_header
from retryhttp._utils import get_http_date

from .conftest import MOCK_URL, scheduled_downtime_response


@retry(
    retry=retry_if_server_error(),
    wait=wait_from_header(header="Retry-After", wait_max=5),
    stop=stop_after_attempt(3),
)
def planned_downtime_impatient_no_fallback():
    response = httpx.get(MOCK_URL)
    response.raise_for_status()
    return response


@retry(
    retry=retry_if_server_error(),
    wait=wait_from_header(
        header="Retry-After", wait_max=5, fallback=wait_exponential()
    ),
    stop=stop_after_attempt(3),
)
def planned_downtime_impatient_fallback():
    response = httpx.get(MOCK_URL)
    response.raise_for_status()
    return response


@respx.mock
def test_wait_from_header():
    http_date = get_http_date(delta_seconds=3)
    route = respx.get(MOCK_URL).mock(
        side_effect=[
            scheduled_downtime_response(retry_after=1),
            scheduled_downtime_response(retry_after=http_date),
            httpx.Response(200),
        ]
    )
    response = planned_downtime_impatient_no_fallback()
    assert response.status_code == 200
    assert route.call_count == 3
    assert route.calls[0].response.status_code == 503
    assert route.calls[0].response.headers.get("retry-after") == "1"
    assert route.calls[1].response.headers.get("retry-after") == http_date


@respx.mock
def test_wait_from_header_max_wait():
    http_date = get_http_date(delta_seconds=20)
    route = respx.get(MOCK_URL).mock(
        side_effect=[scheduled_downtime_response(retry_after=http_date)]
    )
    with pytest.raises(ValueError):
        planned_downtime_impatient_no_fallback()
    assert route.called is True


@respx.mock
def test_wait_from_header_fallback():
    route = respx.get(MOCK_URL).mock(
        side_effect=[scheduled_downtime_response(retry_after=6), httpx.Response(200)],
    )
    response = planned_downtime_impatient_fallback()
    assert response.status_code == 200
    assert route.called is True
