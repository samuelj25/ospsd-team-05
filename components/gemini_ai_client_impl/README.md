# Gemini AI Client Implementation

## Overview

`gemini_ai_client_impl` is the concrete Gemini-backed implementation of the `AIClient` abstract base class from `ai_client_api`. It integrates with Google's Gemini model via the `GEMINI_API_KEY` and powers the natural-language calendar assistant exposed through the `/slack/events` endpoint.

## How It Works

The implementation registers calendar operations (`list_events`, `create_event`, `get_event`, `delete_event`) as Gemini function-call tools defined in `ai_tools.py`. When the model decides to call a tool, the service:

1. Validates the tool arguments using Pydantic schemas (e.g. `_ListEventsArgs`, `_CreateEventArgs`).
2. Dispatches the call to the appropriate `GoogleCalendarClient` method.
3. Serialises the result (or a structured error) back to the model as a `ToolResult`.
4. Returns the model's final text response to the caller.

Per-user conversation history is stored in-process (see the state management note in `DESIGN.md` for the production limitations of this approach).

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio API key. Required at runtime. |

## Installation

This package is part of the `uv` workspace and is installed automatically:

```bash
uv sync --all-packages
```

## Usage

The Gemini client is instantiated internally by the calendar service and is not intended for direct use by consumers. It is wired in through `dependencies.py` and invoked by `slack_routes.py` when a Slack message arrives at `/slack/events`.

## Testing

AI tool dispatch is tested via VCR cassettes in `tests/integration/test_ai_tool_dispatch.py`. To re-record cassettes with fresh credentials:

```bash
uv run pytest tests/integration/test_ai_tool_dispatch.py --record-mode=new_episodes
```

Unit tests for the component:

```bash
uv run pytest components/gemini_ai_client_impl/tests/ -q
```