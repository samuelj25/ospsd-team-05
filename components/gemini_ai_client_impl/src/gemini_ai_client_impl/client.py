"""Google Gemini implementation of AbstractAIClient."""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, Any, TypeAlias, cast

import google.generativeai as genai
from ai_client_api.client import AbstractAIClient

if TYPE_CHECKING:
    from collections.abc import Callable

    from ai_client_api.models import ToolDefinition, ToolResult
    from google.generativeai import ChatSession  # type: ignore[attr-defined]
    from google.generativeai.types import GenerateContentResponse

logger = logging.getLogger(__name__)

_MAX_TOOL_ROUNDS = 10  # Guard against infinite tool-call loops


def _to_gemini_tool(tool_def: ToolDefinition) -> genai.protos.Tool:
    """Convert a :class:`ToolDefinition` to a Gemini ``Tool`` proto."""
    fn = genai.protos.FunctionDeclaration(
        name=tool_def.name,
        description=tool_def.description,
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                k: _schema_prop_to_proto(v)
                for k, v in tool_def.parameters.get("properties", {}).items()
            },
            required=tool_def.parameters.get("required", []),
        ),
    )
    return genai.protos.Tool(function_declarations=[fn])


def _schema_prop_to_proto(prop: dict[str, Any]) -> genai.protos.Schema:
    """Convert a single JSON Schema property dict to a Gemini Schema proto."""
    type_map: dict[str, Any] = {
        "string": genai.protos.Type.STRING,
        "number": genai.protos.Type.NUMBER,
        "integer": genai.protos.Type.INTEGER,
        "boolean": genai.protos.Type.BOOLEAN,
    }
    gemini_type = type_map.get(prop.get("type", "string"), genai.protos.Type.STRING)
    return genai.protos.Schema(type=gemini_type, description=prop.get("description", ""))


class GeminiAIClient(AbstractAIClient):
    """
    Gemini chat-completion client with tool-calling support.

    Reads ``GEMINI_API_KEY`` from the environment on construction.

    Args:
        model_name: Gemini model identifier (default ``gemini-2.5-flash``).
        api_key: Optional explicit API key; falls back to ``GEMINI_API_KEY`` env var.

    """

    def __init__(
        self,
        model_name: str = "gemma-4-31b-it",
        api_key: str | None = None,
    ) -> None:
        """
        Initialize the GeminiAIClient.

        Args:
            model_name: Gemini model identifier (default ``gemini-.5-flash``).
            api_key: Optional explicit API key; falls back to ``GEMINI_API_KEY`` env var.

        """
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not resolved_key:
            msg = "GEMINI_API_KEY is not set in the environment."
            raise RuntimeError(msg)
        genai.configure(api_key=resolved_key) # type: ignore[attr-defined]
        self._model_name = model_name

    def _run_tool_loop(
        self,
        chat: ChatSession,
        response: GenerateContentResponse,
        tool_dispatcher: ToolDispatcher | None,
    ) -> GenerateContentResponse:
        """
        Run the Gemini tool-call round-trip loop.

        Repeatedly checks the response for function-call parts, dispatches
        them via ``tool_dispatcher``, and feeds results back to the model.
        Stops when Gemini returns a plain-text response or ``_MAX_TOOL_ROUNDS``
        is reached.

        Args:
            chat: Active ``ChatSession`` instance.
            response: The initial model response to inspect.
            tool_dispatcher: Optional callable ``(name, args) -> ToolResult``
                            used to execute tool calls.

        Returns:
            The final model response after all tool rounds are complete.

        """
        for _ in range(_MAX_TOOL_ROUNDS):
            fn_calls = [
                part.function_call
                for candidate in response.candidates
                for part in candidate.content.parts
                if part.function_call.name  # non-empty name means it's a real call
                and not getattr(part, "thought", False)
            ]

            if not fn_calls:
                break  # Plain-text response — we're done

            if tool_dispatcher is None:
                logger.warning("Gemini requested tool calls but no dispatcher supplied.")
                break

            tool_response_parts = []
            for fn_call in fn_calls:
                args: dict[str, Any] = dict(fn_call.args)
                result: ToolResult = tool_dispatcher(fn_call.name, args)
                logger.debug("Tool %s -> %s", fn_call.name, result.content)
                tool_response_parts.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fn_call.name,
                            response={"result": result.content},
                        )
                    )
                )

            response = chat.send_message(tool_response_parts)

        return response


    def send_message(
        self,
        prompt: str,
        tools: list[ToolDefinition] | None = None,
        context: list[dict[str, Any]] | None = None,
        *,
        tool_dispatcher: ToolDispatcher | None = None,
    ) -> str:
        """
        Send *prompt* to Gemini and return the final text response.

        If *tools* are provided the model may emit function-call requests.
        When a ``tool_dispatcher`` callable is also supplied each function
        call is dispatched automatically and the result fed back to the
        model.  The loop continues until Gemini returns a plain-text part
        or ``_MAX_TOOL_ROUNDS`` is reached.

        Args:
            prompt: User message.
            tools: Optional tool definitions the model may call.
            context: Prior conversation turns (ignored in this implementation
                    — Gemini multi-turn is handled via ``ChatSession``).
            tool_dispatcher: Optional callable ``(name, args) -> ToolResult``
                            used to execute tool calls.

        Returns:
            The model's final plain-text reply.

        """
        gemini_tools = [_to_gemini_tool(t) for t in tools] if tools else None
        model = genai.GenerativeModel(  # type: ignore[attr-defined]
            model_name=self._model_name,
            tools=gemini_tools,
        )

        gemini_history: list[Any] = []
        if context:
            gemini_history.extend({"role": msg["role"], "parts": [msg["content"]]} for msg in context)  # noqa: E501

        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(prompt)
        response = self._run_tool_loop(chat, response, tool_dispatcher)

        # Pass 1: prefer non-thought parts (avoids leaking chain-of-thought)
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.text and not getattr(part, "thought", False):
                    return cast("str", part.text).strip()

        # Pass 2: fallback — accept any text part (non-thinking models don't set 'thought')
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.text:
                    return cast("str", part.text).strip()

        return json.dumps({"raw": str(response)})


# Type alias used in the send_message signature above
ToolDispatcher: TypeAlias = "Callable[[str, dict[str, Any]], ToolResult]"
