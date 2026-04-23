"""Slack implementation of the shared ChatClient ABC."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

from chat_client_api.client import (
    Channel,
    ChannelNotFoundError,
    ChatClient,
    Message,
    MessageDeleteError,
    MessageNotFoundError,
)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

# Slack message_id convention: "<channel_id>:<ts>"
_SEP = ":"


def _encode_message_id(channel_id: str, ts: str) -> str:
    return f"{channel_id}{_SEP}{ts}"


def _decode_message_id(message_id: str) -> tuple[str, str]:
    """Split a composite message_id back into (channel_id, ts)."""
    parts = message_id.split(_SEP, 1)
    if len(parts) != 2:  # noqa: PLR2004
        msg = f"Invalid Slack message_id format: {message_id!r}"
        raise ValueError(msg)
    return parts[0], parts[1]


class SlackChatAdapter(ChatClient):  # type: ignore[misc]
    """
    Slack implementation of the shared ``ChatClient`` ABC.

    Reads ``SLACK_BOT_TOKEN`` from the environment on construction unless an
    explicit ``bot_token`` is provided.

    Args:
        bot_token: Slack Bot OAuth token (``xoxb-...``). Falls back to the
            ``SLACK_BOT_TOKEN`` environment variable.

    """

    def __init__(self, bot_token: str | None = None) -> None:
        """
        Initialize the SlackChatAdapter.

        Args:
            bot_token: Slack Bot OAuth token. Falls back to ``SLACK_BOT_TOKEN`` env var.

        """
        resolved = bot_token or os.environ.get("SLACK_BOT_TOKEN")
        if not resolved:
            msg = "SLACK_BOT_TOKEN is not set in the environment."
            raise RuntimeError(msg)
        self._client = WebClient(token=resolved)

    # ------------------------------------------------------------------
    # ChatClient interface
    # ------------------------------------------------------------------

    def send_message(self, channel_id: str, text: str) -> Message:
        """
        Send a message to a Slack channel.

        Args:
            channel_id: Slack channel ID (e.g. ``C0123456789``).
            text: Plain-text message content.

        Returns:
            The sent :class:`~chat_client_api.client.Message`.

        Raises:
            ChannelNotFoundError: If the channel does not exist or the bot
                lacks access.

        """
        try:
            resp = self._client.chat_postMessage(channel=channel_id, text=text)
        except SlackApiError as exc:
            if exc.response.get("error") in {"channel_not_found", "not_in_channel"}:
                raise ChannelNotFoundError(channel_id) from exc
            raise
        ts: str = resp["ts"]
        return Message(
            message_id=_encode_message_id(channel_id, ts),
            channel=channel_id,
            text=text,
            sender="bot",
            timestamp=datetime.fromtimestamp(float(ts), tz=UTC),
        )

    def get_channels(self) -> list[Channel]:
        """
        List all public channels the bot has access to.

        Returns:
            List of :class:`~chat_client_api.client.Channel` objects.

        """
        resp = self._client.conversations_list(types="public_channel,private_channel")
        channels: list[dict[str, Any]] = resp.get("channels", [])
        return [
            Channel(
                channel_id=ch["id"],
                name=ch.get("name", ""),
                is_private=ch.get("is_private"),
                channel_type="private" if ch.get("is_private") else "public",
            )
            for ch in channels
        ]

    def get_channel(self, channel_id: str) -> Channel:
        """
        Get a single channel by ID.

        Args:
            channel_id: Slack channel ID.

        Returns:
            :class:`~chat_client_api.client.Channel`.

        Raises:
            ChannelNotFoundError: If the channel is not found.

        """
        try:
            resp = self._client.conversations_info(channel=channel_id)
        except SlackApiError as exc:
            raise ChannelNotFoundError(channel_id) from exc
        ch = resp["channel"]
        return Channel(
            channel_id=ch["id"],
            name=ch.get("name", ""),
            is_private=ch.get("is_private"),
            channel_type="private" if ch.get("is_private") else "public",
        )

    def get_messages(
        self,
        channel_id: str,
        limit: int = 10,
        cursor: str | None = None,
    ) -> list[Message]:
        """
        Get recent messages from a Slack channel.

        Args:
            channel_id: Slack channel ID.
            limit: Maximum number of messages to return.
            cursor: Optional Slack pagination cursor.

        Returns:
            List of :class:`~chat_client_api.client.Message` objects.

        """
        kwargs: dict[str, object] = {"channel": channel_id, "limit": limit}
        if cursor:
            kwargs["cursor"] = cursor
        try:
            resp = self._client.conversations_history(**kwargs)  # type: ignore[arg-type]
        except SlackApiError as exc:
            raise ChannelNotFoundError(channel_id) from exc

        raw_messages: list[dict[str, Any]] = resp.get("messages", [])
        messages: list[Message] = []
        for msg in raw_messages:
            ts: str = msg.get("ts", "0")
            messages.append(
                Message(
                    message_id=_encode_message_id(channel_id, ts),
                    channel=channel_id,
                    text=msg.get("text", ""),
                    sender=msg.get("user", "unknown"),
                    timestamp=datetime.fromtimestamp(float(ts), tz=UTC),
                )
            )
        return messages

    def get_message(self, message_id: str) -> Message:
        """
        Get a single message by its composite ID (``channel_id:ts``).

        Args:
            message_id: Composite ``"channel_id:ts"`` identifier.

        Returns:
            :class:`~chat_client_api.client.Message`.

        Raises:
            MessageNotFoundError: If the message is not found.

        """
        channel_id, ts = _decode_message_id(message_id)
        try:
            resp = self._client.conversations_history(
                channel=channel_id,
                latest=ts,
                inclusive=True,
                limit=1,
            )
        except SlackApiError as exc:
            raise MessageNotFoundError(message_id) from exc

        raw_messages: list[dict[str, Any]] = resp.get("messages", [])
        if not raw_messages:
            raise MessageNotFoundError(message_id)

        msg = raw_messages[0]
        return Message(
            message_id=message_id,
            channel=channel_id,
            text=msg.get("text", ""),
            sender=msg.get("user", "unknown"),
            timestamp=datetime.fromtimestamp(float(ts), tz=UTC),
        )

    def delete_message(self, message_id: str) -> None:
        """
        Delete a Slack message by its composite ID (``channel_id:ts``).

        Args:
            message_id: Composite ``"channel_id:ts"`` identifier.

        Raises:
            MessageDeleteError: If the message cannot be deleted.

        """
        channel_id, ts = _decode_message_id(message_id)
        try:
            self._client.chat_delete(channel=channel_id, ts=ts)
        except SlackApiError as exc:
            raise MessageDeleteError(message_id) from exc
