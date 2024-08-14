# API Reference

## Decorator

This decorator wraps [`tenacity.retry`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.retry) with sensible defaults for retrying potentially transient HTTP errors. It's the most convenient way to leverage `retryhttp`.

::: retryhttp.retry

## Retry Strategies

If you'd rather use [`tenacity.retry`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.retry) directly (without using [`retryhttp.retry`][]), you can use these retry strategies.

::: retryhttp.retry_if_network_error

::: retryhttp.retry_if_rate_limited

::: retryhttp.retry_if_server_error

::: retryhttp.retry_if_timeout

## Wait Strategies

Wait strategies to use with [`tenacity.retry`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.retry) or [`retryhttp.retry`][].

::: retryhttp.wait_from_header

::: retryhttp.wait_context_aware

::: retryhttp.wait_retry_after
