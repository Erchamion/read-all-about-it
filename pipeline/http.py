"""Shared HTTP GET-with-retry helper used by all default fetchers."""

import time

import requests


def get_with_retry(url, *, params=None, headers=None, timeout=30, attempts=3):
    """GET url, retrying transient failures with exponential backoff.

    Raises the last error if every attempt fails. Does not sleep after the
    final failed attempt.
    """
    last_error = None
    for attempt in range(attempts):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            if attempt < attempts - 1:
                time.sleep(2**attempt)
    raise last_error
