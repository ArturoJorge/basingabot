# Basinga Bot

A Discord bot made by **Arturo Jorge**. Current version: **2.0.0**.

## Commands

All commands use the `&` prefix.

| Command | Description |
| --- | --- |
| `&bazinga` | Replies with **BAZINGA!** |
| `&join` | Joins the voice channel you are in. |
| `&leave` | Leaves the voice channel. |
| `&vtk @user` | Starts a vote to kick `@user` from the voice channel. Only people in your voice channel can vote, once each. The vote ends after 30 seconds without votes. |
| `&fishreact` | Reply to a message with this command to send the fish gif and add fish reactions to that message. |
| `&chiste` | Joins your voice channel and tells a random joke out loud (voice: Gonzalo, Colombia). |
| `&chiste <id>` | Tells the joke with that id. |
| `&say <message>` | Joins your voice channel and reads your message out loud with the same voice. |

## Jokes

The first time someone uses `&chiste`, the bot downloads the Spanish jokes from [JokeAPI](https://jokeapi.dev) and saves them to `res/chistes.json` (ids 1–6). After that it never downloads them again, so you can edit that file freely.

To add your own jokes, append them to the list in `res/chistes.json`:

```json
{ "id": 33, "setup": "¿Por qué el libro de matemáticas estaba triste?", "delivery": "Porque tenía muchos problemas." }
```

- `id` must be a number and can't repeat. Use the next free number.
- `delivery` is optional. Leave it out for one-part jokes.
- The bot reads the file every time, so new jokes work without restarting it.

To download the JokeAPI jokes again, delete `res/chistes.json`.

## Setup

### 1. Install the dependencies

The bot needs Python 3.12 or newer. With conda:

```bash
conda create -n basinga_env python=3.12
conda activate basinga_env
pip install -r requirements.txt
```

ffmpeg, which `&chiste` needs to play audio, comes with the `imageio-ffmpeg` package. You don't need to install it separately.

### 2. Add your bot token

Create `scripts/constants.py` with your token in quotes:

```python
BOTTOKEN = 'your-bot-token-here'
```

This file is in `.gitignore`. Never commit it.

### 3. Turn on the intents

In the [Discord Developer Portal](https://discord.com/developers/applications), open your application, go to **Bot** and turn on:

- **Message Content Intent**
- **Server Members Intent**

If you skip this, the bot fails to start with a `PrivilegedIntentsRequired` error.

### 4. Run the bot

From the root of the repository:

```bash
python scripts/main.py
```

When it prints `The bot is ready!`, the bot is online.

## Tests

From the root of the repository:

```bash
python -m pytest
```

## Special thanks

- @oliviareggiardo.
