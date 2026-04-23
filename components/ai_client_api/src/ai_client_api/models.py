"""Models for the AI client API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolDefinition:
    """
    Describes a callable tool the AI model may invoke.

    Attributes:
        name: Unique tool name (snake_case, matches the function the AI will call).
        description: Human-readable description so the model knows when to call it.
        parameters: JSON Schema object describing the tool's input parameters.

    """

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """
    The result of executing a tool call.

    Attributes:
        tool_name: Name of the tool that was called.
        content: Serialised string representation of the return value.
        is_error: Set to ``True`` when tool execution raised an exception.

    """

    tool_name: str
    content: str
    is_error: bool = False
