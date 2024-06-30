# API Reference

!!! note
    All the methods and classes below are imported into the root namespace, so you can refer to them as `retryhttp.retry`, `retryhttp.wait_rate_limited`, etc.

## Retry Decorator

::: retryhttp.retry.retry

## Retry Strategies

If you'd rather use `tenacity.retry` directly (without using [`retryhttp.retry`][]), you can use these retry strategies.

::: retryhttp.retry.retry_if_network_error

::: retryhttp.retry.retry_if_rate_limited

::: retryhttp.retry.retry_if_server_error

::: retryhttp.retry.retry_if_timeout

## Wait Strategies

Wait strategies to use with `tenacity.retry` or [`retryhttp.retry`][].

::: retryhttp.wait.wait_from_header

::: retryhttp.wait.wait_http_errors

::: retryhttp.wait_rate_limited
