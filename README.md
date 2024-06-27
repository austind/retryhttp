# retryhttp

Retry commonly transient HTTP errors in Python.

See [documentation](https://retryhttp.readthedocs.io/en/latest/).

**Note**: This project is in beta status. The API may change significantly. Please [open a discussion](https://github.com/austind/retryhttp/discussions/new/choose) if you see something that you think should change!

## Overview

Several errors with HTTP requests are often transient, and may benefit from retrying:

* HTTP status codes
    * `429 Too Many Requests` (rate limited)
    * `500 Internal Server Error`
    * `502 Bad Gateway`
    * `503 Service Unavailable`
    * `504 Gateway Timeout`
* Network errors
* Timeouts

This project aims to simplify retrying these, by extending [`tenacity`](https://github.com/jd/tenacity) with custom retry and wait strategies, as well as a custom decorator. Defaults are sensible for most use cases, but are fully customizable.

Supports exceptions raised by both [`requests`](https://github.com/psf/requests) and [`httpx`](https://github.com/encode/httpx).

## Install

Install most recent stable release from PyPI:

```sh
pip install retryhttp # Supports both HTTPX and requests
```

You can also install support for only HTTPX or requests:

```sh
pip install retryhttp[httpx] # Supports only HTTPX
pip install retryhttp[requests] # Supports only requests
```

Or, install the latest development snapshot from git:

```sh
pip install git+https://github.com/austind/retryhttp.git@main
```

## Quickstart

```python
import httpx
from retryhttp import retry_http_errors

# Retries all HTTP status codes, network errors, and timeouts listed above
# for a maximum of 3 attempts
@retry_http_errors()
def get_example():
    response = httpx.get("https://example.com/")
    response.raise_for_status()

```

## Contributing

Contributions welcome! Open a discussion and let's chat about your idea. Looking forward to working with you!
