# Slack Chat Adapter

## Overview

`slack_chat_adapter` provides `SlackChatAdapter`, a concrete implementation of the `ChatClient` abstract base class from the shared `chat-client-api` interface. It delegates all messaging operations to the Slack Web API via the `slack-sdk` library.

This component is part of the HW3 cross-vertical integration: the calendar service uses it to send AI-generated responses back to users in Slack without any route code depending on Slack directly.

## Architecture

`SlackChatAdapter` implements the `ChatClient` ABC from the Chat vertical's shared interface (`github.com/HarshithKoriRaj/Shared-API`). The calendar service selects the backend at startup via the `CHAT_BACKEND` environment variable through the `get_chat_client()` factory in `dependencies.py`, so swapping to a different chat platform (e.g. Discord) requires only adding a new adapter and updating that factory — no route code changes.

## Installation

This package is part of the `uv` workspace and is installed automatically:

```bash
uv sync --all-packages
```

## Usage

```python
from slack_chat_adapter.adapter import SlackChatAdapter

adapter = SlackChatAdapter()  # reads SLACK_BOT_TOKEN from environment

adapter.send_message(channel_id="C01234567", text="Hello from the calendar service!")
channels = adapter.get_channels()
messages = adapter.get_messages(channel_id="C01234567")
```

## Provided Methods

| Method | Description |
|---|---|
| `send_message(channel_id, text)` | Post a message to a Slack channel |
| `get_channels()` | List channels the bot belongs to |
| `get_messages(channel_id)` | Retrieve recent messages from a channel |
| `get_message(channel_id, message_id)` | Fetch a single message by timestamp |
| `delete_message(channel_id, message_id)` | Delete a message |

## Environment Variables

| Variable | Description |
|---|---|
| `SLACK_BOT_TOKEN` | Slack Bot OAuth token (`xoxb-…`). Required at runtime. |

## Testing

```bash
uv run pytest components/slack_chat_adapter/tests/ -q
```
