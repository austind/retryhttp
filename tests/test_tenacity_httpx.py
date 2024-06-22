import httpx


def test_retry_http_errors(respx_mock):
    respx_mock.get("https://example.com/").mock(return_value=httpx.Response(200))
    response = httpx.get("https://example.com/")
    assert response.status_code == 200
