# retryhttp

Retry commonly transient HTTP errors.

**Note**: This project is in beta status. The API may change significantly. Please open a discussion if you see something that you think should change!

## Overview

Network errors, timeouts, and certain HTTP status codes might be transient, and may benefit from retrying.

Under the hood, `retryhttp` extends [`tenacity`](https://github.com/jd/tenacity) with custom retry and wait strategies, as well as a decorator that wraps `tenacity.retry()` with sensible defaults, to make retrying these errors easy--without sacrificing any flexibility. You can override all defaults to suit your use case.

Supports exceptions raised by both [`requests`](https://github.com/psf/requests) and [`httpx`](https://github.com/encode/httpx).

## Install

Install most recent stable release from PyPI. This installs support for both `httpx` and `requests`:

```sh
pip install retryhttp
```

You can also install support for only one or the other:

```sh
pip install retryhttp[httpx] # Support only HTTPX
pip install retryhttp[requests] # Support only requests
```

Install latest development snapshot from git:

```sh
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

By default, `retryhttp.retry_http_errors()` retries the following conditions. All of this behavior is customizable (see More Examples below).

Retry if:

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
    * `requests.ConnectionError`
  * Network timeouts
    * `httpx.TimeoutError`
    * `requests.Timeout`

Based on which error is raised, a different wait strategy is used:

* 429 Too Many Requests: Respect the `Retry-After` header, if present. If not, fall back to `tenacity.wait_exponential()`
* 5xx server errors: `tenacity.wait_exponential_jitter()`
* Network errors: `tenacity.wait_exponential()`
* Network timeouts: `tenacity.wait_exponential_jitter()`

# More Examples

```python
import httpx
from tenacity import wait_exponential, wait_rate_limited
from retryhttp import retry_http_errors

# Retry only 503 Service Unavailable and network errors up to 5 times
# with default wait strategies.
@retry_http_errors(
    max_attempt_number=5,
    retry_timeouts=False,
    retry_rate_limited=False,
    retry_server_error_codes=503,
)
def get_example():
    response = httpx.get("https://example.com/")
    response.raise_for_status()

# Retry only httpx.ConnectError and apply a custom wait strategy.
@retry_http_errors(
    retry_timeouts=False,
    retry_rate_limited=False,
    retry_server_errors=False,
    network_errors=httpx.ConnectError,
    wait_network_errors=wait_exponential(multiplier=0.5, min=0.5, max=20),
)
def get_example():
    response = httpx.get("https://example.com/")
    response.raise_for_status()

# Retry server errors, network errors, and timeouts but with different
# fallback wait strategy for rate limited (429 Too Many Requests). I.e.,
# we'll honor the Retry-After header if it exists, otherwise we'll use
# a custom wait_exponential
@retry_http_errors(
    max_attempt_number=5
    wait_rate_limited=wait_rate_limited(
        fallback=wait_exponential(multiplier=0.5, min=0.5, max=20)
    ),
)
def get_example():
    response = httpx.get("https://example.com/")
    response.raise_for_status()
```

# Advanced Usage

You don't have to use the `retryhttp.retry_http_errors()` decorator, which is provided purely for convenience. If you prefer, you can use `tenacity.retry()` and roll your own approach.

**Note**: If you want to apply different wait strategies to specific errors, you'll need to use `retryhttp.wait_http_errors()` as a wait strategy, or write your own context-aware wait strategy.

```python
from tenacity import retry, wait_exponential, stop_after_delay
from retryhttp import retry_if_rate_limited, wait_rate_limited

# Retry only 429 Too Many Requests after a maximum of 20 seconds.
@retry(
    retry=retry_if_rate_limited(),
    wait=wait_rate_limited(),
    stop=stop_after_delay(20))
def get_example():
    response = httpx.get("https://example.com/")
    response.raise_for_status()
```

## Contributing

Contributions welcome! Open a discussion and let's chat about your idea. Looking forward to working with you!
