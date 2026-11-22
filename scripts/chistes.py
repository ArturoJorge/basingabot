# Jokes for the &chiste command: JokeAPI download, JSON cache and TTS.

import json
import os

import aiohttp
import edge_tts

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'res', 'chistes.json')
JOKEAPI_URL = "https://v2.jokeapi.dev/joke/Any?lang=es&safe-mode&amount=10"
VOICE = "es-CO-GonzaloNeural"


class JokeAPIError(Exception):
    """JokeAPI failed or returned no jokes."""


class JokeCacheError(Exception):
    """The cache file exists but is invalid."""


def parse_jokes(payload):
    if payload.get("error"):
        raise JokeAPIError(payload.get("message", "JokeAPI returned an error"))

    raw = payload["jokes"] if "jokes" in payload else [payload]
    jokes = []
    for j in raw:
        if j["type"] == "single":
            jokes.append({"id": j["id"], "setup": j["joke"], "delivery": ""})
        else:
            jokes.append({"id": j["id"], "setup": j["setup"], "delivery": j["delivery"]})
    return jokes


async def fetch_jokes_from_api():
    async with aiohttp.ClientSession() as session:
        async with session.get(JOKEAPI_URL) as response:
            response.raise_for_status()
            return await response.json()


def _read_cache(cache_path):
    # ValueError covers both bad JSON and a file not saved as UTF-8.
    try:
        with open(cache_path, encoding="utf-8") as f:
            jokes = json.load(f)
    except (ValueError, OSError) as e:
        raise JokeCacheError(f"it can't be read, save it as UTF-8 JSON ({e})")

    if not isinstance(jokes, list) or not jokes:
        raise JokeCacheError("it must be a list with at least one joke")

    # Errors name the joke by position, never by its text: jokes are only spoken.
    seen = set()
    for n, joke in enumerate(jokes, start=1):
        if not isinstance(joke, dict) or not joke.get("setup"):
            raise JokeCacheError(f"joke #{n} needs a non-empty \"setup\"")
        joke_id = joke.get("id")
        if not isinstance(joke_id, int):
            raise JokeCacheError(f"joke #{n} needs a numeric \"id\"")
        if joke_id in seen:
            raise JokeCacheError(f"the id {joke_id} is repeated")
        seen.add(joke_id)
    return jokes


async def load_jokes(cache_path=CACHE_PATH, fetch=fetch_jokes_from_api):
    # Download only when the file doesn't exist, so hand-added jokes are never overwritten.
    if os.path.exists(cache_path):
        return _read_cache(cache_path)

    try:
        jokes = parse_jokes(await fetch())
    except (aiohttp.ClientError, TimeoutError, ValueError, KeyError, TypeError) as e:
        raise JokeAPIError(f"couldn't get jokes from JokeAPI ({e!r})")

    if not jokes:
        raise JokeAPIError("JokeAPI returned no jokes")

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(jokes, f, ensure_ascii=False, indent=2)
    return jokes


def find_joke(jokes, joke_id):
    return next((j for j in jokes if j["id"] == joke_id), None)


def speech_text(joke):
    delivery = joke.get("delivery")
    return f"{joke['setup']} ... {delivery}" if delivery else joke["setup"]


async def synthesize(text, voice=VOICE):
    """Return the spoken text as MP3 bytes."""
    audio = bytearray()
    async for chunk in edge_tts.Communicate(text, voice).stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
    return bytes(audio)
