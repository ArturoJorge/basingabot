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

## Setup

### 1. Install the dependencies

The bot needs Python 3.12 or newer. With conda:

```bash
conda create -n basinga_env python=3.12
conda activate basinga_env
pip install -r requirements.txt
```

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

## Special thanks

- @oliviareggiardo.
