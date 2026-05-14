# AI Client API

## Overview

`ai_client_api` defines the abstract interface for AI assistant clients used by the calendar service. It contains the `AIClient` abstract base class, request/response types, and exception definitions — with no concrete logic or provider-specific dependencies.

Any AI backend (Gemini, OpenAI, etc.) that the service integrates with must implement this interface, keeping the service layer decoupled from the specific AI provider.

## Purpose

- Document the operations an AI client must support.
- Provide shared exception types for AI-related failures.
- Enable provider-swappable AI integration through a stable contract.

## Architecture

The package exposes one abstract base class covering the core conversational AI operation. It depends only on Python standard library types and has no runtime dependencies on any AI SDK.

```python
from ai_client_api import AIClient

class MyAIClient(AIClient):
    def chat(self, user_id: str, message: str) -> str:
        ...
```

## API Reference

### AIClient Abstract Base Class

- `chat(user_id: str, message: str) -> str`: Send a message to the AI agent and return its text response. Implementations are responsible for maintaining per-user conversation history.

### Exceptions

- `AIClientError`: Base exception for all AI client errors.
- `AIToolDispatchError`: Raised when a tool call issued by the AI model fails to dispatch or validate.

## Testing

```bash
uv run pytest components/ai_client_api/tests/ -q
```