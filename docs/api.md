# API Reference

!!! note
    All the functions and classes below are imported into the root namespace, so you can refer to them as `retryhttp.retry`, `retryhttp.wait_rate_limited`, etc.

## Decorator

This decorator wraps [`tenacity.retry`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.retry) with sensible defaults for retrying potentially transient HTTP errors. It's the most convenient way to leverage `retryhttp`.

::: retryhttp.retry.retry

## Retry Strategies

If you'd rather use [`tenacity.retry`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.retry) directly (without using [`retryhttp.retry.retry`][]), you can use these retry strategies.

::: retryhttp.retry.retry_if_network_error

::: retryhttp.retry.retry_if_rate_limited

::: retryhttp.retry.retry_if_server_error

::: retryhttp.retry.retry_if_timeout

## Wait Strategies

Wait strategies to use with [`tenacity.retry`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.retry) or [`retryhttp.retry.retry`][].

::: retryhttp.wait.wait_from_header

::: retryhttp.wait.wait_context_aware

::: retryhttp.wait_rate_limited
