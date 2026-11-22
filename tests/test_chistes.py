import asyncio
import json

import aiohttp
import pytest

from chistes import (
    JokeAPIError,
    JokeCacheError,
    find_joke,
    load_jokes,
    parse_jokes,
    speech_text,
)

TWO = {"error": False, "amount": 2, "jokes": [
    {"type": "single", "joke": "A", "id": 3},
    {"type": "twopart", "setup": "Q", "delivery": "R", "id": 1}]}

JOKES = [{"id": 1, "setup": "Q", "delivery": "R"}, {"id": 7, "setup": "x"}]


def make_fetch(payload):
    calls = []

    async def fetch():
        calls.append(1)
        return payload

    return fetch, calls


async def fetch_must_not_be_called():
    raise AssertionError("the API must not be called when the cache exists")


def write_cache(path, text):
    path.write_text(text, encoding="utf-8")


# --- parse_jokes ---

def test_parse_jokes_single_and_twopart():
    assert parse_jokes(TWO) == [{"id": 3, "setup": "A", "delivery": ""},
                                {"id": 1, "setup": "Q", "delivery": "R"}]


def test_parse_jokes_amount_one_shape():
    payload = {"error": False, "type": "single", "joke": "A", "id": 5}
    assert parse_jokes(payload) == [{"id": 5, "setup": "A", "delivery": ""}]


def test_parse_jokes_error_raises():
    with pytest.raises(JokeAPIError):
        parse_jokes({"error": True, "message": "No matching joke found"})


# --- load_jokes ---

def test_load_jokes_downloads_and_writes_cache_when_missing(tmp_path):
    cache = tmp_path / "chistes.json"
    fetch, calls = make_fetch(TWO)

    jokes = asyncio.run(load_jokes(str(cache), fetch))

    expected = [{"id": 3, "setup": "A", "delivery": ""},
                {"id": 1, "setup": "Q", "delivery": "R"}]
    assert jokes == expected
    assert json.loads(cache.read_text(encoding="utf-8")) == expected
    assert len(calls) == 1


def test_load_jokes_uses_existing_cache_without_calling_api(tmp_path):
    cache = tmp_path / "chistes.json"
    write_cache(cache, '[{"id": 7, "setup": "mío"}]')

    jokes = asyncio.run(load_jokes(str(cache), fetch_must_not_be_called))

    assert jokes == [{"id": 7, "setup": "mío"}]


def test_load_jokes_invalid_json_raises_and_keeps_file(tmp_path):
    cache = tmp_path / "chistes.json"
    broken = '[{"id": 7, "setup": "x",]'
    write_cache(cache, broken)

    with pytest.raises(JokeCacheError):
        asyncio.run(load_jokes(str(cache), fetch_must_not_be_called))

    assert cache.read_text(encoding="utf-8") == broken


def test_load_jokes_empty_list_raises(tmp_path):
    cache = tmp_path / "chistes.json"
    write_cache(cache, "[]")

    with pytest.raises(JokeCacheError):
        asyncio.run(load_jokes(str(cache), fetch_must_not_be_called))


def test_load_jokes_api_failure_writes_nothing(tmp_path):
    cache = tmp_path / "chistes.json"

    async def failing_fetch():
        raise aiohttp.ClientConnectionError()

    with pytest.raises(JokeAPIError):
        asyncio.run(load_jokes(str(cache), failing_fetch))

    assert not cache.exists()


def test_load_jokes_missing_id_raises(tmp_path):
    cache = tmp_path / "chistes.json"
    write_cache(cache, '[{"setup": "x"}]')

    with pytest.raises(JokeCacheError):
        asyncio.run(load_jokes(str(cache), fetch_must_not_be_called))


def test_load_jokes_duplicate_id_raises(tmp_path):
    cache = tmp_path / "chistes.json"
    write_cache(cache, '[{"id": 1, "setup": "a"}, {"id": 1, "setup": "b"}]')

    with pytest.raises(JokeCacheError, match="1"):
        asyncio.run(load_jokes(str(cache), fetch_must_not_be_called))


def test_load_jokes_non_utf8_file_raises_cache_error(tmp_path):
    cache = tmp_path / "chistes.json"
    raw = '[{"id": 7, "setup": "café"}]'.encode("cp1252")
    cache.write_bytes(raw)

    with pytest.raises(JokeCacheError):
        asyncio.run(load_jokes(str(cache), fetch_must_not_be_called))

    assert cache.read_bytes() == raw


def test_cache_error_message_does_not_include_joke_text(tmp_path):
    cache = tmp_path / "chistes.json"
    write_cache(cache, '[{"id": 1, "setup": "a"}, {"setup": "remate oculto"}]')

    with pytest.raises(JokeCacheError) as info:
        asyncio.run(load_jokes(str(cache), fetch_must_not_be_called))

    assert "remate oculto" not in str(info.value)
    assert "#2" in str(info.value)


@pytest.mark.parametrize("error", [
    TimeoutError(),
    json.JSONDecodeError("Expecting value", "", 0),
])
def test_load_jokes_api_errors_raise_api_error(tmp_path, error):
    cache = tmp_path / "chistes.json"

    async def failing_fetch():
        raise error

    with pytest.raises(JokeAPIError):
        asyncio.run(load_jokes(str(cache), failing_fetch))

    assert not cache.exists()


def test_load_jokes_unexpected_api_shape_raises_api_error(tmp_path):
    cache = tmp_path / "chistes.json"
    fetch, _ = make_fetch({"error": False, "jokes": [{"id": 1}]})

    with pytest.raises(JokeAPIError):
        asyncio.run(load_jokes(str(cache), fetch))

    assert not cache.exists()


# --- find_joke / speech_text ---

def test_find_joke_by_id():
    assert find_joke(JOKES, 7) == {"id": 7, "setup": "x"}


def test_find_joke_unknown_id_returns_none():
    assert find_joke(JOKES, 99) is None


def test_speech_text_twopart():
    assert speech_text(JOKES[0]) == "Q ... R"


def test_speech_text_without_delivery():
    assert speech_text(JOKES[1]) == "x"
