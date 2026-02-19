#!/usr/bin/env python3
"""OpenAI configuration management for soak monitoring report generation.

Loads API key from AWS Secrets Manager and provides configurable
model settings via environments.yaml.

Supports both Azure OpenAI and standard OpenAI endpoints.

Configuration is read from the `openai` section of environments.yaml:

    openai:
      provider: azure                    # azure or openai
      secret_name: RASP/openai/dylan
      secret_key_field: AZUREOPENAI_API_KEY
      model: gpt-5
      temperature: 0.3
      max_tokens: 4096
      # Azure-specific settings:
      azure_endpoint: https://ist-apim-aoai.azure-api.net/load-balancing/gpt-5
      azure_api_version: "2024-10-21"
      azure_deployment: gpt-5
"""

import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional

import yaml

# Add parent paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Defaults
DEFAULT_PROVIDER = "azure"
DEFAULT_MODEL = "gpt-5"
DEFAULT_TEMPERATURE = None
DEFAULT_MAX_TOKENS = 16384
DEFAULT_SECRET_NAME = "RASP/openai/dylan"
DEFAULT_SECRET_KEY_FIELD = "AZUREOPENAI_API_KEY"
DEFAULT_AZURE_ENDPOINT = "https://ist-apim-aoai.azure-api.net/load-balancing/gpt-5"
DEFAULT_AZURE_API_VERSION = "2024-10-21"
DEFAULT_AZURE_DEPLOYMENT = "gpt-5"


@dataclass
class OpenAIConfig:
    """OpenAI / Azure OpenAI API configuration."""

    api_key: str
    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL
    temperature: Optional[float] = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    # Azure-specific
    azure_endpoint: Optional[str] = DEFAULT_AZURE_ENDPOINT
    azure_api_version: Optional[str] = DEFAULT_AZURE_API_VERSION
    azure_deployment: Optional[str] = DEFAULT_AZURE_DEPLOYMENT

    @property
    def is_azure(self) -> bool:
        """Check if using Azure OpenAI."""
        return self.provider.lower() == "azure"

    def to_dict(self) -> Dict[str, Any]:
        """Return config as dict (without api_key for logging)."""
        d = {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.is_azure:
            d["azure_endpoint"] = self.azure_endpoint
            d["azure_api_version"] = self.azure_api_version
            d["azure_deployment"] = self.azure_deployment
        return d


def get_openai_api_key(secret_name: str = DEFAULT_SECRET_NAME,
                       secret_key_field: str = DEFAULT_SECRET_KEY_FIELD) -> str:
    """Retrieve API key from AWS Secrets Manager.

    Supports two formats:
      - Plain string: The secret value IS the API key
      - JSON object: Extracts value from the specified field name

    Falls back to OPENAI_API_KEY or AZUREOPENAI_API_KEY environment variables.

    Args:
        secret_name: AWS Secrets Manager secret name.
        secret_key_field: JSON field name containing the key.

    Returns:
        The API key string.
    """
    # Check environment variables first (useful for local dev / CI override)
    for env_var in ("AZUREOPENAI_API_KEY", "OPENAI_API_KEY"):
        env_key = os.environ.get(env_var)
        if env_key:
            print(f"  Using API key from environment variable: {env_var}")
            return env_key

    try:
        from common.utils.aws_utils import get_secret

        print(f"  Retrieving API key from AWS Secrets Manager: {secret_name}")
        secret_value = get_secret(secret_name)

        # Try parsing as JSON first
        try:
            secret_json = json.loads(secret_value)
            # Look for the configured field name first, then common alternatives
            search_fields = [secret_key_field]
            for alt in ("AZUREOPENAI_API_KEY", "OPENAI_API_KEY", "api_key", "key", "openai_api_key"):
                if alt not in search_fields:
                    search_fields.append(alt)

            for key_field in search_fields:
                if key_field in secret_json:
                    print(f"  Found key in field: {key_field}")
                    return secret_json[key_field]
            # If JSON but no recognized field, raise
            raise ValueError(
                f"Secret is JSON but contains no recognized API key field. "
                f"Looked for: {search_fields}. Found keys: {list(secret_json.keys())}"
            )
        except json.JSONDecodeError:
            # Plain string — the secret value IS the key
            return secret_value.strip()

    except ImportError:
        print("  WARNING: common.utils.aws_utils not available")
        raise RuntimeError(
            "Cannot retrieve API key: aws_utils not available and "
            "no API key environment variable set"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve API key from '{secret_name}': {e}") from e


def load_openai_config(config_path: Optional[str] = None) -> OpenAIConfig:
    """Load OpenAI configuration from environments.yaml and AWS Secrets Manager.

    Args:
        config_path: Path to environments.yaml. If None, uses default location.

    Returns:
        Populated OpenAIConfig instance.
    """
    # Load settings from config file
    openai_settings: Dict[str, Any] = {}

    if config_path:
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}
            openai_settings = config.get("openai", {})
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"  Warning: Could not load openai config from {config_path}: {e}")
            print(f"  Using defaults")

    # Extract settings with defaults
    provider = openai_settings.get("provider", DEFAULT_PROVIDER)
    secret_name = openai_settings.get("secret_name", DEFAULT_SECRET_NAME)
    secret_key_field = openai_settings.get("secret_key_field", DEFAULT_SECRET_KEY_FIELD)
    model = openai_settings.get("model", DEFAULT_MODEL)
    temperature = openai_settings.get("temperature", DEFAULT_TEMPERATURE)
    max_tokens = openai_settings.get("max_tokens", DEFAULT_MAX_TOKENS)

    # Azure-specific settings
    azure_endpoint = openai_settings.get("azure_endpoint", DEFAULT_AZURE_ENDPOINT)
    azure_api_version = openai_settings.get("azure_api_version", DEFAULT_AZURE_API_VERSION)
    azure_deployment = openai_settings.get("azure_deployment", DEFAULT_AZURE_DEPLOYMENT)

    # Retrieve API key
    api_key = get_openai_api_key(secret_name, secret_key_field)

    return OpenAIConfig(
        api_key=api_key,
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        azure_endpoint=azure_endpoint,
        azure_api_version=azure_api_version,
        azure_deployment=azure_deployment,
    )
