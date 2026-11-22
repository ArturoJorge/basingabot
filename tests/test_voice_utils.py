import asyncio
import time

from voice_utils import wait_until_voice_ready


class FakeConnection:
    def __init__(self, dave_protocol_version=1, ready_after=None):
        self.dave_protocol_version = dave_protocol_version
        self._ready_at = None if ready_after is None else time.monotonic() + ready_after

    @property
    def can_encrypt(self):
        return self._ready_at is not None and time.monotonic() >= self._ready_at


class FakeVoiceClient:
    def __init__(self, connection):
        self._connection = connection


def test_returns_true_once_encryption_is_ready():
    vc = FakeVoiceClient(FakeConnection(ready_after=0.3))
    start = time.monotonic()

    assert asyncio.run(wait_until_voice_ready(vc, timeout=5)) is True
    assert 0.3 <= time.monotonic() - start < 1


def test_returns_false_after_timeout_when_never_ready():
    vc = FakeVoiceClient(FakeConnection(ready_after=None))
    start = time.monotonic()

    assert asyncio.run(wait_until_voice_ready(vc, timeout=0.3)) is False
    assert 0.3 <= time.monotonic() - start < 1


def test_returns_immediately_without_e2ee():
    vc = FakeVoiceClient(FakeConnection(dave_protocol_version=0))
    start = time.monotonic()

    assert asyncio.run(wait_until_voice_ready(vc, timeout=5)) is True
    assert time.monotonic() - start < 0.1
