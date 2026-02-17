"""Custom exceptions for configuration-related errors."""


class ConfigError(Exception):
    """An error occurred while working with configuration."""

    pass


class ConfigFileMissingError(Exception):
    """The configuration file is missing or could not be decoded."""

    pass
