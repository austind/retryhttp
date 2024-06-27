# API Reference

## Retry Decorator

Wraps [`tenacity.retry`][] with sensible defaults for most use cases.

::: retryhttp.retry_http_errors

## Retry Strategies

If you'd rather use [`tenacity.retry`][] directly (without using [`retryhttp.retry_http_errors`][]), you can use these retry strategies.

::: retryhttp.retry_if_network_error

::: retryhttp.retry_if_rate_limited

::: retryhttp.retry_if_server_error

::: retryhttp.retry_if_timeout

## Wait Strategies

Wait strategies to use with [`tenacity.retry`][] or [`retryhttp.retry_http_errors`][].

::: retryhttp.wait_from_header

::: retryhttp.wait_http_errors

::: retryhttp.wait_rate_limited
