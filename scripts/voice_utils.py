import asyncio
import time


async def wait_until_voice_ready(vc, timeout=5.0, interval=0.1):
    """Wait until Discord's voice encryption (DAVE) can encrypt audio.

    Right after joining, the encryption key isn't ready yet and any audio sent
    in that window is dropped, which cuts off the start of the joke.
    Returns True when ready, False if it timed out (the caller plays anyway).
    """
    conn = getattr(vc, "_connection", None)  # discord.py exposes no public API for this
    if conn is None or getattr(conn, "dave_protocol_version", 0) == 0:
        return True

    deadline = time.monotonic() + timeout
    while not conn.can_encrypt:
        if time.monotonic() >= deadline:
            return False
        await asyncio.sleep(interval)
    return True
