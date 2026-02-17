"""This module provides a manager for retrieving and validating SUT configurations.

It uses AWS Secrets Manager to fetch the configuration data and validates it against a predefined model.
"""

from typing import ClassVar

from common.sut_config.models.auth_model import AuthModel
from common.sut_config.models.sut_config_model import SUTConfigModel
from common.sut_config.models.tenant_model import TenantModel
from common.utils import aws_utils, config_utils


class SUTConfigManager:
    """Manager for retrieving and validating SUT configurations."""

    ACTIVE_CONFIG_MARKER_FILENAME = "sutconfigactive"

    _config_cache: ClassVar[dict[str, SUTConfigModel]] = {}

    def __init__(self):
        """Initialize the SUTConfigManager."""

    def get_config_from_remote(self, environment_name: str) -> SUTConfigModel:
        """Retrieve the SUT configuration for the specified environment."""
        try:
            json = aws_utils.get_secret(f"RASP/SUTConfig/{environment_name}")
        except aws_utils.AWSSUTConfigError as ex:
            raise ValueError("Error retrieving SUT configuration from AWS Secret Manager") from ex

        if not json:
            raise ValueError(f"No SUT configuration found for environment: {environment_name}")
        return SUTConfigModel.model_validate_json(json)

    def list_available_configs(self) -> list[str]:
        """List all available SUT configurations in AWS Secrets Manager."""
        try:
            secrets = aws_utils.list_secrets_with_prefix("RASP/SUTConfig/")
            return [s.replace("RASP/SUTConfig/", "") for s in secrets]
        except aws_utils.AWSSUTConfigError as ex:
            raise ValueError("Error listing SUT configurations from AWS Secret Manager") from ex

    def set_active_context(self, environment_name: str, org_id: str | None = None, username: str | None = None):
        """Set the active SUT configuration in the current context."""
        try:
            sut_config = self.get_config_from_remote(environment_name)

            if org_id:
                selected_org_id = org_id
            elif username:
                tenant = sut_config.get_tenant_with_username(username)
                selected_org_id = tenant.orgId if tenant else None
            else:
                selected_org_id = sut_config.get_default_tenant().orgId

            if username:
                selected_username = username
            elif org_id:
                tenant = sut_config.get_tenant_with_orgid(org_id)
                selected_username = tenant.get_default_auth().username if tenant else None
            else:
                selected_username = sut_config.get_default_tenant().get_default_auth().username

            # Clear cache for this environment if it exists
            if environment_name in SUTConfigManager._config_cache:
                del SUTConfigManager._config_cache[environment_name]

            SUTConfigManager._config_cache[environment_name] = sut_config

            config_utils.save_config_file(
                "rasp",
                self.ACTIVE_CONFIG_MARKER_FILENAME,
                {
                    "environmentName": sut_config.name,
                    "tenant": selected_org_id,
                    "username": selected_username,
                },
            )
        except Exception as e:
            raise ValueError(f"Error setting active SUT configuration: {e}") from e

    def get_config(self) -> SUTConfigModel:
        """Get the currently active SUT configuration."""
        active_config_marker = self.__get_active_config_marker()
        environment_name = active_config_marker.get("environmentName")

        if not environment_name:
            raise ValueError("No active SUT configuration found. Please set an active configuration first.")

        if environment_name in SUTConfigManager._config_cache:
            return SUTConfigManager._config_cache[environment_name]

        config = self.get_config_from_remote(environment_name)
        SUTConfigManager._config_cache[environment_name] = config
        return config

    def get_tenant(self) -> TenantModel:
        """Get the tenant from the currently active SUT configuration."""
        active_config_marker = self.__get_active_config_marker()

        sut_config = self.get_config()
        return sut_config.get_tenant_with_username(active_config_marker["username"]) or sut_config.get_default_tenant()

    def get_auth(self) -> AuthModel:
        """Get the authentication details from the currently active SUT configuration."""
        active_config_marker = self.__get_active_config_marker()
        if not active_config_marker:
            raise ValueError("No active SUT configuration found.")

        sut_config = self.get_config()
        tenant = sut_config.get_tenant_with_username(active_config_marker["username"]) or sut_config.get_default_tenant()
        return tenant.get_auth_with_username(active_config_marker["username"]) or tenant.get_default_auth()

    def get_api_url(self) -> str:
        """Get the API URL from the currently active SUT configuration and append the organization ID if present."""
        active_config_marker = self.__get_active_config_marker()
        sut_config = self.get_config()
        tenant = sut_config.get_tenant_with_username(active_config_marker["username"]) or sut_config.get_default_tenant()

        api_url = sut_config.apiUrl
        if tenant.orgId:
            api_url += f"/{tenant.orgId}"

        return api_url

    def __get_active_config_marker(self) -> dict:
        """Get the active configuration marker from the config file."""
        active_config_marker = config_utils.get_config_file("rasp", self.ACTIVE_CONFIG_MARKER_FILENAME)
        if not active_config_marker:
            raise ValueError("No active SUT configuration found.")
        return active_config_marker

    def format_receiver_url(self, base_url: str) -> str:
        """Format the base URL into the format needed for a Receiver Feed / Input based on the SUT configuration."""
        sut_config = self.get_config()
        match sut_config.distribution:
            case "GeoEvent":
                receiver_port = 6143
                return f"{base_url}:{receiver_port!s}/geoevent/rest/receiver"
            case "VelocityEnterprise":
                default_port = 6443
                receving_port = 9001
                return f"{base_url.replace(str(default_port), str(receving_port))}/receiver"
            case "VelocitySaaS":
                return f"{base_url}/receiver"
            case _:
                raise ValueError(f"Unsupported SUT distribution: {sut_config.distribution}")
