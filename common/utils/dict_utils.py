"""Utility functions for working with dictionaries."""

from typing import Any


def get(data: dict, error_message: str, raise_on_missing: bool, *keys) -> Any:
    """Safely retrieve a nested value from a dictionary.

    Args:
        data: The dictionary to retrieve from.
        error_message: Error message if key is missing.
        raise_on_missing: Whether to raise an exception if key is missing.
        *keys: The sequence of keys to traverse.

    Returns:
        The value at the nested key path, or None if not found and raise_on_missing is False.

    Raises:
        KeyError: If the key is not found and raise_on_missing is True.
    """
    result = data
    for key in keys:
        try:
            if isinstance(result, dict):
                result = result[key]
            elif isinstance(result, list) and isinstance(key, int):
                result = result[key]
            else:
                if raise_on_missing:
                    raise KeyError(error_message)
                return None
        except (KeyError, IndexError, TypeError):
            if raise_on_missing:
                raise KeyError(error_message)
            return None
    return result
