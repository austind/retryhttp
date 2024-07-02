# Changelog

## v0.2.0

* Rename `retryhttp.retry_http_errors` to [`retryhttp.retry`][].
* Rename `retryhttp.wait_http_errors` to [`retryhttp.wait_context_aware`][].
* Restructure project so all members are part of the root namespace.
* Move type delcarations to `retryhttp._types`.
* Enable bare decorator syntax for [`retryhttp.retry`][] (i.e., `@retry` works as well as `@retry()`)

## v0.1.0

Initial release.

Added the following methods and classes:

* `retryhttp.retry_http_errors`
* [`retryhttp.retry_if_network_error`][]
* [`retryhttp.retry_if_rate_limited`][]
* [`retryhttp.retry_if_server_error`][]
* [`retryhttp.retry_if_timeout`][]
* [`retryhttp.wait_from_header`][]
* [`retryhttp.wait_rate_limited`][]
* [`retryhttp.wait_context_aware`][]
