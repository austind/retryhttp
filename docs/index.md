# RetryHTTP

Retry potentially transient HTTP errors in Python.

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

Supports exceptions raised by both [`requests`](https://docs.python-requests.org/en/latest/index.html) and [`httpx`](https://python-httpx.org/).

## Install

Install from PyPI:

```sh
# Supports both HTTPX and requests
pip install retryhttp
```

You can also install support for only HTTPX or requests:

```sh
pip install retryhttp[httpx] # Supports only HTTPX
pip install retryhttp[requests] # Supports only requests
```

Or, install the latest development snapshot from git:

```sh
pip install git+https://github.com/austind/retryhttp.git@develop
```

## Quickstart

```python
import httpx
from retryhttp import retry

# Retries retryable status codes (429, 500, 502, 503, 504), network errors,
# and timeouts, up to 3 times, with appropriate wait strategies for each
# type of error. All of these behaviors are customizable.
@retry
def example():
    response = httpx.get("https://example.com/")
    response.raise_for_status()
    return response.text

```
