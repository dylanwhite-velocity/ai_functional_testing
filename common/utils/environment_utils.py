"""Utility functions for environment variable handling."""

import os


def get_chaos_owl_active_config() -> str:
    """Get the active Chaos Owl configuration name from environment.

    Returns:
        The active configuration name, defaults to 'default'.
    """
    return os.environ.get("CHAOS_OWL_ACTIVE_CONFIG", "default")


def get_env_var(name: str, default: str | None = None) -> str | None:
    """Get an environment variable value.

    Args:
        name: The name of the environment variable.
        default: Default value if not set.

    Returns:
        The environment variable value or default.
    """
    return os.environ.get(name, default)
