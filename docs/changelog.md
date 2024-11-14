# Changelog

## v1.2.0

* Added `wait_max` argument to [`retryhttp.wait_from_header`][] and [`retryhttp.wait_retry_after`][], which defaults to 120.0 seconds.
* [`retryhttp._utils.is_rate_limited][]: revert behavior to correctly determine rate limiting by a `429 Too Many Requests` status.
* When receiving `503 Service Unavailable`, honor a `Retry-After` header if provided.
* Rename `retryhttp.wait_rate_limited` to [`retryhttp.wait_retry_after`][], but retain alias for backwards compatibility and convenience.
* [`retryhttp.wait_from_header`][]: Handle case if server responds with a date in the past.
* [`retryhttp.wait_context_aware`][]: The `wait_server_errors` argument now defaults to [`retryhttp.wait_retry_after`][] with [`tenacity.wait_random_exponential][] as fallback, since some server errors may respond with a `Retry-After` header.
* [`retryhttp.wait_context_aware`][]: The `wait_rate_limited` argument now has [`tenacity.wait_random_exponential`][] as fallback to [`retryhttp.wait_retry_after`][], to make retrying rate-limited requests more robust.


## v1.1.0

* Add [HTTP-date](https://httpwg.org/specs/rfc9110.html#http.date) value parsing for [`retryhttp.wait_from_header`][]
* [`retryhttp._utils.is_rate_limited`][] now determines that a request was rate limited by the presence of a `Retry-After` header. In prior versions, this was based on the status code `429 Too Many Requests`. However, many servers return other status codes when rate limiting.

## v1.0.1

* Fix documentation errors.

## v1.0.0

* API is now stable. Any breaking changes will follow [SemVer](https://semver.org/) guidelines.
* Added `requests.exceptions.ChunkedEncodingError` to the list of default network errors.

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
