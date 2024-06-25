# retryhttp

Retry potentially-transient HTTP errors.

**Note**: This project is in beta status. The API may change significantly.

## Overview

Under the hood, `retryhttp` extends [`tenacity`](https://github.com/jd/tenacity) with custom retry and wait strategies, as well as a decorator that wraps `tenacity.retry()` with sensible defaults.

Supports both [`requests`](https://github.com/psf/requests) and [`httpx`](https://github.com/encode/httpx).

## Install

Install most recent stable release from PyPI. This installs support for both `httpx` and `requests`:

```bash
pip install retryhttp
```

You can also install support for only one or the other:

```bash
pip install retryhttp[httpx]
# OR:
pip install retryhttp[requests]
```

Install latest development snapshot from git:

```bash
pip install git+https://github.com/austind/retryhttp.git@main
```

## Quickstart



```python
import httpx
from retryhttp import retry_http_errors

# See Default Behavior section below for what happens here
@retry_http_errors()
def get_example():
    response = httpx.get("https://example.com/")
    response.raise_for_status()

```

## Default Behavior

By default, `retryhttp.retry_http_errors()` retries the following conditions:

* If the response status code is:
  * 429 Too Many Requests
  * 500 Internal Server Error
  * 502 Bad Gateway
  * 503 Service Unavailable
  * 504 Gateway Timeout
* If one of the following other exceptions is raised:
  * Network errors
    * `httpx.ConnectError`
    * `httpx.ReadError`
    * `httpx.WriteError`
    * `requests.ConnectionError`
  * Network timeouts
    * `httpx.TimeoutError`
    * `requests.Timeout`

Based on which error is raised, a different wait strategy is used:

* 429 Too Many Requests: Respect the `Retry-After` header, if present. If not, fall back to `tenacity.wait_exponential()`
* 5xx Server Errors: `tenacity.wait_exponential_jitter()`
* Network errors: `tenacity.wait_exponential()`
* Network timeouts: `tenacity.wait_exponential_jitter()`

