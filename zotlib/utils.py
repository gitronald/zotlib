"""Internal utility functions."""

from typing import Iterable, Any


def unlist(nested: Iterable[Iterable[Any]]) -> list[Any]:
    """Flatten a nested iterable into a single list."""
    return [item for sublist in nested for item in sublist]


def print_line(char: str = "-", length: int = 80) -> None:
    """Print a horizontal line separator."""
    print(char * length)
