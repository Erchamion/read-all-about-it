import requests

from pipeline import http as http_mod
from pipeline.http import get_with_retry


class FakeResponse:
    def __init__(self, status=200, text="ok"):
        self.status_code = status
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def test_get_with_retry_succeeds_after_transient_failure(monkeypatch):
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append(url)
        if len(calls) == 1:
            raise requests.ConnectionError("boom")
        return FakeResponse(200, "recovered")

    monkeypatch.setattr(http_mod.requests, "get", fake_get)
    monkeypatch.setattr(http_mod.time, "sleep", lambda seconds: None)

    response = get_with_retry("https://example.com")
    assert response.text == "recovered"
    assert len(calls) == 2


def test_get_with_retry_raises_after_final_attempt(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        raise requests.ConnectionError("still down")

    monkeypatch.setattr(http_mod.requests, "get", fake_get)
    monkeypatch.setattr(http_mod.time, "sleep", lambda seconds: None)

    try:
        get_with_retry("https://example.com", attempts=3)
        assert False, "expected get_with_retry to raise"
    except requests.ConnectionError as error:
        assert str(error) == "still down"


def test_get_with_retry_does_not_sleep_after_final_failed_attempt(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        raise requests.ConnectionError("still down")

    sleep_calls = []
    monkeypatch.setattr(http_mod.requests, "get", fake_get)
    monkeypatch.setattr(http_mod.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    try:
        get_with_retry("https://example.com", attempts=3)
    except requests.ConnectionError:
        pass

    # 3 attempts total, sleeps only occur between attempts (2 sleeps, not 3)
    assert len(sleep_calls) == 2
