"""Abstract AI client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ai_client_api.models import ToolDefinition, ToolResult

# Callable type for dispatching tool calls: (tool_name, args) -> ToolResult
ToolDispatcher = Callable[[str, dict[str, Any]], "ToolResult"]


class AbstractAIClient(ABC):
    """
    Provider-agnostic interface for AI chat-completion clients.

    Implementations must handle sending a prompt to an AI model and
    returning the model's final text response.  When ``tools`` are
    supplied the implementation must support the model making one or
    more function/tool calls and feeding the results back to the model
    until it produces a plain-text response.

    """

    @abstractmethod
    def send_message(
        self,
        prompt: str,
        tools: list[ToolDefinition] | None = None,
        context: list[dict[str, Any]] | None = None,
        *,
        tool_dispatcher: ToolDispatcher | None = None,
    ) -> str:
        """
        Send a prompt to the AI model and return its text response.

        Args:
            prompt: The user message or instruction to send to the model.
            tools: Optional list of callable tools the model may invoke.
                   Each :class:`ToolDefinition` describes a function the
                   implementation should dispatch when the model requests it.
            context: Optional prior conversation turns in the format
                     ``[{"role": "user"|"model", "content": "..."}]``.
            tool_dispatcher: Callable ``(tool_name, args) -> ToolResult`` used
                             to execute tool calls on behalf of the model.

        Returns:
            The model's final plain-text reply after all tool calls have
            been resolved.

        """
