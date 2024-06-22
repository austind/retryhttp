# tenacity_httpx

Retry potentially-transient errors with tenacity and httpx.

*Note*: This project is in beta status. The API may change significantly.

## Quickstart

Install from git:

```bash
pip install git+https://github.com/austind/tenacity-httpx.git@main
```

This example attempts the request up to 3 times if:

* The response status code is:
  * 429 Too Many Requests
  * 500 Internal Server Error
  * 502 Bad Gateway
  * 503 Service Unavailable
  * 504 Gateway Timeout
* One of the following exceptions is raised:
  * Network errors
    * `httpx.ConnectError`
    * `httpx.ReadError`
    * `httpx.WriteError`
  * Network timeouts
    * `httpx.TimeoutError` (all timeouts)

Based on which error is raised, a different wait strategy is used:

* 429 Too Many Requests: Respect the `Retry-After` header, if present. If not, fall back to `tenacity.wait_exponential()`
* 5xx Server Errors: `tenacity.wait_exponential_jitter()`
* Network errors: `tenacity.wait_exponential()`
* Network timeouts: `tenacity.wait_exponential_jitter()`

```python
import httpx
from tenacity_httpx import retry_http_errors

@retry_http_errors()
httpx.get("https://example.com/")
```
