"""Tests for the frontend's delayed loading notice."""
from contextlib import nullcontext
from unittest.mock import patch

from config import config
from dashboard import api_client


class _FakePlaceholder:
    def __init__(self):
        self.captions = []
        self.cleared = False

    def caption(self, value):
        self.captions.append(value)

    def container(self, **_kwargs):
        return nullcontext()

    def empty(self):
        self.cleared = True


class _FakeStreamlit:
    def __init__(self, page_started_at):
        self.session_state = {config.PAGE_LOAD_STARTED_AT_KEY: page_started_at}
        self.placeholders = []
        self.headings = []
        self.messages = []

    def empty(self):
        placeholder = _FakePlaceholder()
        self.placeholders.append(placeholder)
        return placeholder

    def subheader(self, value):
        self.headings.append(value)

    def write(self, value):
        self.messages.append(value)

    def caption(self, value):
        self.messages.append(value)

    def error(self, value):
        raise AssertionError(f"Unexpected frontend error: {value}")

    def stop(self):
        raise AssertionError("The frontend should not stop for this successful response.")


class _FakeReply:
    status_code = 200

    def json(self):
        return []


class _FakeWorker:
    """Runs the request immediately but stays alive for the configured polling cycles."""
    alive_cycles = 0

    def __init__(self, target, daemon):
        self.target = target
        self.remaining_cycles = self.alive_cycles

    def start(self):
        self.target()

    def is_alive(self):
        if self.remaining_cycles:
            self.remaining_cycles -= 1
            return True
        return False

    def join(self):
        return None


def _call_with_elapsed_page_time(elapsed_seconds):
    fake_streamlit = _FakeStreamlit(page_started_at=0)
    _FakeWorker.alive_cycles = 1
    with (patch.object(api_client, "st", fake_streamlit),
          patch.object(api_client.threading, "Thread", _FakeWorker),
          patch.object(api_client.requests, "request", return_value=_FakeReply()),
          patch.object(api_client.time, "monotonic", side_effect=[0, elapsed_seconds]),
          patch.object(api_client.time, "sleep")):
        response = api_client.call_service("GET", "/queue", None, None, None)
    return fake_streamlit, response


def test_slow_page_shows_loading_notice_after_ten_seconds():
    streamlit, response = _call_with_elapsed_page_time(config.SLOW_PAGE_NOTICE_SECONDS)

    assert response == []
    assert streamlit.headings == ["Still loading your page"]
    assert streamlit.placeholders[1].cleared is True


def test_fast_page_does_not_show_loading_notice():
    streamlit, response = _call_with_elapsed_page_time(config.SLOW_PAGE_NOTICE_SECONDS - 1)

    assert response == []
    assert streamlit.headings == []
