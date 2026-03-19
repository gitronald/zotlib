"""Internal utility functions."""

from typing import Iterable, Any


def unlist(nested: Iterable[Iterable[Any]]) -> list[Any]:
    """Flatten a nested iterable into a single list."""
    return [item for sublist in nested for item in sublist]

