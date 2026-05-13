"""Google Gemini implementation of AbstractAIClient."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import TYPE_CHECKING, Any, TypeAlias, cast

from ai_client_api.client import AbstractAIClient
from ai_client_api.exceptions import AIResponseError
from google import genai
from google.api_core.exceptions import InternalServerError
from google.genai import types

if TYPE_CHECKING:
    from collections.abc import Callable

    from ai_client_api.models import ToolDefinition, ToolResult
    from google.genai.chats import Chat
    from google.genai.types import GenerateContentResponse

logger = logging.getLogger(__name__)

_MAX_TOOL_ROUNDS = 10  # Guard against infinite tool-call loops
_RETRY_ATTEMPTS = 3
_SYSTEM_INSTRUCTION = (
    "You are a concise Google Calendar assistant integrated into Slack. "
    "Rules you must always follow:\n"
    "- Respond ONLY with your final user-facing answer. Never output reasoning, "
    "thinking steps, internal monologue, tool introspection, or tool lists.\n"
    "- Be extremely concise. One or two sentences maximum.\n"
    "- Never repeat yourself.\n"
    "- Never lie or invent calendar data. If a tool call fails, say so plainly.\n"
    "- The current date/time will be provided in each user message."
)
_THINKING_SUPPORTED_MODELS = (
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-pro",
    "gemini-3.1-pro-preview"
)
_THINK_TAG_RE = re.compile(r"<\|channel\|>thought.*?<channel\|>|<think>.*?</think>", re.DOTALL)

def _supports_thinking(model_name: str) -> bool:
    """Return True only for Gemini models that accept ThinkingConfig."""
    return any(model_name.startswith(prefix) for prefix in _THINKING_SUPPORTED_MODELS)

def _strip_thought_tags(text: str) -> str:
    """Strip Gemma-style inline thought blocks from response text."""
    return _THINK_TAG_RE.sub("", text).strip()

def _to_gemini_tool(tool_def: ToolDefinition) -> types.Tool:
    """Convert a ToolDefinition to a types.Tool."""
    return types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name=tool_def.name,
                description=tool_def.description,
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        k: _schema_prop_to_schema(v)
                        for k, v in tool_def.parameters.get("properties", {}).items()
                    },
                    required=tool_def.parameters.get("required", []),
                ),
            )
        ]
    )


def _schema_prop_to_schema(prop: dict[str, Any]) -> types.Schema:
    """Convert a single JSON Schema property dict to a types.Schema."""
    type_map: dict[str, types.Type] = {
        "string":  types.Type.STRING,
        "number":  types.Type.NUMBER,
        "integer": types.Type.INTEGER,
        "boolean": types.Type.BOOLEAN,
    }
    gemini_type = type_map.get(prop.get("type", "string"), types.Type.STRING)
    return types.Schema(type=gemini_type, description=prop.get("description", ""))

def _tool_result_to_part(fn_name: str, result: ToolResult) -> types.Part:
    """
    Convert a ToolResult into a new-SDK FunctionResponse Part.

    FunctionResponse.response must always be a dict. ToolResult.content is
    a JSON string, so we parse it back out before passing it to the type.
    """
    try:
        parsed = json.loads(result.content)
    except (json.JSONDecodeError, TypeError):
        parsed = result.content

    if not isinstance(parsed, dict):
        parsed = {"result": parsed}

    return types.Part.from_function_response(name=fn_name, response=parsed)

def _is_thought_part(part: types.Part) -> bool:
    """Return True if this part is a model thought/reasoning trace."""
    thought_attr = getattr(part, "thought", None)
    return thought_attr is True or (isinstance(thought_attr, bool) and thought_attr)

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
        model_name: str = "gemini-2.5-flash",
        api_key: str | None = None,
    ) -> None:
        """
        Initialize the GeminiAIClient.

        Args:
            model_name: Gemini model identifier (default ``gemini-2.5-flash``).
            api_key: Optional explicit API key; falls back to ``GEMINI_API_KEY`` env var.

        """
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not resolved_key:
            msg = "GEMINI_API_KEY is not set in the environment."
            raise ValueError(msg)
        self._client = genai.Client(api_key=resolved_key)
        self._model_name = model_name

    def _run_tool_loop(
        self,
        chat: Chat,
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
                for candidate in response.candidates or []
                for part in (candidate.content.parts if candidate.content else []) or []
                if part.function_call and part.function_call.name
                and not _is_thought_part(part)
            ]

            if not fn_calls:
                break  # Plain-text response — we're done

            if tool_dispatcher is None:
                logger.warning("Gemini requested tool calls but no dispatcher supplied.")
                break

            tool_response_parts = []
            for fn_call in fn_calls:
                args: dict[str, Any] = dict(cast("Any", fn_call.args) or {})
                name = cast("str", fn_call.name)
                result: ToolResult = tool_dispatcher(name, args)
                logger.debug("Tool %s -> %s", name, result.content)
                tool_response_parts.append(
                    _tool_result_to_part(name, result)
                )

            for attempt in range(_RETRY_ATTEMPTS):
                try:
                    response = chat.send_message(tool_response_parts)
                    break
                except InternalServerError:
                    if attempt == _RETRY_ATTEMPTS - 1:
                        raise
                    wait = 2 ** attempt  # 1s, 2s
                    logger.warning(
                        "Gemini 500 on tool response (attempt %d/%d), retrying in %ds...",
                        attempt + 1,
                        _RETRY_ATTEMPTS,
                        wait,
                    )
                    time.sleep(wait)

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
            context: Prior conversation turns in the format
                    ``[{"role": "user"|"model", "content": "..."}]``.
                    Each turn is converted to a Gemini history entry and
                    passed to ``start_chat`` so the model has full context.
            tool_dispatcher: Optional callable ``(name, args) -> ToolResult``
                            used to execute tool calls.

        Returns:
            The model's final plain-text reply.

        """
        gemini_tools = cast("Any", [_to_gemini_tool(t) for t in tools] if tools else None)
        config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION,
            tools=gemini_tools,
            thinking_config=types.ThinkingConfig(thinking_budget=0) if _supports_thinking(self._model_name) else None,  # noqa: E501
        )

        history: list[types.Content] = []
        if context:
            history.extend(
                types.Content(
                    role=msg["role"],
                    parts=[types.Part.from_text(text=msg["content"])],
                )
                for msg in context
            )

        chat = self._client.chats.create(
            model=self._model_name,
            config=config,
            history=cast("Any", history),
        )
        response = chat.send_message(prompt)
        response = self._run_tool_loop(chat, response, tool_dispatcher)

        # Pass 1: prefer non-thought parts
        for candidate in response.candidates or []:
            text_parts = [
                _strip_thought_tags(part.text)
                for part in (candidate.content.parts if candidate.content else []) or []
                if part.text and not _is_thought_part(part)
            ]
            # Filter out parts that were purely thought tags and are now empty
            text_parts = [t for t in text_parts if t]
            if text_parts:
                return " ".join(text_parts)

        # Pass 2: fallback
        for candidate in response.candidates or []:
            for part in (candidate.content.parts if candidate.content else []) or []:
                if part.text:
                    cleaned = _strip_thought_tags(part.text)
                    if cleaned:
                        return cleaned

        logger.error(
            "Gemini returned a response with no extractable text: %s", response
        )
        msg = (
            "Gemini response contained no plain-text parts. "
            "The model may have returned only thought parts or an empty candidate list."
        )
        raise AIResponseError(msg)


# Type alias used in the send_message signature above
ToolDispatcher: TypeAlias = "Callable[[str, dict[str, Any]], ToolResult]"
