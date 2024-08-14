## Overview

`retryhttp` makes it easy to retry potentially transient HTTP errors when using `httpx` or `requests`.

!!! note
    Errors that you can safely retry vary from service to service.
    
    `retryhttp` ships with sensible defaults, but read the documentation and/or contact the system administrators of the services you're querying to ensure you're only retrying the right error codes, and using the right wait strategies.

## Examples

```python
import httpx
from tenacity import wait_exponential, wait_retry_after
from retryhttp import retry

# Retry only 503 Service Unavailable and network errors up to 5 times
# with default wait strategies.
@retry(
    max_attempt_number=5,
    retry_timeouts=False,
    retry_rate_limited=False,
    retry_server_error_codes=503,
)
def get_example():
    response = httpx.get("https://example.com/")
    response.raise_for_status()

# Retry only httpx.ConnectError and apply a custom wait strategy.
@retry(
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
@retry(
    max_attempt_number=5
    wait_rate_limited=wait_retry_after(
        fallback=wait_exponential(multiplier=0.5, min=0.5, max=20)
    ),
)
def get_example():
    response = httpx.get("https://example.com/")
    response.raise_for_status()
```

## Advanced Usage

You don't have to use the [`retryhttp.retry`][] decorator, which is provided purely for convenience. If you prefer, you can use [`tenacity.retry`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.retry) and roll your own approach.

!!! note
    If you want to apply different wait strategies to specific errors, you'll need to use [`retryhttp.wait_context_aware`][] as a wait strategy, or write your own context-aware wait strategy.

```python
from tenacity import retry, wait_exponential, stop_after_delay
from retryhttp import retry_if_rate_limited, wait_retry_after

# Retry only 429 Too Many Requests after a maximum of 20 seconds.
@retry(
    retry=retry_if_rate_limited(),
    wait=wait_retry_after(),
    stop=stop_after_delay(20))
def get_example():
    response = httpx.get("https://example.com/")
    response.raise_for_status()
```

# Technical Details

Under the hood, RetryHTTP is a convenience layer on top of the excellent retry library [`tenacity`](https://tenacity.readthedocs.io/).

`tenacity` works by adding a decorator to functions that might fail. This decorator is configured with retry, wait, and stop strategies that configure what conditions to retry, how long to wait between retries, and when to stop retrying, respectively. Failures could be a raised exception, or a configurable return value. See [`tenacity` documentation](https://tenacity.readthedocs.io/en/latest/index.html) for details.

`retryhttp` provides new retry and stop strategies for potentially transient error conditions raised by `httpx` and `requests`. To make things as convenient as possible, `retryhttp` also provides a [new decorator][retryhttp.retry] that wraps [`tenacity.retry`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.retry) with sensible defaults, which are all customizable.