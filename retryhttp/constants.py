# Potentially transient HTTP 5xx error statuses to retry.
RETRY_SERVER_ERROR_CODES = (
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
)
