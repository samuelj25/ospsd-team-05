"""Exceptions for the AI client API."""


class AIResponseError(Exception):
    """
    Raised when the AI model returns a response with no extractable text.

    This indicates the model completed a request but produced output that
    contains no plain-text parts (e.g. only thought parts, or an empty
    candidate list).  Callers should catch this and decide how to surface
    the failure — for example by posting an apology message or retrying.
    """
