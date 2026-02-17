"""This module contains helpful utility functions for working with the various config files Axl utilizes."""

import json
import os
from enum import Enum
from pathlib import Path

import typer
from loguru import logger

from common.exceptions.config_exceptions import ConfigError, ConfigFileMissingError
from common.utils import dict_utils, environment_utils


def get_item_config_files(config_directory: Path) -> list[dict]:
    """Returns a list of item configs as defined in the items-configs directory JSON files.

    Args:
      config_directory (Path): The path to the items-configs directory.

    Returns:
      List[Dict]: A list of item configurations.

    Raises:
      FileNotFoundError: If the file is not found.
      JSONDecodeError: If the config file is not a valid JSON.
    """
    item_configs = []

    for entry in os.scandir(str(config_directory)):
        if entry.path.endswith(".json") and entry.is_file() and entry.name is not None and "skip" not in entry.name:
            file_path = os.path.join(config_directory, entry.name)
            with open(file_path, encoding="utf-8") as config_file:
                item_config = json.load(config_file)
                logger.info(f"Loaded item config file {file_path}")
                item_configs.append(item_config)

    return item_configs


def get_test_profile_file(filepath) -> dict:
    """Get the test profile file from the specified filepath.

    Args:
      filepath (str): The path to the test profile file.

    Returns:
      dict: The loaded test profile configuration.

    Raises:
      FileNotFoundError: If the file is not found.
      JSONDecodeError: If the file is not a valid JSON.
    """
    with open(filepath, encoding="utf-8") as test_profile_raw:
        test_profile_json = json.load(test_profile_raw)
        logger.opt(colors=True).info(f"Loading Test Profile >>> <magenta>{os.path.basename(filepath)}</magenta> <<<")
    return test_profile_json


def parse_output_label(item_config: dict, username: str, is_developer_environment: bool, output_index: int):
    """Parse the output label based on the item configuration and output index.

    Args:
      item_config (dict): The item configuration.
      username (str): The username to prefix the label with.
      is_developer_environment (bool): Whether the environment is a developer environment.
      output_index (int): The index of the output.

    Returns:
      str: The parsed output label.
    """
    output = dict_utils.get(
        item_config,
        "Invalid item config - does not contain 'outputs' property.",
        True,
        "outputs",
        output_index,
    )
    label_value = dict_utils.get(output, "Invalid item config - does not contain 'label' property", True, "label")
    return prefix_label_with_username(output, username, "label") if is_developer_environment else label_value


def prefix_label_with_username(data: dict, username: str, label_property_name: str) -> str:
    """Prefix the item label with the username.

    Args:
      data (dict): The item configuration.
      username (str): The username to prefix the label with.
      label_property_name (str): The name of the label property.

    Returns:
      str: The prefixed label.
    """
    label_value = dict_utils.get(
        data,
        f"Invalid config - does not contain '{label_property_name}' property",
        True,
        label_property_name,
    )
    return f"{username}{label_value}"


def save_config_file(app_name: str, config_name: str = "default", config: dict | None = None) -> None:
    """Save the provided configuration to the config file.

    Args:
      app_name (str): The name of the application.
      config_name (str): The name of the configuration file.
      config (dict): The configuration to save.
    """
    if config is None:
        config = {}
    config_path: Path = app_config_path(app_name, config_name)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f)

    logger.debug(f"Saved config file to {config_path}")


def app_config_path(app_name: str, config_name: str = "default") -> Path:
    """Get the path to the configuration file.

    Args:
      app_name (str): The name of the application.
      config_name (str): The name of the configuration file.

    Returns:
      Path: The path to the configuration file.
    """
    if config_name == "":
        return Path("")
    app_dir = typer.get_app_dir(app_name, force_posix=True)

    config_path: Path = Path(app_dir) / "config" / f"{config_name}.json"
    return config_path


def get_config_files(app_name: str) -> list[str]:
    """Get the list of configuration files.

    Args:
      app_name (str): The name of the application.

    Returns:
      list: The list of configuration files.
    """
    app_dir = typer.get_app_dir(app_name, force_posix=True)
    app_dir_path = Path(app_dir) / "config"
    app_dir_path.mkdir(parents=True, exist_ok=True)

    config_files = [entry.name[:-5] for entry in os.scandir(app_dir_path) if entry.path.endswith(".json") and entry.is_file()]

    return config_files


def get_active_config_file() -> dict:
    """Get the active configuration file.

    Returns:
      dict: The configuration file.
    """
    current_config = environment_utils.get_chaos_owl_active_config()
    config_path: Path = app_config_path(current_config)
    with open(config_path) as file:
        try:
            return json.load(file)
        except json.JSONDecodeError as e:
            raise ConfigFileMissingError(f"Unable to fine or decode config file: {e}") from None


def get_config_file(app_name: str, config_name: str = "default") -> dict | None:
    """Get the configuration file.

    Args:
      app_name (str): The name of the application.
      config_name (str): The name of the configuration file.

    Returns:
      dict: The configuration file.
    """
    try:
        config_path: Path = app_config_path(app_name, config_name)
        with open(config_path) as file:
            try:
                return json.load(file)
            except json.JSONDecodeError as e:
                raise ConfigFileMissingError(f"Unable to find or decode config file: {e}") from None
    except FileNotFoundError:
        return None


def get_config_file_value(app_name: str, config_name: str = "default", key: str = "") -> str:
    """Get the value of the specified key from the configuration file.

    Args:
      app_name (str): The name of the application.
      config_name (str): The name of the configuration file.
      key (str): The key to get the value for.

    Returns:
      str: The value of the key from the configuration file.
    """
    config = get_config_file(app_name, config_name)
    if key in config:
        return config[key]
    else:
        raise ConfigError(f"{key} key is missing in the config")


class ConfigKeys(str, Enum):  # pragma: no cover
    """Configuration keys."""

    username = "username"
    velocity_base_url = "velocity_base_url"
    geoevent_base_url = "geoevent_base_url"
    geoevent_username = "geoevent_username"
    geoevent_password = "geoevent_password"
    geoevent_environment_name = "geoevent_environment_name"
    agol_portal_url = "agol_portal_url"
    agol_portal_username = "agol_portal_username"
    agol_portal_password = "agol_portal_password"
    azure_devops_organization_url = "azure_devops_organization_url"
    azure_devops_pat = "azure_devops_pat"
    environment_type = "environment_type"
    velocity_environment_name = "velocity_environment_name"
    tenants = "tenants"
    org_id = "org_id"
    is_developer_environment = "is_developer_environment"
    disable_metric_upload = "disable_metric_upload"
    disable_remote_secret_patching = "disable_remote_secret_patching"
    azure_event_hub_connection_string = "azure_event_hub_connection_string"
    azure_service_bus_connection_string = "azure_service_bus_connection_string"
    timestream_table = "timestream_table"
