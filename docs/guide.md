## Overview

`retryhttp` extends the core functionality of `tenacity` with custom retry and wait strategies aimed at making it easier to retry commonly transient HTTP errors.

## Examples

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

## Advanced Usage

You don't have to use the [`retryhttp.retry_http_errors`][] decorator, which is provided purely for convenience. If you prefer, you can use [`tenacity.retry`][] and roll your own approach.

!!! note
    If you want to apply different wait strategies to specific errors, you'll need to use [`retryhttp.wait_http_errors`][] as a wait strategy, or write your own context-aware wait strategy.

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