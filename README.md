# RetryHTTP

Retry potentially transient HTTP errors in Python.

See [documentation](https://retryhttp.readthedocs.io/en/latest/).

## Overview

Several HTTP errors are often transient, and might succeed if retried:

* HTTP status codes
    * `429 Too Many Requests` (rate limited)
    * `500 Internal Server Error`
    * `502 Bad Gateway`
    * `503 Service Unavailable`
    * `504 Gateway Timeout`
* Network errors
* Timeouts

This project aims to simplify retrying these, by extending [`tenacity`](https://tenacity.readthedocs.io/) with custom retry and wait strategies, as well as a custom decorator. Defaults are sensible for most use cases, but are fully customizable.

Supports both [`requests`](https://docs.python-requests.org/en/latest/index.html), [`httpx`](https://python-httpx.org/) and [`aiohttp`](https://docs.aiohttp.org/) natively, but could be customized to use with any library that raises exceptions for the conditions listed above.

## Install

Install from PyPI:

```sh
pip install retryhttp  # Supports HTTPX, requests and aiohttp
```

You can also install support for only HTTPX or requests, if you would rather not install unnecessary dependencies:

```sh
pip install retryhttp[httpx]  # Supports only HTTPX
pip install retryhttp[requests]  # Supports only requests
pip install retryhttp[aiohttp]  # Supports only aiohttp
```

Or, install the latest development snapshot from git:

```sh
pip install git+https://github.com/austind/retryhttp.git@develop
```

## Quickstart

```python
import httpx
from retryhttp import retry

# Retries safely retryable status codes (429, 500, 502, 503, 504), network errors,
# and timeouts, up to a total of 3 times, with appropriate wait strategies for each
# type of error. All of these behaviors are customizable.
@retry
def example():
    response = httpx.get("https://example.com/")
    response.raise_for_status()
    return response.text

```

## Contributing

Contributions welcome! Bug fixes and minor tweaks can jump straight to a [pull request](https://github.com/austind/retryhttp/compare). For more involved changes, [open an issue](https://github.com/austind/retryhttp/issues/new/choose) and let's chat about your idea. Thanks for your contribution!
